from fastapi import APIRouter

from app.models.schemas import AuthSession, GoogleLoginRequest
from app.services.auth_service import verify_google_credential

router = APIRouter()


@router.post("/auth/google", response_model=AuthSession)
def login_with_google(payload: GoogleLoginRequest) -> AuthSession:
    return verify_google_credential(payload.credential)
