# AprovaAí

Protótipo inicial da interface da AprovaAí.

## Estrutura do repositório

- `frontend/`: aplicação Next.js, arquivos públicos e testes Selenium.
- `backend/services/learning/`: API de vídeo e aprendizagem em Python com FastAPI. Veja as [instruções de execução](backend/services/learning/README.md).
- `backend/services/identity/`: implementação de identidade de Renan, preservada para integração.

Cada backend usa seu próprio diretório de trabalho e ambiente. Não copie banco, `.env` ou mídia de outro ambiente automaticamente.

## Requisitos

### PostgreSQL de integração

Em um banco novo e exclusivo de integração, um administrador executa `backend/infrastructure/learning.sql` com `psql`, fornecendo `LEARNING_MIGRATION_PASSWORD` e `LEARNING_RUNTIME_PASSWORD` pelo ambiente. Esse provisionamento inicial cria schema e permissões; não roda no startup.

Na pasta do serviço, aplique `uv run --locked alembic upgrade head` com `DATABASE_URL` da role `aa_learning_migration`. Inicie a aplicação com a role `aa_learning_runtime`. As tabelas continuam sendo gerenciadas pelo Alembic; credenciais ficam fora do Git.

Para identidade, execute `backend/infrastructure/identity.sql` com `IDENTITY_MIGRATION_PASSWORD` e `IDENTITY_RUNTIME_PASSWORD`; use as roles correspondentes `aa_identity_migration` e `aa_identity_runtime` na pasta `backend/services/identity/`.

Para autenticação HTTP em aprendizagem, configure `IDENTITY_URL` e `FRONTEND_ORIGIN`; em identidade, use a mesma origem em `AA_FRONTEND_ORIGIN`. Login/refresh emitem o access cookie HttpOnly. Bearer explícito prevalece sobre cookie. Configurar identidade real não configura catálogo ou matrícula automaticamente.

### Frontend

- Node.js 24
- npm

## Comandos

Execute os comandos abaixo dentro de `frontend/`:

```bash
cd frontend
```

- `npm install`: instala as dependências.
- `npm run dev`: inicia o ambiente de desenvolvimento.
- `npm run lint`: verifica o código.
- `npm run typecheck`: verifica os tipos TypeScript.
- `npm run build`: gera a versão de produção.
- `npm run test:e2e`: executa os testes Selenium em paralelo no Chromium, com a aplicação já iniciada em `http://localhost:3000`.
- `npm run test:e2e:sequential`: executa os testes um de cada vez, sem pausas.
- `npm run test:e2e:visual`: executa os testes um de cada vez, com pausas para acompanhar o navegador.

Para executar os testes, inicie a aplicação em um terminal, dentro de `frontend/`:

```bash
npm run dev
```

Em outro terminal, também dentro de `frontend/`, execute os testes:

```bash
npm run test:e2e
```

Para usar o frontend com a API, copie `frontend/.env.example` para
`frontend/.env.local` e mantenha o backend disponível em `http://localhost:8000`.
Com `NEXT_PUBLIC_API_URL` configurada, login, cadastro, confirmação de e-mail e
recuperação de senha usam a API; `/avisos` lista as notificações da conta
autenticada. O backend precisa ter um provedor de e-mail configurado e o worker
da outbox em execução para enviar os links de confirmação e recuperação. Sem
essa variável, os fluxos demonstrativos locais continuam disponíveis. Configure
`AA_FRONTEND_ORIGIN` no backend quando a origem do frontend não for
`http://localhost:3000`.

Abra `/` sem perfil demo para ver a landing, com cursos de exemplo e links para entrar ou criar conta. Depois de entrar como aluno, `/` mostra a Home de estudos. Professor e administrador são direcionados às suas áreas em `/professor/cursos` e `/admin`. O menu da conta permite trocar de perfil ou sair. Dúvidas do aluno ficam em `/duvidas`; dúvidas recebidas pelo professor, em `/professor/duvidas`.

Sem a API, o papel escolhido fica em um cookie de demonstração, usado para mostrar o menu e a área correspondentes. Esse cookie pode ser alterado pelo navegador e **não é uma autenticação segura**. Com a API configurada, o login usa o usuário e o papel retornados pelo banco; ao abrir a aplicação, a sessão é restaurada e validada por `/api/v1/auth/me`. O cookie de papel continua servindo apenas à navegação da interface. A autorização efetiva de operações e dados privados é verificada pela API a partir da sessão e do papel atual no banco. Os demais dados demonstrativos continuam no armazenamento local do navegador.

Para acompanhar o navegador, use `npm run test:e2e:visual`. Os testes serão executados um de cada vez, com pausas de 1,5 segundo. Use `E2E_SLOW_MS` para definir outro intervalo em milissegundos.

Use `BASE_URL` se a aplicação estiver em outra porta. Use `CHROME_BINARY` se o Chromium estiver em outro caminho.

O Chromium executa sem janela por padrão, inclusive nos modos sequencial e com pausas. Para uma demonstração visível, use `E2E_HEADLESS=false npm run test:e2e:visual`.

Os testes percorrem descoberta e detalhes de cursos, contratação demonstrativa, navegação entre aulas e playlists, estudo da videoaula, organização de aulas, dúvidas entre aluno e professor, perfil, avisos, certificados, criação de cursos, seleção de arquivos, métricas e moderação. Também verificam os fluxos demonstrativos de entrada, solicitação docente e denúncia.

Vídeo e aprendizagem têm backend real: aulas, upload/inspeção de vídeo e thumbnail, reprodução, progresso e certificados. A autenticação pode consultar identidade por HTTP; catálogo, matrícula, biblioteca/interações e pagamento ainda dependem das próximas integrações. O cliente de sessão do frontend também precisa das adaptações finais para esse fluxo.
