import hashlib
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.models import ROLES, User
from app.services.audit import log_action

PBKDF2_ITERATIONS = 200_000


class DuplicateUsernameError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidRoleError(Exception):
    pass


def _hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS).hex()


def has_any_user(session: Session) -> bool:
    return session.scalar(select(User.id).limit(1)) is not None


def create_user(session: Session, username: str, password: str, role: str) -> User:
    username = username.strip()
    if role not in ROLES:
        raise InvalidRoleError(f"Invalid role: {role}")
    existing = session.scalar(select(User).where(User.username == username))
    if existing is not None:
        raise DuplicateUsernameError(f"Username '{username}' already exists")

    salt = secrets.token_bytes(16)
    user = User(
        username=username,
        password_hash=_hash_password(password, salt),
        salt=salt.hex(),
        role=role,
        is_active=True,
    )
    session.add(user)
    session.flush()
    log_action(session, "user_created", f"username={username} role={role}")
    return user


def authenticate(session: Session, username: str, password: str) -> User:
    """Log in a user, committing its own audit entry either way.

    Unlike the other service functions, this commits internally: a login
    attempt is a complete unit of work from the UI's point of view, and a
    failed attempt must still be recorded even though the caller never
    reaches a commit() after the exception below.
    """
    user = session.scalar(select(User).where(User.username == username.strip()))
    if user is None or not user.is_active:
        log_action(session, "login_failed", f"username={username}")
        session.commit()
        raise InvalidCredentialsError("Invalid username or password")

    salt = bytes.fromhex(user.salt)
    if _hash_password(password, salt) != user.password_hash:
        log_action(session, "login_failed", f"username={username}")
        session.commit()
        raise InvalidCredentialsError("Invalid username or password")

    log_action(session, "login_success", f"username={username}")
    session.commit()
    return user


def list_users(session: Session):
    return session.scalars(select(User).order_by(User.username)).all()


def set_user_active(session: Session, user_id: int, is_active: bool) -> User:
    user = session.get(User, user_id)
    user.is_active = is_active
    log_action(session, "user_status_changed", f"user_id={user_id} is_active={is_active}")
    session.flush()
    return user


def change_role(session: Session, user_id: int, role: str) -> User:
    if role not in ROLES:
        raise InvalidRoleError(f"Invalid role: {role}")
    user = session.get(User, user_id)
    user.role = role
    log_action(session, "user_role_changed", f"user_id={user_id} role={role}")
    session.flush()
    return user


def change_password(session: Session, user_id: int, new_password: str) -> User:
    user = session.get(User, user_id)
    salt = secrets.token_bytes(16)
    user.password_hash = _hash_password(new_password, salt)
    user.salt = salt.hex()
    log_action(session, "password_changed", f"user_id={user_id}")
    session.flush()
    return user
