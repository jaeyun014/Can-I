from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

from app.core.config import settings
from app.models.schemas import (
    AnalyzeResponse,
    FeedbackCreate,
    FeedbackRecord,
    ReviewQueueItem,
    UsageLog,
    UsageLogCreate,
)


def _database_path() -> Path:
    url = settings.database_url
    if url.startswith("sqlite:///"):
        return Path(url.removeprefix("sqlite:///"))
    return Path("can_i.db")


DB_PATH = _database_path()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT,
                input_type TEXT NOT NULL DEFAULT 'unknown',
                input_text TEXT NOT NULL DEFAULT '',
                target_type TEXT NOT NULL DEFAULT 'UNKNOWN',
                item_name TEXT NOT NULL,
                detected_material TEXT NOT NULL,
                region TEXT NOT NULL,
                overall_risk TEXT NOT NULL,
                decisions_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            )
            """
        )
        _ensure_column(connection, "usage_logs", "target_type", "TEXT NOT NULL DEFAULT 'UNKNOWN'")
        _ensure_column(connection, "usage_logs", "decisions_json", "TEXT NOT NULL DEFAULT '{}'")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usage_log_id INTEGER NOT NULL,
                object_name TEXT NOT NULL,
                object_type TEXT NOT NULL DEFAULT '',
                material TEXT NOT NULL,
                normalized_json TEXT NOT NULL DEFAULT '{}',
                result_json TEXT NOT NULL,
                versions_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY (usage_log_id) REFERENCES usage_logs(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS confidence_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usage_log_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                level TEXT NOT NULL,
                method TEXT NOT NULL DEFAULT 'rule_based_v2',
                positive_factors_json TEXT NOT NULL DEFAULT '[]',
                negative_factors_json TEXT NOT NULL DEFAULT '[]',
                explanation TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (usage_log_id) REFERENCES usage_logs(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS evidence_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usage_log_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                value TEXT NOT NULL,
                source TEXT NOT NULL,
                raw_confidence REAL NOT NULL,
                source_reliability REAL NOT NULL,
                evidence_text TEXT NOT NULL DEFAULT '',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY (usage_log_id) REFERENCES usage_logs(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conflict_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usage_log_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                source_a TEXT NOT NULL,
                value_a TEXT NOT NULL,
                source_b TEXT NOT NULL,
                value_b TEXT NOT NULL,
                resolution TEXT NOT NULL,
                confidence_penalty REAL NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (usage_log_id) REFERENCES usage_logs(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usage_log_id INTEGER,
                user_email TEXT,
                feedback_type TEXT NOT NULL,
                original_prediction_json TEXT NOT NULL DEFAULT '{}',
                user_correction_json TEXT NOT NULL DEFAULT '{}',
                comment TEXT NOT NULL DEFAULT '',
                review_status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS product_barcodes (
                barcode TEXT PRIMARY KEY,
                product_name TEXT NOT NULL,
                manufacturer TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'internal_product_db',
                verified INTEGER NOT NULL DEFAULT 0,
                data_confidence REAL NOT NULL DEFAULT 0.7,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS product_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT NOT NULL,
                part_name TEXT NOT NULL,
                material TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (barcode) REFERENCES product_barcodes(barcode) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS product_usage_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                conditions_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                FOREIGN KEY (barcode) REFERENCES product_barcodes(barcode) ON DELETE CASCADE
            )
            """
        )
        _seed_product_database(connection)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS review_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usage_log_id INTEGER NOT NULL,
                review_score REAL NOT NULL,
                reasons_json TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'pending',
                assigned_to TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (usage_log_id) REFERENCES usage_logs(id) ON DELETE CASCADE
            )
            """
        )


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def create_usage_log(
    payload: UsageLogCreate,
    user_email: Optional[str] = None,
    input_type: str = "unknown",
    input_text: str = "",
    result: AnalyzeResponse | None = None,
    normalized: dict[str, Any] | None = None,
    evidence_records: list[Any] | None = None,
    conflicts: list[Any] | None = None,
) -> UsageLog:
    created_at = _utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO usage_logs (
                user_email, input_type, input_text, target_type, item_name, detected_material,
                region, overall_risk, decisions_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_email,
                input_type,
                input_text,
                payload.targetType,
                payload.itemName,
                payload.detectedMaterial,
                payload.region,
                payload.overallRisk,
                _dumps(payload.decisions),
                created_at.isoformat(),
            ),
        )
        log_id = int(cursor.lastrowid)

        if result:
            result.logId = log_id
            connection.execute(
                """
                INSERT INTO analysis_results (
                    usage_log_id, object_name, object_type, material,
                    normalized_json, result_json, versions_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log_id,
                    result.itemName,
                    result.objectType,
                    result.detectedMaterial,
                    _dumps(normalized or {}),
                    result.model_dump_json(),
                    _dumps(getattr(result, "versions", {})),
                    created_at.isoformat(),
                ),
            )
            connection.execute(
                """
                INSERT INTO confidence_records (
                    usage_log_id, score, level, method, positive_factors_json,
                    negative_factors_json, explanation, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log_id,
                    result.confidence.score,
                    result.confidence.level,
                    "rule_based_v2",
                    _dumps([factor.model_dump() for factor in result.confidence.factors]),
                    _dumps([penalty.model_dump() for penalty in result.confidence.penalties]),
                    result.confidence.summary,
                    created_at.isoformat(),
                ),
            )
            for evidence in evidence_records or []:
                connection.execute(
                    """
                    INSERT INTO evidence_records (
                        usage_log_id, field_name, value, source, raw_confidence,
                        source_reliability, evidence_text, metadata_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        log_id,
                        evidence.field,
                        evidence.value,
                        evidence.source,
                        evidence.rawConfidence,
                        evidence.sourceReliability,
                        evidence.evidenceText,
                        _dumps(evidence.metadata),
                        created_at.isoformat(),
                    ),
                )
            for conflict in conflicts or []:
                connection.execute(
                    """
                    INSERT INTO conflict_records (
                        usage_log_id, field_name, source_a, value_a, source_b, value_b,
                        resolution, confidence_penalty, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        log_id,
                        conflict.field,
                        conflict.sourceA,
                        conflict.valueA,
                        conflict.sourceB,
                        conflict.valueB,
                        conflict.resolution,
                        conflict.confidencePenalty,
                        created_at.isoformat(),
                    ),
                )
            _maybe_enqueue_review(connection, log_id, result, created_at)

    return UsageLog(
        id=log_id,
        createdAt=created_at,
        userEmail=user_email,
        **payload.model_dump(),
    )


def list_usage_logs(user_email: Optional[str] = None, limit: int = 20) -> list[UsageLog]:
    with get_connection() as connection:
        if user_email:
            rows = connection.execute(
                """
                SELECT ul.*, ar.result_json
                FROM usage_logs ul
                LEFT JOIN analysis_results ar ON ar.usage_log_id = ul.id
                WHERE ul.user_email = ?
                ORDER BY datetime(ul.created_at) DESC, ul.id DESC
                LIMIT ?
                """,
                (user_email, limit),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT ul.*, ar.result_json
                FROM usage_logs ul
                LEFT JOIN analysis_results ar ON ar.usage_log_id = ul.id
                WHERE ul.user_email IS NULL
                ORDER BY datetime(ul.created_at) DESC, ul.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    return [_row_to_usage_log(row) for row in rows]


def delete_usage_logs(user_email: str) -> int:
    with get_connection() as connection:
        rows = connection.execute("SELECT id FROM usage_logs WHERE user_email = ?", (user_email,)).fetchall()
        log_ids = [row["id"] for row in rows]
        if not log_ids:
            return 0

        placeholders = ",".join("?" for _ in log_ids)
        connection.execute(f"DELETE FROM evidence_records WHERE usage_log_id IN ({placeholders})", log_ids)
        connection.execute(f"DELETE FROM conflict_records WHERE usage_log_id IN ({placeholders})", log_ids)
        connection.execute(f"DELETE FROM confidence_records WHERE usage_log_id IN ({placeholders})", log_ids)
        connection.execute(f"DELETE FROM analysis_results WHERE usage_log_id IN ({placeholders})", log_ids)
        connection.execute(f"DELETE FROM review_queue WHERE usage_log_id IN ({placeholders})", log_ids)
        connection.execute(f"DELETE FROM usage_logs WHERE id IN ({placeholders})", log_ids)
        return len(log_ids)


def _row_to_usage_log(row: sqlite3.Row) -> UsageLog:
    analysis_result = None
    if "result_json" in row.keys() and row["result_json"]:
        try:
            analysis_result = AnalyzeResponse.model_validate_json(row["result_json"])
        except Exception:
            analysis_result = None
    return UsageLog(
        id=row["id"],
        itemName=row["item_name"],
        detectedMaterial=row["detected_material"],
        region=row["region"],
        overallRisk=row["overall_risk"],
        targetType=row["target_type"] if "target_type" in row.keys() else "UNKNOWN",
        decisions=json.loads(row["decisions_json"] or "{}") if "decisions_json" in row.keys() else {},
        createdAt=datetime.fromisoformat(row["created_at"]),
        userEmail=row["user_email"],
        analysisResult=analysis_result,
    )


def _ensure_column(connection: sqlite3.Connection, table: str, column: str, declaration: str) -> None:
    columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")


def _maybe_enqueue_review(
    connection: sqlite3.Connection,
    log_id: int,
    result: AnalyzeResponse,
    created_at: datetime,
) -> None:
    reasons: list[str] = []
    confidence = result.confidence
    if confidence.score < 65:
        reasons.append("low_confidence")
    if confidence.conflictDetected:
        reasons.append("evidence_conflict")
    if result.detectedMaterial == "unknown":
        reasons.append("unknown_material")
    if result.disposal.category == "확인 필요":
        reasons.append("fallback_rule_used")

    if not reasons:
        return

    review_score = min(1.0, 0.35 + (65 - min(confidence.score, 65)) / 100 + 0.2 * (len(reasons) - 1))
    existing = connection.execute("SELECT id FROM review_queue WHERE usage_log_id = ?", (log_id,)).fetchone()
    if existing:
        connection.execute(
            """
            UPDATE review_queue
            SET review_score = ?, reasons_json = ?, updated_at = ?
            WHERE usage_log_id = ?
            """,
            (review_score, _dumps(reasons), created_at.isoformat(), log_id),
        )
        return
    connection.execute(
        """
        INSERT INTO review_queue (
            usage_log_id, review_score, reasons_json, status, created_at, updated_at
        )
        VALUES (?, ?, ?, 'pending', ?, ?)
        """,
        (log_id, review_score, _dumps(reasons), created_at.isoformat(), created_at.isoformat()),
    )


def lookup_product_by_barcode(barcode: str) -> dict[str, Any] | None:
    if not barcode:
        return None
    with get_connection() as connection:
        product = connection.execute("SELECT * FROM product_barcodes WHERE barcode = ?", (barcode,)).fetchone()
        if not product:
            return None
        materials = connection.execute("SELECT part_name, material FROM product_materials WHERE barcode = ?", (barcode,)).fetchall()
        usage_rules = connection.execute("SELECT category, status, conditions_json FROM product_usage_rules WHERE barcode = ?", (barcode,)).fetchall()
    return {
        "barcode": barcode,
        "productName": product["product_name"],
        "manufacturer": product["manufacturer"],
        "source": product["source"],
        "verified": bool(product["verified"]),
        "dataConfidence": product["data_confidence"],
        "materials": {row["part_name"]: row["material"] for row in materials},
        "usage": {
            row["category"]: {
                "status": row["status"],
                "conditions": json.loads(row["conditions_json"] or "[]"),
            }
            for row in usage_rules
        },
    }


def create_feedback(payload: FeedbackCreate, user_email: Optional[str] = None) -> FeedbackRecord:
    created_at = _utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO feedback_records (
                usage_log_id, user_email, feedback_type, original_prediction_json,
                user_correction_json, comment, review_status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            """,
            (
                payload.logId,
                user_email,
                payload.feedbackType,
                _dumps(payload.originalPrediction),
                _dumps(payload.userCorrection),
                payload.comment,
                created_at.isoformat(),
                created_at.isoformat(),
            ),
        )
        feedback_id = int(cursor.lastrowid)
        if payload.logId:
            _enqueue_user_feedback_review(connection, payload.logId, created_at)

    return FeedbackRecord(
        id=feedback_id,
        userEmail=user_email,
        reviewStatus="pending",
        createdAt=created_at,
        updatedAt=created_at,
        **payload.model_dump(),
    )


