"""Verifica a conexão do serviço sem criar tabelas ou alterar registros."""

import argparse
import os
import sys

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-database", required=True)
    parser.add_argument("--require-remote", action="store_true")
    args = parser.parse_args()

    raw_url = os.environ.get("DATABASE_URL")
    if not raw_url:
        print("ERRO: DATABASE_URL não foi configurada.", file=sys.stderr)
        return 1

    try:
        url = make_url(raw_url)
    except (SQLAlchemyError, ValueError):
        print("ERRO: DATABASE_URL tem um formato inválido.", file=sys.stderr)
        return 1

    try:
        if url.get_backend_name() != "postgresql":
            raise ValueError("DATABASE_URL deve apontar para PostgreSQL.")
        if args.require_remote and (
            not url.host or url.host.lower() in {"localhost", "127.0.0.1", "::1", "db"}
        ):
            raise ValueError("O teste remoto não aceita um banco local.")
        if url.database != args.expected_database:
            raise ValueError("DATABASE_URL aponta para um nome de banco diferente do esperado.")

        # Evita uma espera indefinida durante a inicialização do serviço.
        os.environ.setdefault("PGCONNECT_TIMEOUT", "10")
        from app.database import engine

        try:
            with engine.connect() as connection:
                with connection.begin():
                    connection.execute(text("SET TRANSACTION READ ONLY"))
                    database, user, schema = connection.execute(
                        text("SELECT current_database(), current_user, current_schema()")
                    ).one()
                    if database != args.expected_database:
                        raise ValueError("O servidor respondeu por um banco diferente do esperado.")
                    connection.execute(text("SELECT 1")).scalar_one()
            print(
                f"Conexão PostgreSQL OK: banco={database}, usuário={user}, "
                f"schema={schema}. Teste somente de leitura."
            )
        finally:
            engine.dispose()
    except ValueError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1
    except (SQLAlchemyError, ImportError):
        # Exceções de conexão podem conter a URL; não imprimir credenciais nos logs.
        print(
            "ERRO: não foi possível conectar ao PostgreSQL. Confira as credenciais, "
            "o host, o acesso de rede e a configuração TLS de DATABASE_URL.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
