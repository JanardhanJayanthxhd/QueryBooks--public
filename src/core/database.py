from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.constants import CONNECTION

engine = create_engine(url=CONNECTION)
session_local = sessionmaker(autoflush=False, autocommit=False, bind=engine)


def get_db():
    db = session_local()
    try:
        yield db
    except Exception:
        raise
    finally:
        db.close()