def list_review_queue(status: str = "pending", limit: int = 50) -> list[ReviewQueueItem]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT rq.*, ul.item_name, ul.detected_material, ul.overall_risk
            FROM review_queue rq
            JOIN usage_logs ul ON ul.id = rq.usage_log_id
            WHERE rq.status = ?
            ORDER BY rq.review_score DESC, datetime(rq.created_at) ASC
            LIMIT ?
            """,
            (status, limit),
        ).fetchall()
    return [_row_to_review_queue_item(row) for row in rows]


def update_review_queue_status(review_id: int, status: str, assigned_to: Optional[str] = None) -> ReviewQueueItem | None:
    updated_at = _utc_now()
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE review_queue
            SET status = ?, assigned_to = COALESCE(?, assigned_to), updated_at = ?
            WHERE id = ?
            """,
            (status, assigned_to, updated_at.isoformat(), review_id),
        )
        row = connection.execute(
            """
            SELECT rq.*, ul.item_name, ul.detected_material, ul.overall_risk
            FROM review_queue rq
            JOIN usage_logs ul ON ul.id = rq.usage_log_id
            WHERE rq.id = ?
            """,
            (review_id,),
        ).fetchone()
    return _row_to_review_queue_item(row) if row else None


def _enqueue_user_feedback_review(connection: sqlite3.Connection, log_id: int, created_at: datetime) -> None:
    existing = connection.execute("SELECT id, reasons_json FROM review_queue WHERE usage_log_id = ?", (log_id,)).fetchone()
    reasons = ["user_reported_error"]
    if existing:
        existing_reasons = json.loads(existing["reasons_json"] or "[]")
        reasons = list(dict.fromkeys([*existing_reasons, *reasons]))
        connection.execute(
            """
            UPDATE review_queue
            SET review_score = 1.0, reasons_json = ?, status = 'pending', updated_at = ?
            WHERE usage_log_id = ?
            """,
            (_dumps(reasons), created_at.isoformat(), log_id),
        )
        return
    connection.execute(
        """
        INSERT INTO review_queue (
            usage_log_id, review_score, reasons_json, status, created_at, updated_at
        )
        VALUES (?, 1.0, ?, 'pending', ?, ?)
        """,
        (log_id, _dumps(reasons), created_at.isoformat(), created_at.isoformat()),
    )


