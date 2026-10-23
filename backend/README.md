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
- Verificação de funcionamento: http://127.0.0.1:8000/api/health

## Verificar o banco

Dentro de `backend/`, execute uma consulta sem criar tabelas:

```bash
uv run --env-file .env python -c 'from sqlalchemy import text; from app.database import engine; conn = engine.connect(); print(conn.execute(text("SELECT 1")).scalar_one()); conn.close(); engine.dispose()'
```

O resultado esperado é `1`. O arquivo `app/database.py` fornece a conexão e `get_session`, que poderá ser usado pelas rotas com `Depends`. A sessão é fechada ao final da requisição; cada operação de escrita será responsável por confirmar sua transação com `commit()`.

O endpoint `/api/health` continua verificando apenas se a API responde, sem consultar o banco.

## Catálogo e gestão de cursos

O módulo `app/courses` implementa os fluxos F01, F07, F08, F09, F10, F27,
F35, F36, F39 e F40. A documentação interativa dos contratos fica em
`http://127.0.0.1:8000/docs`.

Principais endpoints públicos:

- `GET /api/landing`
- `GET /api/courses`
- `GET /api/search?q=...`
- `GET /api/courses/{course_id}`
- `GET /api/recommendations`
- `GET /api/courses/{course_id}/materials`

Principais endpoints do professor:

- `GET /api/teacher/courses`
- `POST /api/courses`
- `PATCH /api/courses/{course_id}`
- `POST /api/courses/{course_id}/lessons`
- `POST /api/courses/{course_id}/materials`
- `POST /api/courses/{course_id}/materials/upload`
- `GET /api/courses/{course_id}/preview`
- `POST /api/courses/{course_id}/publication`

Enquanto o módulo definitivo de autenticação não estiver integrado, as rotas do
professor recebem `X-Teacher-Id` e `X-Teacher-Name`. Recomendações e verificações
de matrícula recebem `X-Student-Id`.

Uploads são gravados em `MEDIA_ROOT`. Links de download são temporários e
assinados com `MEDIA_SIGNING_KEY`; troque a chave de exemplo em qualquer ambiente
que não seja exclusivamente local.

Para executar os testes:

```bash
uv run --all-groups --env-file .env pytest -q
```

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

## Deploy no Render

O arquivo `render.yaml`, na raiz do repositório, descreve um Blueprint com a API
e um PostgreSQL gerenciado. No painel do Render, crie um **Blueprint**, conecte o
repositório e selecione esse arquivo. O serviço acompanha a branch
`backend_lucas`, executa as migrações antes de iniciar o Uvicorn e verifica
`/api/health`.

No plano gratuito, o diretório local do serviço é temporário. Por isso,
`MEDIA_ROOT=/tmp/aprovaai-media` serve apenas para testes: uploads podem desaparecer
quando a instância reiniciar. Para produção, use armazenamento de objetos ou um
serviço pago com disco persistente.

Após o deploy, valide:

```text
https://<nome-do-servico>.onrender.com/api/health
https://<nome-do-servico>.onrender.com/docs
```
