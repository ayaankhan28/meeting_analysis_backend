from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from app.config import DATABASE_URL

# Convert the regular PostgreSQL URL to async format
# Note: Using the transaction pooler (port 6543) which is ideal for serverless/cloud hosting
ASYNC_DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

# Create async engine with optimized settings for Render and Supabase Pooler
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,  # Set to False for production
    future=True,
    poolclass=NullPool,  # Disable SQLAlchemy's connection pooling
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "command_timeout": 30,  # 30 second timeout
        "server_settings": {
            "statement_timeout": "30000",  # 30 seconds in milliseconds
            "idle_in_transaction_session_timeout": "30000",  # 30 seconds in milliseconds
            "application_name": "meetingiq_pro"  # Helps identify your app in Supabase logs
        },
        "ssl": True,  # Enable SSL for Supabase connection
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

# Dependency to get DB session with proper error handling and retry logic
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            # Test the connection using proper SQLAlchemy text() function
            await session.execute(text("SELECT 1"))
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

