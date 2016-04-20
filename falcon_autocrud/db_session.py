from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker

@contextmanager
def session_scope(db_engine):
    """
    Provide a scoped db session for a series of operarions.
    The session is created immediately before the scope begins, and is closed
    on scope exit.
    """
    db_session = sessionmaker(bind=db_engine)()
    try:
        yield db_session
    finally:
        db_session.close()
