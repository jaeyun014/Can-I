#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$ROOT_DIR/.dev-pids"
LOG_DIR="$ROOT_DIR/.dev-logs"
BACKEND_PID="$PID_DIR/backend.pid"
FRONTEND_PID="$PID_DIR/frontend.pid"

mkdir -p "$PID_DIR" "$LOG_DIR"

is_running() {
  local pid_file="$1"
  [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null
}

port_pids() {
  local port="$1"
  lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true
}

stop_port() {
  local port="$1"
  local pids
  pids="$(port_pids "$port")"

  if [[ -n "$pids" ]]; then
    echo "Stopping process on port $port: $pids"
    kill $pids 2>/dev/null || true
  fi
}

stop_one() {
  local name="$1"
  local pid_file="$2"

  if is_running "$pid_file"; then
    local pid
    pid="$(cat "$pid_file")"
    echo "Stopping $name ($pid)"
    kill "$pid"
  fi

  rm -f "$pid_file"
}

start_backend() {
  if is_running "$BACKEND_PID"; then
    echo "Backend already running ($(cat "$BACKEND_PID"))"
    return
  fi

  stop_port 8000

  if [[ ! -x "$ROOT_DIR/backend/venv/bin/uvicorn" ]]; then
    echo "Backend venv is missing. Run: cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
  fi

  echo "Starting backend on http://localhost:8000"
  (
    cd "$ROOT_DIR/backend"
    venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  ) >"$LOG_DIR/backend.log" 2>&1 &
  echo $! > "$BACKEND_PID"
}

start_frontend() {
  if is_running "$FRONTEND_PID"; then
    echo "Frontend already running ($(cat "$FRONTEND_PID"))"
    return
  fi

  stop_port 3000

  if [[ ! -d "$ROOT_DIR/frontend/node_modules" ]]; then
    echo "Frontend dependencies are missing. Run: cd frontend && npm install"
    exit 1
  fi

  rm -rf "$ROOT_DIR/frontend/.next"
  echo "Starting frontend on http://localhost:3000"
  (
    cd "$ROOT_DIR/frontend"
    npm run dev -- --hostname 0.0.0.0
  ) >"$LOG_DIR/frontend.log" 2>&1 &
  echo $! > "$FRONTEND_PID"
}

status_one() {
  local name="$1"
  local pid_file="$2"

  if is_running "$pid_file"; then
    echo "$name: running ($(cat "$pid_file"))"
  else
    echo "$name: stopped"
  fi
}

show_urls() {
  echo ""
  echo "Open on this Mac: http://localhost:3000"
  echo "Backend health:   http://localhost:8000/health"
  echo ""
  echo "Logs:"
  echo "  tail -f .dev-logs/frontend.log"
  echo "  tail -f .dev-logs/backend.log"
}

case "${1:-start}" in
  start)
    start_backend
    start_frontend
    show_urls
    ;;
  stop)
    stop_one "frontend" "$FRONTEND_PID"
    stop_one "backend" "$BACKEND_PID"
    stop_port 3000
    stop_port 8000
    ;;
  restart)
    "$0" stop
    "$0" start
    ;;
  status)
    status_one "backend" "$BACKEND_PID"
    status_one "frontend" "$FRONTEND_PID"
    backend_ports="$(port_pids 8000)"
    frontend_ports="$(port_pids 3000)"
    [[ -n "$backend_ports" ]] && echo "port 8000: in use ($backend_ports)"
    [[ -n "$frontend_ports" ]] && echo "port 3000: in use ($frontend_ports)"
    ;;
  logs)
    echo "== backend =="
    tail -n 40 "$LOG_DIR/backend.log" 2>/dev/null || true
    echo ""
    echo "== frontend =="
    tail -n 40 "$LOG_DIR/frontend.log" 2>/dev/null || true
    ;;
  *)
    echo "Usage: ./scripts/dev.sh [start|stop|restart|status|logs]"
    exit 1
    ;;
esac
