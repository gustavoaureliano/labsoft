# Backend — AprovaAí

Estrutura inicial da API em Python com FastAPI.

## Requisitos

- Python 3.12 ou superior
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- PostgreSQL com usuário e banco criados

## Executar

Dentro de `backend/`, instale as dependências:

```bash
uv sync --locked
```

Copie `.env.example` para `.env` e preencha a senha do PostgreSQL na variável `DATABASE_URL`:

```bash
cp .env.example .env
```

O arquivo `.env` é local e não é versionado. O `uv` carrega suas variáveis com `--env-file`.

Inicie o servidor de desenvolvimento:

```bash
uv run --env-file .env uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Documentação Swagger: http://127.0.0.1:8000/docs
- Verificação de funcionamento: http://127.0.0.1:8000/api/health

No Swagger, clique em **Authorize** e informe o e-mail no campo `username` e a
senha da conta. A API obtém o token automaticamente. O endpoint JSON
`POST /api/v1/auth/login` continua disponível para os clientes da aplicação.

## Verificar o banco

Dentro de `backend/`, execute uma consulta sem criar tabelas:

```bash
uv run --env-file .env python -c 'from sqlalchemy import text; from app.database import engine; conn = engine.connect(); print(conn.execute(text("SELECT 1")).scalar_one()); conn.close(); engine.dispose()'
```

O resultado esperado é `1`. O arquivo `app/database.py` fornece a conexão e `get_session`, que poderá ser usado pelas rotas com `Depends`. A sessão é fechada ao final da requisição; cada operação de escrita será responsável por confirmar sua transação com `commit()`.

O endpoint `/api/health` continua verificando apenas se a API responde, sem consultar o banco.

## Migrações

O Alembic usa a mesma `DATABASE_URL` da aplicação. Para criar ou atualizar as tabelas, execute dentro de `backend/`:

```bash
uv run --env-file .env alembic upgrade head
```

Para consultar a revisão aplicada:

```bash
uv run --env-file .env alembic current
```

A primeira migração cria `media`, com identificador UUID, chave relativa do arquivo, nome original, tipo, tamanho em bytes, estado e data de criação. Os estados permitidos são `pending`, `available` e `failed`. O arquivo fica no disco; a tabela guarda apenas seus metadados.

Ao alterar modelos, gere uma migração e revise o arquivo antes de aplicá-lo:

```bash
uv run --env-file .env alembic revision --autogenerate -m "Describe schema change"
uv run --env-file .env alembic upgrade head
```

Novos modelos precisam ser importados em `migrations/env.py` para que o Alembic reconheça suas tabelas. As migrações ficam versionadas em `migrations/versions/`.
