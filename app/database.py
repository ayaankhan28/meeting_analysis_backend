# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import declarative_base, sessionmaker
# from app.config import DATABASE_URL

# # Convert the regular PostgreSQL URL to async format
# ASYNC_DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

# # Create async engine
# engine = create_async_engine(
#     ASYNC_DATABASE_URL,
#     echo=True,  # Set to False in production
#     future=True
# )

# # Create async session factory
# AsyncSessionLocal = sessionmaker(
#     engine,
#     class_=AsyncSession,
#     expire_on_commit=False
# )

# # Create declarative base
# Base = declarative_base()

# # Dependency to get DB session
# async def get_db() -> AsyncSession:
#     async with AsyncSessionLocal() as session:
#         try:
#             yield session
#         finally:
#             await session.close() 
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import DATABASE_URL

# Convert the sync URL to async URL
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine with connection pooling
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,  # Set to False in production
    future=True,
    pool_size=10,        # Number of open connections to keep in pool
    max_overflow=20,     # Extra connections to allow beyond pool_size
    pool_timeout=30,     # Seconds to wait for a connection before timeout
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Declarative base class for models
Base = declarative_base()

# Dependency to get DB session (use in FastAPI)
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
