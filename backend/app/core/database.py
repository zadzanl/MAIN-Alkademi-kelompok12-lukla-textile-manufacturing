import uuid
from typing import Optional, Generator
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import Pool
from .config import settings

# Engine for application database access
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

@event.listens_for(Pool, "reset")
def receive_reset(dbapi_connection, connection_record, reset_state):
    """
    Execute RESET ALL / rollback on pool return.
    Ensures transaction-local GUCs (app.tenant_id) never leak across pooled connections.
    Uses autocommit mode so connection returns in clean IDLE state.
    """
    if dbapi_connection is None:
        return
    try:
        if hasattr(dbapi_connection, "rollback"):
            dbapi_connection.rollback()
        was_autocommit = getattr(dbapi_connection, "autocommit", False)
        if not was_autocommit:
            dbapi_connection.autocommit = True
        try:
            with dbapi_connection.cursor() as cursor:
                cursor.execute("RESET ALL;")
        finally:
            if not was_autocommit:
                dbapi_connection.autocommit = False
    except Exception:
        try:
            if hasattr(dbapi_connection, "rollback"):
                dbapi_connection.rollback()
        except Exception:
            pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def set_db_tenant_context(
    session: Session,
    tenant_id: uuid.UUID,
    actor_id: Optional[uuid.UUID] = None,
    role: Optional[str] = None
) -> None:
    """Set transaction-local tenant context securely."""
    session.execute(
        text("SELECT set_request_context(:tenant_id, :actor_id, :role)"),
        {
            "tenant_id": str(tenant_id),
            "actor_id": str(actor_id) if actor_id else None,
            "role": role
        }
    )
