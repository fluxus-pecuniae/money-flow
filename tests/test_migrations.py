from __future__ import annotations

import os
import subprocess
import sys

import psycopg
from sqlalchemy.engine import make_url


def test_alembic_upgrade_head_smoke() -> None:
    database_url = os.environ.get("TEST_DATABASE_URL")
    assert database_url, "TEST_DATABASE_URL must be set for migration smoke tests."

    url = make_url(database_url)
    env = os.environ.copy()
    with psycopg.connect(
        dbname="postgres",
        host=url.host or "127.0.0.1",
        port=url.port or 5432,
        user=url.username or None,
        password=url.password or None,
        autocommit=True,
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (url.database,),
            )
            exists = cursor.fetchone()
            if exists is None:
                cursor.execute(f'CREATE DATABASE "{url.database}"')

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=False,
        capture_output=True,
        text=True,
        env={
            **env,
            "APP_ENV": env.get("APP_ENV", "dev"),
            "DB_HOST": url.host or "127.0.0.1",
            "DB_PORT": str(url.port or 5432),
            "DB_NAME": url.database or "money_flow",
            "DB_USER": url.username or "",
            "DB_PASSWORD": url.password or "",
        },
    )
    assert result.returncode == 0, result.stderr or result.stdout
