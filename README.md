# Logos Academy

Protótipo inicial da interface da Logos Academy.

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

Para executar os testes, inicie a aplicação com `npm run dev` em um terminal e rode `npm run test:e2e` em outro. Use `BASE_URL` se a aplicação estiver em outra porta e `CHROME_BINARY` se o Chromium estiver em outro caminho.

Os testes cobrem cinco jornadas: explorar cursos, filtrar e buscar materiais, recuperar-se de uma busca sem resultados, continuar uma aula e salvar o apelido no perfil. O botão da videoaula apenas alterna entre os ícones de reproduzir e pausar nesta demonstração; ainda não há um vídeo.
