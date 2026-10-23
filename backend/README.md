# Backend — AprovaAí

API em FastAPI. O fluxo de identidade segue a especificação do microsserviço:
JWT Ed25519 de curta duração, refresh token opaco em cookie HttpOnly,
confirmação de e-mail, recuperação de senha, RBAC, rate limiting e auditoria.

## Requisitos

- Python 3.12 ou superior
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- PostgreSQL com usuário e banco criados

## Configuração local

Dentro de `backend/`, instale as dependências e copie o exemplo de ambiente:

```bash
uv sync --locked
cp .env.example .env
```

Defina `DATABASE_URL`, as chaves e o serviço de envio de e-mail em `.env`.
Gere um par Ed25519 PEM e uma chave Fernet localmente com:

```bash
uv run python - <<'PY'
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

private = Ed25519PrivateKey.generate()
private_pem = private.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
)
public_pem = private.public_key().public_bytes(
    serialization.Encoding.PEM,
    serialization.PublicFormat.SubjectPublicKeyInfo,
)
print("AA_JWT_PRIVATE_KEY_B64=" + base64.urlsafe_b64encode(private_pem).decode())
print("AA_JWT_PUBLIC_KEY_B64=" + base64.urlsafe_b64encode(public_pem).decode())
print("AA_EMAIL_ENCRYPTION_KEY=" + Fernet.generate_key().decode())
PY
```

Copie as três linhas geradas para `.env`. Não compartilhe nem versione esse
arquivo. As configurações de tokens, emissor, audiência, cookies e origem do
frontend estão documentadas em `.env.example`. Em produção, use HTTPS e
configure `AA_COOKIE_SECURE=true`.

Configure **um** provedor de e-mail:

- Brevo: `BREVO_API_KEY` e `BREVO_SENDER_EMAIL` (opcionalmente
  `BREVO_SENDER_NAME`); ou
- SMTP: `AA_SMTP_HOST`, `AA_SMTP_PORT`, `AA_SMTP_USERNAME`,
  `AA_SMTP_PASSWORD` e `AA_SMTP_FROM` (opcionalmente
  `AA_SMTP_STARTTLS`).

Sem um provedor configurado, cadastro e recuperação de senha não poderão
enviar mensagens. Ajuste `AA_PUBLIC_APP_URL` para a origem do frontend e
`AA_PASSWORD_RESET_URL` para `http://localhost:3000/recuperar-acesso` (ou para
a página `/recuperar-acesso` na origem usada pela aplicação).
Configure também `AA_FRONTEND_ORIGIN` com a origem exata permitida pelo CORS.

## Banco de dados e primeiro administrador

Com `.env` configurado, aplique as migrações:

```bash
uv run --env-file .env alembic upgrade head
uv run --env-file .env alembic current
```

Crie o primeiro administrador (a senha é solicitada sem eco e não vai para o
histórico do shell):

```bash
uv run --env-file .env python -m app.identity_access.bootstrap_admin admin@exemplo.com
```

O comando só cria o administrador inicial se ainda não houver um. Para
atribuir papéis ou suspender contas posteriormente, use os endpoints
administrativos de identidade.

## Executar

Inicie a API dentro de `backend/`:

```bash
uv run --env-file .env uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Health check: http://127.0.0.1:8000/api/health
- Login administrativo do Swagger: http://127.0.0.1:8000/admin/login
- Swagger: http://127.0.0.1:8000/docs

O OpenAPI e o Swagger estão disponíveis somente para uma sessão administrativa
ativa. Após entrar em `/admin/login`, abra `/docs`. Para autorizar chamadas,
faça login pelo endpoint `POST /api/v1/auth/login` e informe o access token no
botão **Authorize** usando o esquema Bearer. O endpoint de login da API retorna
JWT; o refresh token é mantido em cookie HttpOnly. Não há fluxo OAuth2 password
grant.

O access token expira em 15 minutos por padrão e o refresh token opaco é
rotacionado, com validade padrão de 7 dias. Uma reutilização de refresh token
revoga a sessão. Alterações de papel/status e redefinição de senha também
invalidam as sessões conforme a política de identidade.

## Worker de e-mail

O worker entrega mensagens persistidas na outbox e tenta novamente em caso de
falha. Execute-o em um processo separado, mantendo-o ativo junto à API:

```bash
uv run --env-file .env python -m app.identity_access.email_worker
```

Confirmação de e-mail expira em 24 horas por padrão; links de redefinição de
senha expiram em 20 minutos. Tokens da outbox são cifrados com
`AA_EMAIL_ENCRYPTION_KEY`.

## Migrações

O Alembic usa a mesma `DATABASE_URL` da aplicação. Para conferir a revisão
aplicada:

```bash
uv run --env-file .env alembic current
```

Ao alterar modelos, gere uma migração e revise-a antes de aplicar:

```bash
uv run --env-file .env alembic revision --autogenerate -m "Describe schema change"
uv run --env-file .env alembic upgrade head
```

Os modelos de identidade e mídia compartilham a metadata carregada pelo Alembic.
As revisões ficam em `migrations/versions/`.
