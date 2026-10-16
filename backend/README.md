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

## Upload de vídeo

Após aplicar as migrações e iniciar a API, abra http://127.0.0.1:8000/docs e use `POST /api/media`. Selecione um arquivo no campo `file` e execute a requisição.

Também é possível enviar pelo terminal:

```bash
curl -F 'file=@/caminho/aula.mp4;type=video/mp4' http://127.0.0.1:8000/api/media
```

- Aceita extensões `.mp4` e `.webm` com os tipos declarados `video/mp4` e `video/webm`, respectivamente. Ainda não inspeciona o conteúdo ou os codecs.
- O limite padrão é 100 MiB. Configure `MAX_UPLOAD_BYTES` para alterá-lo.
- Os arquivos são gravados em blocos, com nomes UUID, em `backend/storage/videos/`. `STORAGE_DIR` pode indicar outro diretório absoluto ou relativo a `backend/`.
- A resposta `201` contém o identificador e os metadados públicos da mídia. O estado `available` indica que o arquivo foi armazenado, não que seus codecs foram verificados.
- Arquivo vazio ou formato inválido retorna `400`. Tamanho excedido retorna `413`.
- A validação de tamanho acontece ao copiar o arquivo recebido. O parser multipart pode armazenar temporariamente a requisição antes disso; esse limite não é uma limitação do tráfego de entrada.

Este endpoint é de desenvolvimento, ainda sem autorização, associação com aula ou reprodução. Arquivos armazenados não são versionados no Git.

## Testes do backend

```bash
uv run python -m pytest
```

Os testes de upload usam SQLite e arquivos temporários, sem alterar o PostgreSQL ou os vídeos locais.
