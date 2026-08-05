# SPEC-FEAT-001 — Base do projeto e identidade visual

| | |
| --- | --- |
| **App** | frontend |
| **Épico** | Base e dashboard |
| **Atende** | Critérios: organização do código, qualidade da implementação |
| **Depende de** | `backend/SPEC-FEAT-013` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

A interface será operada por técnicos de manutenção em chão de fábrica e apresentada em uma
entrevista. Precisa ser densa em informação, legível à distância e sóbria — não um template
genérico de dashboard.

## Escopo

- Vite + React + TypeScript com `strict` ligado.
- Cliente de API tipado, com os tipos derivados do contrato da API (SPEC-FEAT-013 do backend).
- TanStack Query para busca, cache e estados de carregamento/erro.
- Layout de aplicação: barra lateral de navegação, cabeçalho com estado do sistema
  (banco, índice, provider) e área de conteúdo.
- Tokens de design: paleta industrial escura, tipografia com números tabulares, escala de
  espaçamento consistente. Cores semânticas de severidade (normal / atenção / falha) que
  não dependem só de matiz — daltonismo é comum na indústria.
- Estados vazios, de carregamento e de erro tratados como parte do design, não como sobra.
- **Proxy no container**: o navegador chama `/api/*` no próprio host do frontend; o nginx
  encaminha para a API injetando o cabeçalho `X-Internal-Key` lido do ambiente. A chave de
  comunicação interna nunca é embutida no bundle nem exposta ao navegador.
- `Dockerfile` multi-estágio (build Vite → nginx) e `docker-compose.yml` próprio, na rede
  externa compartilhada com o backend.

## Fora de escopo

- Tema claro/escuro alternável — a operação é em ambiente de baixa luminosidade; um tema só,
  bem resolvido, vale mais que dois medianos.
- Biblioteca de componentes pesada; o conjunto de componentes é pequeno e específico.

## Decisões técnicas

- **Vite + React em vez de Next.js.** Não há SEO nem SSR em jogo: é uma aplicação interna
  atrás da rede da fábrica. Next.js adicionaria superfície sem benefício.
- **TanStack Query em vez de estado global manual.** Os dados são majoritariamente de
  servidor; cache, revalidação e estados de carregamento saem de graça.
- **Severidade sinalizada por cor + forma + rótulo.** Só cor é inacessível e, em tela de
  fábrica com brilho ruim, ilegível.
- **Chave interna no proxy, não no cliente.** Qualquer segredo que chegue ao bundle é
  público — basta abrir o DevTools. O nginx do container injeta o cabeçalho; o navegador
  nunca vê a chave.
- **Compose próprio, separado do backend.** A interface é reconstruída e publicada sem
  derrubar banco nem API.

## Contrato

```
src/
  api/          cliente tipado e hooks de query
  components/   componentes reutilizáveis
  features/     dashboard, analise, chat, documentos
  lib/          formatação, tokens de design
  routes/       definição de rotas
```
