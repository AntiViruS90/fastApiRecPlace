from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db import models

# Создаем асинхронный движок для работы с базой данных
engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URL, echo=True)

# Создаем сессионный класс для работы с базой
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Получаем сессию базы данных
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# Функция для создания всех таблиц
async def create_db_and_tables():
    # Создаём таблицы в базе данных на основе всех моделей
    async with engine.begin() as conn:

        # Создаём все таблицы
        await conn.run_sync(models.Base.metadata.create_all)
