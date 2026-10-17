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

- Aceita extensões `.mp4` e `.webm` com os tipos declarados `video/mp4` e `video/webm`, respectivamente.
- Novos uploads são inspecionados com `ffprobe` (instale FFmpeg no servidor). São aceitos MP4/H.264 e WebM/VP8/VP9, com duração positiva. A resposta inclui `duration_seconds` e `codec`. Isso não transcodifica nem garante suporte a todos os fluxos de áudio de cada navegador.
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

Há autorização usando os contratos de identidade e acesso; a identidade demo não é autenticação segura. A resposta inclui duração, posição salva e conclusão. A URL não é assinada nem temporária nesta etapa. A disponibilidade e a permissão são verificadas novamente na rota de conteúdo.

## Progresso

`PATCH /api/learning/lessons/{id}/progress` recebe `{"media_id": "UUID-atual", "position_seconds": 4.5}`. A identidade vem da dependência; prévias do professor não gravam progresso. Posição negativa/não finita é rejeitada; posição além da duração retorna `400`, vídeo alterado ou sem duração verificada retorna `409`.

A aula é concluída ao informar pelo menos 90% da duração. Isso não comprova que todos os segundos foram assistidos. Recuar o vídeo atualiza a posição sem desfazer a conclusão. Trocar o vídeo invalida efetivamente a posição/conclusão anterior. Os saves concorrentes são serializados por curso: a última gravação confirmada vence. Excluir aula remove seu progresso; o vídeo é preservado. A limpeza também preserva mídias referenciadas por progresso.

## Home e cursos do aluno

`GET /api/learning/courses` lista cursos acessíveis (ou cursos próprios para o professor). `GET /api/learning/courses/{id}` inclui aulas, seção padrão, estado de reprodução, thumbnails, progresso e aula para continuar. `GET /api/learning/dashboard` retorna os cursos, curso atual e recomendações/avisos dos contratos externos (vazios na implementação demo). Falhas nesses contratos opcionais não impedem a Home. Cursos sem aulas não estão concluídos. Cursos inacessíveis não são apresentados como reproduzíveis.

## Gerenciar aulas

- `PATCH /api/learning/lessons/{id}` altera título/descrição.
- `PATCH /api/learning/lessons/{id}/media` com `media_id: null` remove a associação, não o arquivo.
- `DELETE /api/learning/lessons/{id}` exclui a aula sem excluir seu vídeo.
- `PUT /api/learning/courses/{course_id}/lessons/order` recebe `{"lesson_ids": ["id2", "id1"]}` contendo todas as aulas do curso, sem duplicatas.

Todas essas operações são exclusivas do professor proprietário. A ordem é salva em transação; no PostgreSQL, um advisory lock por curso serializa alterações de ordem/criação/exclusão. Ordens concorrentes válidas seguem a última operação confirmada. Listas inválidas não alteram a ordem. Cursos sem seções externas usam uma única lista de aulas; não criamos outro gerenciador de módulos.

## Integrações individuais de desenvolvimento

`app/integrations.py` define contratos de usuário, curso e direito de acesso. A implementação local é ativada explicitamente com `LEARNING_DEMO_MODE=true` no `.env`; fora desse modo, a dependência responde `503` até a integração real ser configurada.

Identidades locais: `aluno-demo`, `aluno-demo-2`, `professor-demo` e `professor-demo-2`. O primeiro aluno acessa Física Quântica e Mecânica; o segundo apenas Mecânica. O segundo professor possui Biologia. Envie `X-Demo-User` na API ou o cookie `aprovaai_demo_user` (necessário também para requisições nativas de vídeo). Ambos são manipuláveis e **não constituem autenticação segura**. O cookie de papel do frontend não identifica sozinho um usuário.

Para criar aulas de exemplo sem sobrescrever registros ou posições existentes:

```bash
uv run --env-file .env python -m app.seed
```

Esse comando nunca roda ao iniciar o servidor. Não importa vídeos nem substitui o módulo de cursos dos outros integrantes.

As rotas de aula e mídia agora exigem identidade: professor proprietário cria/associa; aluno com acesso válido assiste; o professor proprietário pode visualizar prévias. O arquivo e as requisições Range passam pelas mesmas verificações. Upload não associado é privado do professor que o enviou.

Uploads anteriores ficam com `owner_id` nulo, sem atribuição automática. Para atribuir explicitamente uma mídia antiga:

```bash
uv run --env-file .env python -m app.claim_media UUID_DA_MIDIA professor-demo
```

O comando recusa mídia já atribuída e verifica o proprietário dos cursos associados. Não altera os arquivos. O professor do curso ainda pode visualizar uma mídia antiga associada, mas precisa atribuí-la antes de realizar uma nova associação. As integrações demo devem estar ativadas explicitamente também no servidor.

## Thumbnails e limpeza

`POST /api/media/thumbnails` recebe JPEG/PNG de até 5 MiB e 20 megapixels, validando a imagem com Pillow. Associe com `PATCH /api/learning/lessons/{id}/thumbnail` e `{"media_id": "UUID"}`; envie `null` para remover. A imagem usa a mesma rota protegida de conteúdo. A interface usará a capa do curso como fallback, sem extrair frames.

Limpeza explícita de uploads antigos não associados (vídeos ou thumbnails):

```bash
uv run --env-file .env python -m app.media.cleanup professor-demo --minimum-age-hours 24
uv run --env-file .env python -m app.media.cleanup professor-demo --minimum-age-hours 24 --apply
```

Sem `--apply`, apenas lista candidatos. A operação ignora referências de aulas e arquivos recentes, limita-se ao professor indicado e bloqueia registros de mídia durante a operação no PostgreSQL. Associação também bloqueia o registro, evitando competir com a limpeza. Banco e disco não são uma transação distribuída: falhas de disco/commit são reportadas, e restauração deve considerar ambos. Nunca rode limpeza no armazenamento de testes apontando para dados reais.

## Rodar testes

```bash
uv run python -m pytest
```

Os testes de upload e consulta usam SQLite e arquivos temporários, sem alterar o PostgreSQL ou os vídeos locais. Verificam os bytes entregues e HTTP Range; não testam decodificação ou reprodução visual no navegador.

Testes de inspeção geram vídeos reais de 12 segundos com FFmpeg em diretórios temporários. Para gerar manualmente um vídeo descartável: `uv run python scripts/generate_test_video.py /caminho/temporario/teste.mp4`.

Para inspecionar um upload anterior explicitamente, sem alterar o arquivo: `uv run --env-file .env python -m app.inspect_media UUID_DA_MIDIA`. Falhas não apagam o vídeo original. Novas colunas permanecem nulas até essa inspeção.

Testes PostgreSQL são opcionais: configure `TEST_DATABASE_URL` para um banco exclusivo cujo nome termine em `_test`. O papel não precisa de permissão de criar bancos, apenas de schemas nesse banco. Os testes criam/removem somente schemas aleatórios próprios. Nunca use o banco normal da aplicação. Sem essa variável, esses testes são marcados como ignorados.
