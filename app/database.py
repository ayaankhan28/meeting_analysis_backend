from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from app.config import DATABASE_URL

# Convert the regular PostgreSQL URL to async format
ASYNC_DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

# Create async engine with optimized settings for Render and Supabase
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,  # Set to False for production
    future=True,
    poolclass=NullPool,  # Disable SQLAlchemy's connection pooling since Supabase handles it
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "command_timeout": 60,  # 60 second timeout
        "server_settings": {
            "statement_timeout": "60000",  # 60 seconds in milliseconds
            "idle_in_transaction_session_timeout": "60000"  # 60 seconds in milliseconds
        }
    },
)

# Create async session factory with appropriate settings
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Create declarative base
Base = declarative_base()

# Dependency to get DB session with proper error handling
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            # Test the connection
            await session.execute("SELECT 1")
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

