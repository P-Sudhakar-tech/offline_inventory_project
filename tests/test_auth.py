import pytest

from app.data.db import create_db_engine, init_db, make_session_factory
from app.security.session_context import get_current_user, set_current_user
from app.services.audit import recent_audit_log
from app.services.auth import (
    DuplicateUsernameError,
    InvalidCredentialsError,
    InvalidRoleError,
    authenticate,
    change_password,
    change_role,
    create_user,
    has_any_user,
    list_users,
    set_user_active,
)


@pytest.fixture()
def session():
    engine = create_db_engine(db_path=":memory:")
    init_db(engine)
    factory = make_session_factory(engine)
    with factory() as s:
        yield s


@pytest.fixture(autouse=True)
def reset_current_user():
    previous = get_current_user()
    set_current_user(None)
    yield
    set_current_user(previous)


def test_has_any_user_false_then_true(session):
    assert has_any_user(session) is False
    create_user(session, "admin", "correct horse battery staple", role="admin")
    session.commit()
    assert has_any_user(session) is True


def test_password_is_never_stored_in_plaintext(session):
    user = create_user(session, "admin", "supersecret", role="admin")
    session.commit()
    assert "supersecret" not in user.password_hash
    assert user.password_hash != "supersecret"


def test_authenticate_succeeds_with_correct_password(session):
    create_user(session, "alice", "hunter2", role="operator")
    session.commit()

    user = authenticate(session, "alice", "hunter2")
    assert user.username == "alice"


def test_authenticate_fails_with_wrong_password(session):
    create_user(session, "alice", "hunter2", role="operator")
    session.commit()

    with pytest.raises(InvalidCredentialsError):
        authenticate(session, "alice", "wrong-password")


def test_authenticate_fails_for_deactivated_user(session):
    user = create_user(session, "bob", "password123", role="viewer")
    session.commit()
    set_user_active(session, user.id, False)
    session.commit()

    with pytest.raises(InvalidCredentialsError):
        authenticate(session, "bob", "password123")


def test_create_user_rejects_duplicate_username(session):
    create_user(session, "admin", "pw1", role="admin")
    with pytest.raises(DuplicateUsernameError):
        create_user(session, "admin", "pw2", role="manager")


def test_create_user_rejects_invalid_role(session):
    with pytest.raises(InvalidRoleError):
        create_user(session, "admin", "pw1", role="superuser")


def test_change_role_and_password(session):
    user = create_user(session, "carol", "oldpassword", role="viewer")
    session.commit()

    change_role(session, user.id, "manager")
    change_password(session, user.id, "newpassword")
    session.commit()

    assert authenticate(session, "carol", "newpassword").role == "manager"
    with pytest.raises(InvalidCredentialsError):
        authenticate(session, "carol", "oldpassword")


def test_list_users_returns_created_users(session):
    create_user(session, "zeta", "pw", role="viewer")
    create_user(session, "alpha", "pw", role="viewer")
    session.commit()

    names = [u.username for u in list_users(session)]
    assert names == ["alpha", "zeta"]


def test_login_attempts_are_audited(session):
    create_user(session, "admin", "correct-password", role="admin")
    session.commit()

    with pytest.raises(InvalidCredentialsError):
        authenticate(session, "admin", "wrong-password")
    authenticate(session, "admin", "correct-password")

    entries = recent_audit_log(session)
    actions = [log.action for log, _ in entries]
    assert "login_failed" in actions
    assert "login_success" in actions
