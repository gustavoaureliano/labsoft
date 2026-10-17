# Backend — AprovaAí

Backend individual de vídeo e aprendizagem em Python com FastAPI. Inclui mídia, aulas, progresso, Home e certificados; os outros domínios usam contratos demonstrativos explícitos.

## Requisitos

- Python 3.12 ou superior
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- PostgreSQL com usuário e banco criados
- `ffprobe` (pacote FFmpeg) para inspecionar vídeos
- FFmpeg para gerar as mídias dos testes

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
curl -H 'X-Demo-User: professor-demo' -F 'file=@/caminho/aula.mp4;type=video/mp4' http://127.0.0.1:8000/api/media
```

- Aceita extensões `.mp4` e `.webm` com os tipos declarados `video/mp4` e `video/webm`, respectivamente.
- Novos uploads são inspecionados com `ffprobe` (instale FFmpeg no servidor). São aceitos MP4/H.264 e WebM/VP8/VP9, com duração positiva. A resposta inclui `duration_seconds` e `codec`. Isso não transcodifica nem garante suporte a todos os fluxos de áudio de cada navegador.
- O limite padrão é 100 MiB. Configure `MAX_UPLOAD_BYTES` para alterá-lo.
- Os arquivos são gravados em blocos, com nomes UUID, em `backend/storage/videos/`. `STORAGE_DIR` pode indicar outro diretório absoluto ou relativo a `backend/`.
- A resposta `201` contém o identificador e os metadados públicos da mídia. Novos vídeos disponíveis foram armazenados e inspecionados. Arquivos antigos podem precisar da inspeção explícita descrita abaixo.
- Arquivo vazio ou formato inválido retorna `400`. Tamanho excedido retorna `413`.
- A validação de tamanho acontece ao copiar o arquivo recebido. O parser multipart pode armazenar temporariamente a requisição antes disso; esse limite não é uma limitação do tráfego de entrada.

As rotas aplicam autorização de proprietário/acesso. A identidade ainda é demonstrativa: ative `LEARNING_DEMO_MODE=true` e preencha `X-Demo-User` no `/docs`, ou use o cookie pelo site. Arquivos armazenados não são versionados no Git.

## Consultar e reproduzir vídeo

Use o `id` retornado pelo upload:

- `GET /api/media/{id}`: consulta os metadados, sem expor o caminho no disco.
- `GET /api/media/{id}/content`: entrega o arquivo para reprodução no navegador.

Abra `http://127.0.0.1:8000/api/media/{id}/content` no navegador, substituindo `{id}` pelo identificador. A reprodução depende de o arquivo ser um vídeo válido com codecs suportados pelo navegador.

Para solicitar apenas um trecho:

