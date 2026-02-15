"""Database connection and session management."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from termical.models import Base


class Database:
    """Database connection manager."""
    
    def __init__(self, connection_string: str):
        """Initialize database connection.
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.engine = create_engine(
            connection_string,
            poolclass=NullPool,
            echo=False
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_tables(self) -> None:
        """Create all tables defined in models."""
        Base.metadata.create_all(self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    def verify_connection(self) -> bool:
        """Verify database connection is working.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
    
    def close(self) -> None:
        """Close database connection."""
        self.engine.dispose()


# Global database instance (initialized during setup)
_db: Database | None = None


def get_database() -> Database:
    """Get the global database instance.
    
    Returns:
        Database instance
        
    Raises:
        RuntimeError: If database not initialized
    """
    if _db is None:
        raise RuntimeError("Database not initialized. Run 'termical setup' first.")
    return _db


def init_database(connection_string: str) -> Database:
    """Initialize the global database instance.
    
    Args:
        connection_string: PostgreSQL connection string
        
    Returns:
        Initialized Database instance
    """
    global _db
    _db = Database(connection_string)
    return _db
