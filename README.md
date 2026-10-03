# AprovaAí

Protótipo inicial da interface da AprovaAí.

## Requisitos

- Node.js 24
- npm

## Comandos

- `npm install`: instala as dependências.
- `npm run dev`: inicia o ambiente de desenvolvimento.
- `npm run lint`: verifica o código.
- `npm run typecheck`: verifica os tipos TypeScript.
- `npm run build`: gera a versão de produção.
- `npm run test:e2e`: executa até 24 testes Selenium ao mesmo tempo no Chromium, com a aplicação já iniciada em `http://localhost:3000`.
- `npm run test:e2e:sequential`: executa os testes um de cada vez, sem pausas.
- `npm run test:e2e:visual`: executa os testes um de cada vez, com pausas para acompanhar o navegador.

Para executar os testes, inicie a aplicação em um terminal:

```bash
npm run dev
```

Em outro terminal, execute os testes:

```bash
npm run test:e2e
```

Abra `/` sem perfil demo para ver a landing, com cursos de exemplo e links para entrar ou criar conta. Depois de entrar como aluno, `/` mostra a Home de estudos. Professor e administrador são direcionados às suas áreas em `/professor/cursos` e `/admin`. O menu da conta permite trocar de perfil ou sair. Dúvidas do aluno ficam em `/duvidas`; dúvidas recebidas pelo professor, em `/professor/duvidas`.

O papel escolhido fica em um cookie de demonstração, usado para mostrar o menu e a área correspondentes. Esse cookie pode ser alterado pelo navegador e **não é uma autenticação segura**. Os demais dados demonstrativos continuam no armazenamento local do navegador.

Para acompanhar o navegador, use `npm run test:e2e:visual`. Os testes serão executados um de cada vez, com pausas de 1,5 segundo. Use `E2E_SLOW_MS` para definir outro intervalo em milissegundos.

Use `BASE_URL` se a aplicação estiver em outra porta. Use `CHROME_BINARY` se o Chromium estiver em outro caminho.

Os testes percorrem descoberta de cursos e materiais, estudo da videoaula, organização de aulas, dúvidas entre aluno e professor, perfil, avisos, certificados ilustrativos, gestão de cursos, métricas e moderação. Também verificam os fluxos demonstrativos de entrada, solicitação docente e denúncia.

Este é um protótipo de interface. Conta, dúvidas, anotações, playlists e decisões de moderação são simuladas no navegador. Não há autenticação, envio de e-mail, pagamento, vídeo real ou backend. Detalhes do curso, editor e planos pertencem ao módulo do João e ainda precisam ser integrados.