def _row_to_review_queue_item(row: sqlite3.Row) -> ReviewQueueItem:
    return ReviewQueueItem(
        id=row["id"],
        usageLogId=row["usage_log_id"],
        reviewScore=row["review_score"],
        reasons=json.loads(row["reasons_json"] or "[]"),
        status=row["status"],
        assignedTo=row["assigned_to"],
        itemName=row["item_name"],
        detectedMaterial=row["detected_material"],
        overallRisk=row["overall_risk"],
        createdAt=datetime.fromisoformat(row["created_at"]),
        updatedAt=datetime.fromisoformat(row["updated_at"]),
    )


def _seed_product_database(connection: sqlite3.Connection) -> None:
    created_at = _utc_now().isoformat()
    products = [
        {
            "barcode": "8801234567890",
            "product_name": "즉석식품 PP 용기",
            "manufacturer": "Can I 샘플 제조사",
            "verified": 1,
            "data_confidence": 0.95,
            "materials": {"body": "pp", "lid": "pet", "label": "paper"},
            "usage": {
                "microwave": {"status": "allowed_with_conditions", "conditions": ["뚜껑 제거", "2분 이내 가열"]},
                "freezer": {"status": "allowed", "conditions": []},
                "dishwasher": {"status": "not_recommended", "conditions": ["일회용 뚜껑은 변형 가능"]},
            },
        }
    ]
    for product in products:
        connection.execute(
            """
            INSERT OR IGNORE INTO product_barcodes (
                barcode, product_name, manufacturer, source, verified,
                data_confidence, created_at, updated_at
            )
            VALUES (?, ?, ?, 'internal_product_db', ?, ?, ?, ?)
            """,
            (
                product["barcode"],
                product["product_name"],
                product["manufacturer"],
                product["verified"],
                product["data_confidence"],
                created_at,
                created_at,
            ),
        )
        for part_name, material in product["materials"].items():
            exists = connection.execute(
                "SELECT id FROM product_materials WHERE barcode = ? AND part_name = ?",
                (product["barcode"], part_name),
            ).fetchone()
            if not exists:
                connection.execute(
                    "INSERT INTO product_materials (barcode, part_name, material, created_at) VALUES (?, ?, ?, ?)",
                    (product["barcode"], part_name, material, created_at),
                )
        for category, rule in product["usage"].items():
            exists = connection.execute(
                "SELECT id FROM product_usage_rules WHERE barcode = ? AND category = ?",
                (product["barcode"], category),
            ).fetchone()
            if not exists:
                connection.execute(
                    """
                    INSERT INTO product_usage_rules (barcode, category, status, conditions_json, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (product["barcode"], category, rule["status"], _dumps(rule["conditions"]), created_at),
                )