```bash
curl -i -H 'X-Demo-User: professor-demo' -H 'Range: bytes=0-15' http://127.0.0.1:8000/api/media/ID/content
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

O backend gera o identificador da aula como uma string UUID. `course_id` é validado no contrato de cursos (em memória no modo demo), sem criar uma tabela de cursos concorrente ao domínio do outro integrante. As aulas demonstrativas antigas do frontend não são importadas automaticamente.

A posição começa em 1 e é única dentro do curso (`409` em caso de conflito). Curso sem aulas retorna uma lista vazia. Associação exige aula e mídia existentes (`404`) e mídia no estado `available` (`409` caso contrário). Essa validação consulta os metadados; a rota de conteúdo continua responsável por verificar a existência do arquivo.

É possível substituir o vídeo associado ou repetir a mesma associação. Nenhum vídeo antigo é excluído. Uploads sem associação só podem ser consultados pelo proprietário. A gestão de aulas, uploads, reprodução, progresso e certificados estão integrados às telas. A criação/publicação de novos cursos e seus materiais ainda são demonstrativos de outro domínio; seus rascunhos locais continuam explicitamente separados de aulas reais. Não há limpeza automática.

## Abrir uma aula para reprodução

`GET /api/learning/lessons/{lesson_id}/playback` retorna os dados da aula, `media_id` e `content_url`, um caminho relativo da API para o vídeo. Use esse caminho no mesmo servidor da API para acessar o conteúdo.

Antes de retornar, verifica a existência da aula, a associação de vídeo, o estado `available` e o arquivo no armazenamento. Aula sem vídeo retorna `409`; aula inexistente, mídia indisponível ou arquivo ausente retorna `404`. A resposta não expõe caminhos no disco e não altera dados.

Há autorização usando os contratos de identidade e acesso; a identidade demo não é autenticação segura. A resposta inclui duração, posição salva e conclusão. A URL não é assinada nem temporária nesta etapa. A disponibilidade e a permissão são verificadas novamente na rota de conteúdo.

## Progresso

`PATCH /api/learning/lessons/{id}/progress` recebe `{"media_id": "UUID-atual", "position_seconds": 4.5}`. A identidade vem da dependência; prévias do professor não gravam progresso. Posição negativa/não finita é rejeitada; posição além da duração retorna `400`, vídeo alterado ou sem duração verificada retorna `409`.

A aula é concluída ao informar pelo menos 90% da duração. Isso não comprova que todos os segundos foram assistidos. Recuar o vídeo atualiza a posição sem desfazer a conclusão. Trocar o vídeo invalida efetivamente a posição/conclusão anterior. Os saves concorrentes são serializados por curso: a última gravação confirmada vence. Excluir aula remove seu progresso; o vídeo é preservado. A limpeza também preserva mídias referenciadas por progresso.

## Home e cursos do aluno

`GET /api/learning/courses` lista cursos acessíveis (ou cursos próprios para o professor). `GET /api/learning/courses/{id}` inclui aulas, seção padrão, estado de reprodução, thumbnails, progresso e aula para continuar. `GET /api/learning/dashboard` retorna os cursos, curso atual e recomendações/avisos dos contratos externos (a recomendação demo é uma amostra fixa e os avisos são vazios). Falhas nesses contratos opcionais não impedem a Home. Cursos sem aulas não estão concluídos. Cursos inacessíveis não são apresentados como reproduzíveis.

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

## Certificados

- `POST /api/learning/courses/{id}/certificate`: emite ou retorna o certificado existente, exigindo acesso atual e todas as aulas concluídas. Curso vazio é inelegível.
- `GET /api/learning/certificates` e `GET /api/learning/certificates/{id}`: consulta privada do proprietário.
- `GET /api/learning/certificates/{id}/download`: PDF gerado do snapshot persistido.
- `GET /api/learning/certificates/verify/{code}`: verificação pública mínima, sem identificador privado do usuário.

O certificado guarda nome, título, quantidade de aulas e carga horária da emissão. Mudanças posteriores no curso, progresso ou expiração do acesso não apagam esse documento do proprietário. Emissão é única por aluno/curso e serializada no PostgreSQL. Não é assinatura digital qualificada. O PDF identifica a emissão local de desenvolvimento.

Falha na notificação não desfaz emissão; nova solicitação tenta novamente a entrega sem criar outro certificado. O contrato de notificação deve usar o identificador do certificado como chave idempotente. O adaptador demo não envia mensagens reais.

## Integração do player e testes

O frontend encaminha `/api` para `BACKEND_URL` (padrão `http://127.0.0.1:8000`). Ative `LEARNING_DEMO_MODE=true` na API e entre novamente no site para definir também o cookie de identidade demo. O player nativo reproduz vídeos reais e salva a posição a cada cinco segundos, ao pausar e ao terminar. Falha de salvamento é informada; não se depende exclusivamente do fechamento da página.

O Next.js usa `proxyClientMaxBodySize: "101mb"` para permitir o limite de 100 MiB mais overhead multipart. O proxy pode bufferizar uploads até esse limite; a entrega de conteúdo usa a resposta parcial/stream do servidor. Se aumentar `MAX_UPLOAD_BYTES`, ajuste também o limite do frontend. Essa configuração local não substitui controles de ingresso de uma futura implantação.

Biblioteca, comentários, dúvidas e moderação continuam no navegador, mas recebem os IDs corretos de curso/aula. Referências antigas não são apagadas nem remapeadas silenciosamente. Itens sem resolução/acesso são informados como indisponíveis. A biblioteca é um adaptador local, não uma implementação do backend de outro integrante.

Para Selenium com backend isolado, configure `TEST_DATABASE_URL` (banco `_test`) e `STORAGE_DIR` apontando para um diretório exclusivo de testes, execute `uv run --env-file .env python -m scripts.prepare_e2e` e inicie uma API separada usando esse banco e armazenamento. Encaminhe o frontend para essa API e rode `E2E_BACKEND=true node --test tests/e2e/backend-playback.test.ts` dentro de `frontend/`. Nunca prepare esses dados sobre o banco/armazenamento normal. Sem `E2E_BACKEND=true`, esse teste é ignorado explicitamente.

Exemplo completo, após criar `aprovaai_learning_test` com o mesmo proprietário do banco local:

```bash
# Terminal do backend. Substitua a senha local, sem versionar este comando.
export TEST_DATABASE_URL='postgresql+psycopg://aprovaai:SENHA@127.0.0.1:5432/aprovaai_learning_test'
export STORAGE_DIR='/tmp/aprovaai-learning-test'
uv run --env-file .env python -m scripts.prepare_e2e
DATABASE_URL="$TEST_DATABASE_URL" LEARNING_DEMO_MODE=true uv run uvicorn app.main:app --port 18000
```

