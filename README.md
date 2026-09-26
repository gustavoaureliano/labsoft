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
- `npm run test:e2e`: executa os testes Selenium em Chromium, com a aplicação já iniciada em `http://localhost:3000`.
- `npm run test:e2e:visual`: executa os testes um de cada vez, com pausas para acompanhar o navegador.

Para executar os testes, inicie a aplicação em um terminal:

```bash
npm run dev
```

Em outro terminal, execute os testes:

```bash
npm run test:e2e
```

Para acompanhar o navegador, use `npm run test:e2e:visual`. Os testes serão executados um de cada vez, com pausas de 1,5 segundo. Use `E2E_SLOW_MS` para definir outro intervalo em milissegundos.

Use `BASE_URL` se a aplicação estiver em outra porta. Use `CHROME_BINARY` se o Chromium estiver em outro caminho.

Os testes cobrem estas jornadas:

- Explorar e filtrar cursos.
- Buscar materiais complementares.
- Recuperar-se de uma busca sem resultados.
- Continuar uma aula.
- Salvar o apelido no perfil.
- Alternar o período no painel administrativo.
- Aprovar um professor na moderação.
