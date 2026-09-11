"""Tracks the currently logged-in user for this process.

The application is a single-operator desktop app: one login is active at a
time, so a process-wide "current user" is simpler and safer than threading a
user id through every service call, and it is exactly what audit logging
needs to attribute actions to a person.
"""

_current_user = None


def set_current_user(user) -> None:
    global _current_user
    _current_user = user


def get_current_user():
    return _current_user


def current_user_id():
    return _current_user.id if _current_user is not None else None
