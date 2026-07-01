"""Authentication utilities for JWT and password management."""

import hashlib
import os
import secrets
import time

import bcrypt
import jwt
from dotenv import load_dotenv

load_dotenv()


JWT_SECRET = os.environ.get("secret") or "medi-hub-jwt-secret"
JWT_ALGORITHM = os.environ.get("algorithm", "HS256")
OTP_SECRET = os.environ.get("otp_secret", JWT_SECRET or "medi-hub-otp-secret")


def signJWT(user_role: str, id: str, expiry_duration: int = 3600) -> str:
    """
    Create a signed JWT access token for the given user.

    The token payload contains:
        - user_role: role of the user (e.g., "USER", "ADMIN")
        - id: user's unique identifier (ObjectId as string)
        - expires: Unix timestamp when this token expires

    Args:
        user_role: Role string from UserRole enum
        id: User ID as string
        expiry_duration: Seconds until expiry (default 15 minutes)

    Returns:
        str: Signed JWT token string
    """
    payload = {
        "user_role": user_role,
        "id": id,
        "expires": time.time() + expiry_duration,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decodeJWT(token: str) -> dict | None:
    """
    Decode and validate a JWT token.

    Returns the decoded payload if valid and not expired.
    Returns None if the token is invalid or expired.

    Args:
        token: JWT string to decode

    Returns:
        dict | None: Decoded payload or None
    """
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded if decoded.get("expires", 0) > time.time() else None
    except Exception:
        return None


def encrypt_password(password: str) -> str:
    """Hash a plain-text password with bcrypt.

    The application uses the native ``bcrypt`` library directly because the
    currently installed ``passlib`` + ``bcrypt`` combination in this repo can
    mis-handle valid short passwords during hashing and verification.
    """

    password_bytes = password.encode("utf-8")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash.

    Returns ``False`` for malformed stored hashes instead of raising a runtime
    error during login.
    """

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP with the requested number of digits."""
    return "".join(secrets.choice("0123456789") for _ in range(length))


def hash_otp(otp: str) -> str:
    """Hash an OTP before persisting it to storage."""
    payload = f"{otp}:{OTP_SECRET}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify_hashed_otp(plain_otp: str, hashed_otp: str) -> bool:
    """Compare a plain OTP against its hashed representation."""
    return secrets.compare_digest(hash_otp(plain_otp), hashed_otp)
