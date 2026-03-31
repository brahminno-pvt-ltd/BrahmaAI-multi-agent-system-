"""
BrahmaAI Auth Routes
Basic JWT authentication.
"""
import time
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import hashlib
import hmac
import base64
import json
from backend.config.settings import settings

router = APIRouter()
security = HTTPBearer(auto_error=False)

# Demo users (replace with DB in production)
DEMO_USERS = {
    "admin": hashlib.sha256(b"brahmaai123").hexdigest(),
    "demo": hashlib.sha256(b"demo").hexdigest(),
}


class LoginRequest(BaseModel):
    username: str
    password: str


def create_token(username: str) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode()
    payload = base64.urlsafe_b64encode(json.dumps({
        "sub": username,
        "exp": time.time() + settings.JWT_EXPIRE_MINUTES * 60,
        "iat": time.time(),
    }).encode()).decode()
    sig_input = f"{header}.{payload}"
    sig = base64.urlsafe_b64encode(
        hmac.new(settings.JWT_SECRET.encode(), sig_input.encode(), hashlib.sha256).digest()
    ).decode()
    return f"{header}.{payload}.{sig}"


def verify_token(token: str) -> dict | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict | None:
    if not credentials:
        return None
    payload = verify_token(credentials.credentials)
    return payload


@router.post("/login")
async def login(request: LoginRequest):
    """Authenticate and receive a JWT token."""
    pw_hash = hashlib.sha256(request.password.encode()).hexdigest()
    if DEMO_USERS.get(request.username) != pw_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(request.username)
    role = "admin" if request.username == "admin" else "user"
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": request.username,
        "role": role,
        "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
    }


@router.get("/me")
async def me(user: dict | None = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    username = user.get("sub", "")
    role = "admin" if username == "admin" else "user"
    return {"username": username, "role": role, "authenticated": True}
