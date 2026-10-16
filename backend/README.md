# Backend — AprovaAí

Estrutura inicial da API em Python com FastAPI.

## Requisitos

- Python 3.12 ou superior
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Executar

Dentro de `backend/`, instale as dependências:

```bash
uv sync --locked
```

Inicie o servidor de desenvolvimento:

```bash
uv run uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Verificação de funcionamento: http://127.0.0.1:8000/api/health
