from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Float,
    Text
)

from sqlalchemy.orm import mapped_column, DeclarativeBase, Mapped, relationship


# Создаем базовый класс для всех моделей
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))

    favorites = relationship("Favorite", back_populates="user")


class Favorite(Base):
    __tablename__ = 'favorites'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kinopoisk_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(255))
    year: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="favorites")


class MovieDB(Base):
    __tablename__ = 'movies'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kinopoisk_id: Mapped[int] = mapped_column(Integer, index=True, unique=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    description: Mapped[str] = Column(Text, nullable=True)
    rating: Mapped[int] = mapped_column(Float, nullable=True)
    poster_url: Mapped[str] = mapped_column(String(255), nullable=True)
