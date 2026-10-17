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

Os endpoints de mídia são de desenvolvimento, ainda sem autorização ou associação com aula. Arquivos armazenados não são versionados no Git.

## Consultar e reproduzir vídeo

Use o `id` retornado pelo upload:

- `GET /api/media/{id}`: consulta os metadados, sem expor o caminho no disco.
- `GET /api/media/{id}/content`: entrega o arquivo para reprodução no navegador.

Abra `http://127.0.0.1:8000/api/media/{id}/content` no navegador, substituindo `{id}` pelo identificador. A reprodução depende de o arquivo ser um vídeo válido com codecs suportados pelo navegador.

Para solicitar apenas um trecho:

```bash
curl -i -H 'Range: bytes=0-15' http://127.0.0.1:8000/api/media/ID/content
```

O servidor retorna `206 Partial Content` e `Content-Range` para um intervalo válido. Um intervalo fora do arquivo retorna `416`. Mídia inexistente retorna `404`; na rota de conteúdo, mídia não disponível ou arquivo ausente também retorna `404`. Os metadados continuam consultáveis se apenas o arquivo estiver ausente.

## Aulas e associação de vídeo

Depois de aplicar as migrações, use os endpoints no `/docs`:

1. `POST /api/learning/lessons`: cria uma aula sem vídeo.
2. `POST /api/media`: envia um vídeo e retorna seu `id`.
3. `PATCH /api/learning/lessons/{lesson_id}/media`: associa o vídeo já enviado com `{"media_id": "UUID-da-midia"}`.
4. `GET /api/learning/courses/{course_id}/lessons`: lista as aulas em ordem de `position`, incluindo `media_id`.

Exemplo de criação de aula:

```json
{
  "course_id": "fisica-quantica",
  "title": "Introdução",
  "description": "Contexto histórico da física quântica",
  "position": 1
}
```

O backend gera o identificador da aula como uma string UUID. `course_id` aceita os identificadores textuais do frontend, mas ainda não consulta nem valida a existência do curso em outro módulo. As aulas demonstrativas existentes no frontend não são importadas automaticamente.

A posição começa em 1 e é única dentro do curso (`409` em caso de conflito). Curso sem aulas retorna uma lista vazia. Associação exige aula e mídia existentes (`404`) e mídia no estado `available` (`409` caso contrário). Essa validação consulta os metadados; a rota de conteúdo continua responsável por verificar a existência do arquivo.

É possível substituir o vídeo associado ou repetir a mesma associação. Nenhum vídeo antigo é excluído. Uploads sem associação permanecem acessíveis pelo identificador. Ainda não há autorização, integração com as telas, reordenação ou limpeza automática de mídias.

## Abrir uma aula para reprodução

`GET /api/learning/lessons/{lesson_id}/playback` retorna os dados da aula, `media_id` e `content_url`, um caminho relativo da API para o vídeo. Use esse caminho no mesmo servidor da API para acessar o conteúdo.

Antes de retornar, verifica a existência da aula, a associação de vídeo, o estado `available` e o arquivo no armazenamento. Aula sem vídeo retorna `409`; aula inexistente, mídia indisponível ou arquivo ausente retorna `404`. A resposta não expõe caminhos no disco e não altera dados.

Ainda não há autenticação, verificação de direito de acesso ou posição salva. A URL não é assinada nem temporária nesta etapa. A disponibilidade do arquivo é verificada novamente na rota de conteúdo.

## Testes do backend

```bash
uv run python -m pytest
```

Os testes de upload e consulta usam SQLite e arquivos temporários, sem alterar o PostgreSQL ou os vídeos locais. Verificam os bytes entregues e HTTP Range; não testam decodificação ou reprodução visual no navegador.
