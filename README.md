# AprovaAí

Protótipo inicial da interface da AprovaAí.

## Estrutura do repositório

- `frontend/`: aplicação Next.js, arquivos públicos e testes Selenium.
- `backend/services/learning/`: API de vídeo e aprendizagem em Python com FastAPI. Veja as [instruções de execução](backend/services/learning/README.md).

Na branch de integração, cada backend terá diretório de trabalho e ambiente próprios. Neste primeiro incremento somente aprendizagem foi incorporada. Execute seus comandos dentro de `backend/services/learning/`; não copie banco, `.env` ou arquivos de mídia de outro ambiente automaticamente.

## Requisitos

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

Abra `/` sem perfil demo para ver a landing, com cursos de exemplo e links para entrar ou criar conta. Depois de entrar como aluno, `/` mostra a Home de estudos. Professor e administrador são direcionados às suas áreas em `/professor/cursos` e `/admin`. O menu da conta permite trocar de perfil ou sair. Dúvidas do aluno ficam em `/duvidas`; dúvidas recebidas pelo professor, em `/professor/duvidas`.

O papel escolhido fica em um cookie de demonstração, usado para mostrar o menu e a área correspondentes. Esse cookie pode ser alterado pelo navegador e **não é uma autenticação segura**. Os demais dados demonstrativos continuam no armazenamento local do navegador.

Para acompanhar o navegador, use `npm run test:e2e:visual`. Os testes serão executados um de cada vez, com pausas de 1,5 segundo. Use `E2E_SLOW_MS` para definir outro intervalo em milissegundos.

Use `BASE_URL` se a aplicação estiver em outra porta. Use `CHROME_BINARY` se o Chromium estiver em outro caminho.

O Chromium executa sem janela por padrão, inclusive nos modos sequencial e com pausas. Para uma demonstração visível, use `E2E_HEADLESS=false npm run test:e2e:visual`.

Os testes percorrem descoberta e detalhes de cursos, contratação demonstrativa, navegação entre aulas e playlists, estudo da videoaula, organização de aulas, dúvidas entre aluno e professor, perfil, avisos, certificados, criação de cursos, seleção de arquivos, métricas e moderação. Também verificam os fluxos demonstrativos de entrada, solicitação docente e denúncia.

Vídeo e aprendizagem têm backend real: aulas, upload/inspeção de vídeo e thumbnail, reprodução, progresso e certificados. Identidade, catálogo e matrícula ainda usam adaptadores demonstrativos nesta etapa da branch. Biblioteca/interações e outras telas ainda dependem de integrações posteriores; não há autenticação real ou pagamento integrado neste incremento.
