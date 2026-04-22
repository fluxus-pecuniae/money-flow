"""Database engine and session factories."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.config.settings import get_settings

settings = get_settings()

engine = create_engine(
    settings.database.sqlalchemy_url,
    echo=settings.database.echo,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

