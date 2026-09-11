from app.data.db import create_db_engine, init_db, make_session_factory

_engine = None
_SessionFactory = None


def get_session_factory():
    global _engine, _SessionFactory
    if _SessionFactory is None:
        _engine = create_db_engine()
        init_db(_engine)
        _SessionFactory = make_session_factory(_engine)
    return _SessionFactory


def new_session():
    return get_session_factory()()
