import os

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


def claims_from_token(token: str) -> dict:
    """Validate a Supabase access token and return its signed claims."""
    secret = os.getenv("SUPABASE_JWT_SECRET")
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth not configured",
        )
    try:
        audience = os.getenv("SUPABASE_JWT_AUDIENCE")
        issuer = os.getenv("SUPABASE_JWT_ISSUER")
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=audience if audience else None,
            issuer=issuer if issuer else None,
            options={"verify_aud": bool(audience), "verify_iss": bool(issuer)},
        )
        if not payload.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing sub",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        ) from None
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from None


def identity_from_token(token: str) -> str:
    return str(claims_from_token(token)["sub"])


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    return identity_from_token(credentials.credentials)


def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    claims = claims_from_token(credentials.credentials)
    metadata = claims.get("app_metadata") or {}
    role = metadata.get("role") or claims.get("role")
    if role not in {"admin", "service_role"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required")
    return str(claims["sub"])
