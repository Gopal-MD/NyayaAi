"""Firebase Admin token verification and FastAPI dependency."""
import json
import os
from functools import lru_cache
from typing import Annotated

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
_bearer = HTTPBearer(auto_error=False)


@lru_cache
def _init_firebase() -> firebase_admin.App:
    """Initialise Firebase Admin SDK (once)."""
    if firebase_admin._apps:
        return firebase_admin.get_app()

    # Prefer inline JSON env var (for cloud deployments)
    if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
        try:
            sa_dict = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
            cred = credentials.Certificate(sa_dict)
            return firebase_admin.initialize_app(cred)
        except Exception as exc:
            logger.warning("firebase_inline_cred_failed", error=str(exc))

    # Fall back to file path
    if settings.FIREBASE_SERVICE_ACCOUNT_PATH and os.path.exists(
        settings.FIREBASE_SERVICE_ACCOUNT_PATH
    ):
        cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
        return firebase_admin.initialize_app(cred)

    # Dev-only fallback: no credentials (token verification will fail gracefully)
    logger.warning(
        "firebase_no_credentials",
        msg="No Firebase credentials found. Token verification will fail.",
    )
    return firebase_admin.initialize_app(
        options={"projectId": settings.FIREBASE_PROJECT_ID or "dev-project"}
    )


def verify_firebase_token(token: str) -> dict:
    """Verify a Firebase ID token and return decoded claims."""
    _init_firebase()
    try:
        decoded = firebase_auth.verify_id_token(token, check_revoked=False)
        return decoded
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except firebase_auth.InvalidIdTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )
    except Exception as exc:
        logger.error("token_verification_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
        )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> dict:
    """FastAPI dependency: verifies the Bearer token and returns user info."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    decoded = verify_firebase_token(credentials.credentials)
    return {
        "user_id": decoded["uid"],
        "email": decoded.get("email", ""),
        "display_name": decoded.get("name", ""),
        "is_anonymous": decoded.get("firebase", {}).get("sign_in_provider") == "anonymous",
    }


CurrentUser = Annotated[dict, Depends(get_current_user)]