```bash
# Terminal do frontend
BACKEND_URL=http://127.0.0.1:18000 npm run dev
```

```bash
# Outro terminal do frontend
E2E_BACKEND=true \
E2E_VIDEO_PATH=/tmp/aprovaai-learning-test/videos/e2e-fixture.mp4 \
E2E_THUMBNAIL_PATH=/tmp/aprovaai-learning-test/thumbnails/e2e-fixture.png \
npm run test:e2e
```

`prepare_e2e` é exclusivo do banco de teste: cria mídias conhecidas e associa apenas as aulas de fixture. Os cursos recebem mídias distintas para testar permissões sem acesso cruzado por uma mídia compartilhada. Para um estado completamente novo, pare os servidores de teste e recrie somente esse banco dedicado e o diretório de testes, nunca `aprovaai` ou o armazenamento normal. Não existe reset automático dos dados pessoais de desenvolvimento.

Para a suíte completa, defina também `E2E_VIDEO_PATH` para o MP4 gerado e `E2E_THUMBNAIL_PATH` para o PNG gerado pelo script, e execute `E2E_BACKEND=true npm run test:e2e` no frontend. Os testes de aprendizagem existentes também precisam do backend e das aulas de exemplo. Chromium é headless por padrão; `E2E_HEADLESS=false` abre janela somente quando solicitado.

## Demonstração e integração futura

1. Aplique migrações e ative as integrações demo.
2. Use `python -m app.seed` para criar aulas sem sobrescrever posições existentes.
3. No site, entre como professor e abra um curso conhecido, como Física Quântica. Edite/crie aula, envie vídeo/thumbnail e visualize a prévia.
4. Troque para aluno e abra Meus Cursos. Assista, avance, pause e recarregue. Confirme a posição salva e o progresso na Home/curso.
5. Conclua as aulas e emita o certificado. Abra PDF e verificação.

Para a mídia antiga enviada manualmente, execute os comandos explícitos de atribuição de proprietário e inspeção apenas se desejar completar seus metadados; nada é atribuído ou reinspecionado automaticamente.

Para integrar os outros integrantes, substitua `get_integrations` e `get_current_user`: identidade/sessão real, dados/posse/publicação do curso, direitos de matrícula, recomendações/avisos e entrega idempotente de notificação. A biblioteca local será substituída pelo contrato de coleções ordenadas. Não existe autenticação real, pagamento, catálogo persistido ou envio real de mensagem nesta entrega individual.

Backup/restauração deve preservar conjuntamente PostgreSQL e `STORAGE_DIR`. Migrações alteram estrutura, não movem arquivos nem geram backup. Certificados são gerados de snapshots no banco. Banco e arquivos não têm atomicidade distribuída: após uma queda de processo pode ser necessária reconciliação manual. Não exponha esta configuração demo à internet.

## Validação desta entrega

- 71 verificações de backend, incluindo PostgreSQL isolado, migrações, concorrência, permissões e conteúdo do PDF.
- 38 testes de navegador/transporte na suíte completa em Chromium headless, usando a API e mídia de teste reais.
- Lint, TypeScript e build de produção do frontend aprovados; permanece o aviso pré-existente de `<img>` no avatar do perfil.
- Foram conferidas visualmente Home, videoaula e certificados. Nenhum arquivo de vídeo, credencial ou banco de testes é versionado.

## Comandos de teste

```bash
uv run python -m pytest
```

Os testes de upload e consulta usam SQLite e arquivos temporários, sem alterar o PostgreSQL ou os vídeos locais. Verificam os bytes entregues e HTTP Range; não testam decodificação ou reprodução visual no navegador.

Testes de inspeção geram vídeos reais de 12 segundos com FFmpeg em diretórios temporários. Para gerar manualmente um vídeo descartável: `uv run python scripts/generate_test_video.py /caminho/temporario/teste.mp4`.

Para inspecionar um upload anterior explicitamente, sem alterar o arquivo: `uv run --env-file .env python -m app.inspect_media UUID_DA_MIDIA`. Falhas não apagam o vídeo original. Novas colunas permanecem nulas até essa inspeção.

Testes PostgreSQL são opcionais: configure `TEST_DATABASE_URL` para um banco exclusivo cujo nome termine em `_test`. O papel não precisa de permissão de criar bancos, apenas de schemas nesse banco. Os testes criam/removem somente schemas aleatórios próprios. Nunca use o banco normal da aplicação. Sem essa variável, esses testes são marcados como ignorados.
