from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker

@contextmanager
def session_scope(db_engine, sessionmaker_=sessionmaker, **kwargs):
    """
    Provide a scoped db session for a series of operations.
    The session is created immediately before the scope begins, and is closed
    on scope exit.
    """
    db_session = sessionmaker_(bind=db_engine, **kwargs)()
    try:
        yield db_session
    finally:
        db_session.close()
