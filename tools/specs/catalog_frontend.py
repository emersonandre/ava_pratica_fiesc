"""Catálogo de features do frontend.

Fonte única das specs. O gerador (`tools/specs/gen.py`) materializa cada item em
`frontend/docs/SPEC-FEAT-XXX/{spec.md,acceptance.md,tasks.md}`.
"""

APP = "frontend"
DOCS_DIR = "frontend/docs"
TITLE = "Frontend — Manutenção Prescritiva"
STACK = "React 19 · TypeScript · Vite · TanStack Query · Recharts"

EPICS = {
    "base": "Base e dashboard",
    "analise": "Análise e chat",
}

FEATURES = [
    # ------------------------------------------------------------------ 001
    dict(
        id="SPEC-FEAT-001",
        title="Base do projeto e identidade visual",
        epic="base",
        atende="Critérios: organização do código, qualidade da implementação",
        depends=["backend/SPEC-FEAT-013"],
        contexto="""
A interface será operada por técnicos de manutenção em chão de fábrica e apresentada em uma
entrevista. Precisa ser densa em informação, legível à distância e sóbria — não um template
genérico de dashboard.
""",
        escopo="""
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
""",
        fora_escopo="""
- Tema claro/escuro alternável — a operação é em ambiente de baixa luminosidade; um tema só,
  bem resolvido, vale mais que dois medianos.
- Biblioteca de componentes pesada; o conjunto de componentes é pequeno e específico.
""",
        decisoes="""
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
""",
        contrato="""
```
src/
  api/          cliente tipado e hooks de query
  components/   componentes reutilizáveis
  features/     dashboard, analise, chat, documentos
  lib/          formatação, tokens de design
  routes/       definição de rotas
```
""",
        acceptance=[
            ("Build limpo",
             "`npm run build` termina sem erro e sem aviso de TypeScript."),
            ("Contrato de API tipado ponta a ponta",
             "Nenhum `any` no cliente de API; alterar um campo do backend quebra a compilação no frontend."),
            ("Estado do sistema visível",
             "O cabeçalho mostra o resultado de `/api/health`; com a API fora, exibe estado degradado em vez de tela quebrada."),
            ("Erro de rede não quebra a tela",
             "Com a API indisponível, cada painel mostra estado de erro com opção de nova tentativa."),
            ("Legibilidade verificada",
             "Contraste do texto principal atende AA; números usam fonte tabular e não dançam ao atualizar."),
            ("Chave interna não vaza para o navegador",
             "Buscar por `INTERNAL_API_KEY` no bundle gerado e no painel de rede do navegador não encontra o valor."),
            ("Sobe e desce sem afetar o backend",
             "`docker compose -f frontend/docker-compose.yml down && up -d` não reinicia os containers de banco e API."),
        ],
        tasks=[
            "Criar o projeto com Vite + React + TypeScript e ligar o modo `strict`",
            "Definir tokens de design (cores, tipografia, espaçamento) em CSS custom properties",
            "Implementar o layout de aplicação (barra lateral, cabeçalho, conteúdo)",
            "Implementar o cliente de API tipado e configurar o TanStack Query",
            "Implementar os componentes de estado vazio, carregamento e erro",
            "Implementar o indicador de saúde do sistema no cabeçalho",
            "Escrever o `Dockerfile` multi-estágio e a configuração do nginx com injeção de `X-Internal-Key`",
            "Configurar ESLint e Prettier e rodar o build de produção",
        ],
    ),
    # ------------------------------------------------------------------ 002
    dict(
        id="SPEC-FEAT-002",
        title="Dashboard de indicadores",
        epic="base",
        atende="§3 — apresentação visual dos resultados; DIF — Dashboards",
        depends=["SPEC-FEAT-001"],
        contexto="""
Primeira tela da apresentação. Precisa responder em segundos: qual a situação do parque,
quais falhas dominam, e o que a base de conhecimento cobre.
""",
        escopo="""
- Cartões de indicador: total de eventos monitorados, eventos classificados como problema,
  número de famílias de falha distintas, cobertura documental (famílias cobertas / total),
  período coberto pelo histórico.
- Ranking das famílias de falha por número de ocorrências, com o status de cobertura
  documental em cada linha.
- Destaque para as famílias **sem documento** — é a lacuna acionável, e o gancho para a
  narrativa da entrevista.
- Atalho de cada família para a análise detalhada.
""",
        fora_escopo="""
- Filtro por equipamento/linha — o dataset é de uma única máquina rotativa.
- Alertas em tempo real.
""",
        decisoes="""
- **Cobertura documental como indicador de primeira linha.** É o diferencial conceitual da
  solução: o sistema sabe o que não sabe.
- **Números vindos de uma única chamada (`/api/stats/overview`).** Evita cascata de
  requisições e mantém os cartões consistentes entre si.
""",
        contrato="""
```ts
GET /api/stats/overview -> {
  totalEvents, problemEvents, familyCount,
  coveredFamilies, uncoveredFamilies,
  periodStart, periodEnd,
  ranking: { family, count, covered, documents }[]
}
```
""",
        acceptance=[
            ("Indicadores conferem com o banco",
             "Os valores dos cartões batem com consulta SQL direta sobre `sensor_events`."),
            ("Famílias sem documento saltam à vista",
             "Elas aparecem visualmente destacadas no ranking e contabilizadas em um cartão próprio."),
            ("Estados não contam como problema",
             "`normal`, `baseline`, `motor_desligado` e afins não entram no total de eventos-problema."),
            ("Carregamento não pisca",
             "Enquanto carrega, os cartões mostram esqueleto de mesma dimensão — sem salto de layout."),
            ("Navegação encadeia",
             "Clicar em uma família leva à análise já filtrada por ela."),
        ],
        tasks=[
            "Implementar o hook de query de `/api/stats/overview`",
            "Implementar o componente de cartão de indicador com esqueleto de carregamento",
            "Implementar a tabela de ranking com coluna de status de cobertura",
            "Implementar o destaque visual e o cartão de famílias descobertas",
            "Ligar a navegação família → tela de análise",
            "Conferir os números contra consulta SQL e registrar a verificação",
        ],
    ),
    # ------------------------------------------------------------------ 003
    dict(
        id="SPEC-FEAT-003",
        title="Gráficos analíticos",
        epic="base",
        atende="§3 — distribuição ao longo do tempo, frequência de ocorrência",
        depends=["SPEC-FEAT-002"],
        contexto="""
O enunciado pede nominalmente distribuição temporal e frequência de ocorrência. São os
gráficos que sustentam a conversa sobre padrão de falha na entrevista.
""",
        escopo="""
- Linha do tempo de ocorrências por dia, empilhada por família, com seleção de período.
- Distribuição de uma métrica de vibração por família (dispersão ou caixa) — evidencia
  visualmente por que as famílias são separáveis no espaço de features.
- Frequência de ocorrência e intervalo médio entre eventos por família.
- Marcação visual do corte entre histórico (≤ 09/jun) e holdout (10–16/jun) — deixa o rigor
  metodológico visível em vez de precisar ser explicado.
""",
        fora_escopo="""
- Gráficos 3D ou animações — atrapalham a leitura de dado técnico.
- Exportação de imagem dos gráficos.
""",
        decisoes="""
- **Recharts.** Suficiente para os tipos usados, componível em React, sem o peso e a curva do D3.
- **Eixos sempre rotulados com unidade.** Público técnico: `mm/s` sem rótulo é ruído.
- **Paleta de famílias estável entre gráficos e telas.** A mesma família mantém a mesma cor
  em toda a aplicação; cor inconsistente entre painéis confunde mais do que ajuda.
""",
        contrato="""
```ts
GET /api/stats/timeline?family=&from=&to= -> { date, family, count }[]
```
""",
        acceptance=[
            ("Distribuição temporal correta",
             "Os picos da linha do tempo coincidem com os períodos de ensaio conhecidos de cada família."),
            ("Corte de holdout visível",
             "A separação entre 09/jun e 10/jun aparece marcada no gráfico, com legenda explicando."),
            ("Cores consistentes",
             "Uma família tem a mesma cor no dashboard, nos gráficos e no painel de similares."),
            ("Legível em volume",
             "Com todas as famílias ativas, o gráfico permanece legível; famílias pouco frequentes são agrupadas ou filtráveis."),
            ("Eixos com unidade",
             "Todo eixo de métrica física traz a unidade no rótulo."),
            ("Responsivo",
             "Os gráficos se ajustam em telas a partir de 1280 px sem cortar rótulo."),
        ],
        tasks=[
            "Definir a paleta de famílias e centralizá-la em `lib/palette.ts`",
            "Implementar o gráfico de linha do tempo empilhado com seletor de período",
            "Implementar o gráfico de distribuição de métrica por família",
            "Implementar o painel de frequência e intervalo médio",
            "Implementar a marcação visual do corte de holdout",
            "Ajustar responsividade e conferir legibilidade com todas as famílias ativas",
        ],
    ),
    # ------------------------------------------------------------------ 004
    dict(
        id="SPEC-FEAT-004",
        title="Gestão de documentos",
        epic="base",
        atende="§3 — registrar novo documento; DIF — Dashboards",
        depends=["SPEC-FEAT-001", "backend/SPEC-FEAT-014"],
        contexto="""
Contraparte visual do ciclo de cobertura documental: mostrar o que a base conhece, o que
falta, e permitir preencher a lacuna.
""",
        escopo="""
- Lista de documentos indexados: título, família vinculada, páginas, número de chunks,
  método de extração (texto ou OCR) e estado da indexação.
- Sinalização dos documentos processados por OCR — informação relevante de confiabilidade.
- Upload de novo documento: arquivo, família alvo e título, com progresso e resultado.
- Painel de lacunas: famílias sem documento, com chamada direta para o upload.
""",
        fora_escopo="""
- Edição ou exclusão de documento pela interface.
- Visualizador de PDF embutido.
""",
        decisoes="""
- **Método de extração exposto na interface.** Um documento vindo de OCR tem risco maior de
  erro; quem opera precisa saber disso ao avaliar uma prescrição.
- **Upload disparado a partir da lacuna.** O caminho natural é ver o que falta e resolver ali,
  não procurar um botão em outra tela.
""",
        contrato="""
```ts
GET  /api/documents -> Document[]
POST /api/documents (multipart: file, fault_family, title) -> { documentId, status, chunks }
```
""",
        acceptance=[
            ("Lista reflete o backend",
             "Documentos, páginas e contagem de chunks batem com `/api/documents`."),
            ("OCR é sinalizado",
             "O documento processado por OCR aparece marcado como tal na lista."),
            ("Upload dá retorno claro",
             "Durante o processamento há indicação de progresso; ao final, sucesso com contagem de chunks ou erro com motivo."),
            ("Lacunas viram ação",
             "Cada família sem documento tem um botão que abre o upload já com a família preenchida."),
            ("Cobertura atualiza na hora",
             "Após upload bem-sucedido, a lista e o painel de lacunas se atualizam sem recarregar a página."),
            ("Arquivo inválido é barrado com clareza",
             "Enviar um não-PDF mostra mensagem específica, sem deixar a interface em estado de carregamento infinito."),
        ],
        tasks=[
            "Implementar a listagem de documentos com estado de indexação",
            "Implementar a sinalização visual de extração por OCR",
            "Implementar o formulário de upload com seleção de família e barra de progresso",
            "Implementar o painel de lacunas de cobertura com ação de upload",
            "Invalidar as queries de documentos e de cobertura após upload",
            "Tratar e testar os casos de erro de upload",
        ],
    ),
    # ------------------------------------------------------------------ 005
    dict(
        id="SPEC-FEAT-005",
        title="Análise de evento e simulador",
        epic="analise",
        atende="Critério de entrevista: demonstração com dados de teste",
        depends=["SPEC-FEAT-001", "backend/SPEC-FEAT-013"],
        contexto="""
Ponto de entrada da demonstração ao vivo. Precisa aceitar o JSON de sensor do enunciado e,
principalmente, permitir puxar um evento real do holdout — mostrar o sistema acertando (ou
errando) sobre dado que ele nunca viu é mais forte que qualquer slide.
""",
        escopo="""
- Editor de JSON com validação e mensagem de erro apontando o campo problemático.
- Botão "carregar evento do holdout": busca um evento real de 10–16/jun via
  `/api/events/sample`, com filtro opcional por família.
- Execução da análise com exibição do rótulo real ao lado do diagnóstico — acerto e erro
  ficam visíveis, sem maquiagem.
- Cartão de diagnóstico: família, confiança, sinalização de fora de distribuição.
- Tempo de cada etapa exibido (similaridade, recuperação, geração, verificação).
""",
        fora_escopo="""
- Upload de CSV em lote para análise.
- Edição gráfica de valores por sliders.
""",
        decisoes="""
- **Mostrar o rótulo real junto do diagnóstico.** Esconder o gabarito numa demonstração
  técnica é o que produz a pergunta constrangedora na entrevista. Expor demonstra confiança
  e permite discutir os erros.
- **Amostra vem do holdout, nunca do treino.** Demonstrar sobre dado de treino inflaria o
  resultado e seria vazamento óbvio.
""",
        contrato="""
```ts
GET  /api/events/sample?family=&split=holdout -> SensorEvent
POST /api/events/analyze (SensorEvent) -> AnalyzeResponse
```
""",
        acceptance=[
            ("JSON do enunciado funciona",
             "Colar o exemplo do §2 do desafio e executar produz análise completa."),
            ("JSON inválido é explicado",
             "Campo ausente ou tipo errado gera mensagem apontando o campo, sem chamar a API."),
            ("Amostra é sempre de holdout",
             "Todo evento carregado pelo botão tem data entre 10 e 16/jun/2026."),
            ("Gabarito visível",
             "O rótulo real do evento aparece ao lado do diagnóstico, com indicação de acerto ou erro."),
            ("Fora de distribuição é comunicado",
             "Evento fora de distribuição exibe aviso específico, distinto de \"falha sem documento\"."),
            ("Desempenho transparente",
             "Os tempos por etapa aparecem na interface após a análise."),
        ],
        tasks=[
            "Implementar o editor de JSON com validação contra o schema do evento",
            "Implementar a busca de amostra do holdout com filtro por família",
            "Implementar o cartão de diagnóstico com confiança e sinalização de fora de distribuição",
            "Implementar a comparação diagnóstico × rótulo real",
            "Exibir os tempos por etapa",
            "Tratar os estados de carregamento e erro da análise",
        ],
    ),
    # ------------------------------------------------------------------ 006
    dict(
        id="SPEC-FEAT-006",
        title="Painel de eventos similares",
        epic="analise",
        atende="§3 — quantidade de eventos similares, distribuição, frequência, contexto operacional",
        depends=["SPEC-FEAT-005", "backend/SPEC-FEAT-005"],
        contexto="""
Materializa exatamente a lista de informações que o §3 do desafio pede como saída da busca
por similaridade. É a evidência que sustenta o diagnóstico e antecede a prescrição.
""",
        escopo="""
- Tabela dos vizinhos mais próximos: identificador, data, família, similaridade e RPM.
- Contagem de eventos similares por família, com a distribuição do voto visível — deixa claro
  se o diagnóstico foi unânime ou disputado.
- Linha do tempo dos eventos similares, com o evento em análise posicionado nela.
- Bloco de contexto operacional: faixa de RPM e temperatura da vizinhança comparada à do
  evento analisado.
- Frequência de ocorrência e intervalo médio entre eventos.
""",
        fora_escopo="""
- Inspeção da forma de onda bruta — não está no dataset.
""",
        decisoes="""
- **Distribuição do voto exposta, não só a família vencedora.** Um diagnóstico 51% × 49% e
  outro 98% × 2% não merecem a mesma leitura, e a interface precisa deixar isso evidente.
- **Similaridade em barra e em número.** A barra dá leitura imediata; o número permite
  comparação precisa na discussão técnica.
""",
        contrato="""
```ts
POST /api/events/similar (SensorEvent) -> {
  neighbors, familyCounts, timeline,
  frequencyPerDay, meanIntervalHours, operatingContext
}
```
""",
        acceptance=[
            ("Todos os itens do enunciado presentes",
             "A tela exibe quantidade de eventos similares, distribuição temporal, frequência e contexto operacional."),
            ("Vizinhos são do histórico",
             "Nenhum vizinho listado pertence ao período de holdout."),
            ("Voto disputado é perceptível",
             "Um caso com voto dividido é visualmente distinguível de um caso unânime."),
            ("Evento em análise localizado na linha do tempo",
             "O marcador do evento analisado aparece posicionado corretamente entre os similares."),
            ("Contexto operacional comparável",
             "As faixas de RPM e temperatura da vizinhança aparecem lado a lado com os valores do evento."),
            ("Tabela usável com muitos vizinhos",
             "Com k = 50 a tabela permanece navegável, ordenável e sem quebra de layout."),
        ],
        tasks=[
            "Implementar a tabela de vizinhos com barra de similaridade e ordenação",
            "Implementar o gráfico de distribuição do voto por família",
            "Implementar a linha do tempo dos similares com marcador do evento analisado",
            "Implementar o bloco de contexto operacional comparativo",
            "Exibir frequência e intervalo médio com unidades explícitas",
            "Testar com k alto e ajustar a densidade da tabela",
        ],
    ),
    # ------------------------------------------------------------------ 007
    dict(
        id="SPEC-FEAT-007",
        title="Chat prescritivo com citações",
        epic="analise",
        atende="§3 — modelo de linguagem para auxílio; OBS 3 — interação com o chat na apresentação",
        depends=["SPEC-FEAT-005", "backend/SPEC-FEAT-011"],
        contexto="""
A observação 3 do enunciado é explícita: espera-se interação mínima com o modelo durante a
apresentação. Este é o componente que será operado ao vivo, e onde o critério "alucinação do
modelo" vai ser julgado.
""",
        escopo="""
- Conversa com histórico, ancorada no evento em análise (o contexto do evento acompanha as
  perguntas seguintes).
- Resposta renderizada por seções: diagnóstico, evidência, inspeção, correção, validação.
- **Citações clicáveis** — `[Doc2, p. 4]` abre um painel lateral com o trecho exato recuperado,
  com destaque. É o que transforma "confie no modelo" em "verifique você mesmo".
- Indicador de embasamento da resposta (score de grounding) e lista do que foi removido por
  falta de suporte.
- Perguntas sugeridas conforme o diagnóstico, para agilizar a demonstração.
- Resposta em fluxo (streaming) quando disponível.
""",
        fora_escopo="""
- Conversa livre sem evento associado — o sistema é prescritivo, ancorado em um evento.
- Histórico persistido entre sessões.
""",
        decisoes="""
- **Citação clicável mostrando o trecho original.** É a defesa mais concreta contra a
  acusação de alucinação: o avaliador confere na hora, contra o PDF.
- **Score de embasamento visível.** Assume a incerteza em vez de escondê-la — postura mais
  forte que fingir certeza absoluta.
- **Resposta seccionada em vez de bolha de texto.** Espelha a estrutura da saída do backend e
  é o formato que um técnico consegue seguir passo a passo.
""",
        contrato="""
```ts
POST /api/chat { eventId?, event?, messages[] } -> {
  answer: PrescriptiveAnswer, citations, grounding, timings
}
```
""",
        acceptance=[
            ("Prescrição legível por seções",
             "Diagnóstico, inspeção, correção e validação aparecem separados e na ordem."),
            ("Citação abre o trecho real",
             "Clicar em uma citação exibe o texto do chunk recuperado, com documento e página."),
            ("Embasamento exposto",
             "O score de grounding aparece na resposta, junto do que foi removido por falta de suporte."),
            ("Contexto do evento persiste",
             "Uma pergunta de acompanhamento (\"e como valido depois?\") é respondida sem reenviar o evento."),
            ("Erro do provider é comunicado",
             "Falha do LLM mostra mensagem acionável e mantém o histórico da conversa."),
            ("Interação fluida na demonstração",
             "A resposta começa a aparecer em poucos segundos (streaming) ou há indicação clara de progresso."),
        ],
        tasks=[
            "Implementar o componente de conversa com histórico ancorado no evento",
            "Implementar a renderização seccionada da resposta prescritiva",
            "Implementar citações clicáveis e o painel lateral de trecho recuperado",
            "Implementar o indicador de embasamento e a lista de itens removidos",
            "Implementar perguntas sugeridas por diagnóstico",
            "Implementar streaming (ou indicador de progresso por etapa)",
            "Tratar erro do provider preservando o histórico",
        ],
    ),
    # ------------------------------------------------------------------ 008
    dict(
        id="SPEC-FEAT-008",
        title="Estado de falha não documentada",
        epic="analise",
        atende="§3 — reportar ausência de documento e sugerir registro",
        depends=["SPEC-FEAT-007", "backend/SPEC-FEAT-008", "SPEC-FEAT-004"],
        contexto="""
A regra de recusa do enunciado precisa de tratamento visual próprio. Se a recusa parecer um
erro do sistema, o avaliador lê como falha; se parecer uma decisão deliberada e informada,
lê como o comportamento correto — que é o que é.
""",
        escopo="""
- Estado visual distinto (não é erro, não é sucesso): a análise estatística é entregue, a
  prescrição é explicitamente retida.
- Texto alinhado ao enunciado: não existe documentação para o problema identificado; sugere
  registrar um novo documento para o defeito.
- Mesmo sem prescrição, exibe o que o sistema sabe: família diagnosticada, quantidade de
  eventos similares, distribuição temporal.
- Ação direta de registrar documento, com a família já preenchida (SPEC-FEAT-004).
- **Distinção entre três situações**, com mensagens diferentes: falha sem documento; evento
  fora de distribuição; estado operacional (não é problema).
""",
        fora_escopo="""
- Sugerir procedimento "genérico" de manutenção como paliativo — seria exatamente a
  alucinação que a regra existe para impedir.
""",
        decisoes="""
- **Recusa desenhada como resultado, não como erro.** É o comportamento correto do sistema, e
  a interface precisa comunicar isso com clareza.
- **Três mensagens distintas para três causas distintas.** Colapsá-las em "não sei" desperdiça
  a informação mais interessante da solução.
""",
        contrato="""
```ts
coverage.reason: "covered" | "no_document" | "state_not_problem" | "out_of_distribution"
```
""",
        acceptance=[
            ("Recusa não parece falha do sistema",
             "O estado usa tratamento visual informativo, distinto do estado de erro da aplicação."),
            ("Texto fiel ao enunciado",
             "A mensagem informa que não há documentação para o problema identificado e sugere registrar um novo documento."),
            ("Evidência continua sendo entregue",
             "Família, contagem de eventos similares e distribuição temporal permanecem visíveis na recusa."),
            ("Três causas, três mensagens",
             "`no_document`, `out_of_distribution` e `state_not_problem` produzem textos e ícones diferentes."),
            ("Ciclo fecha na interface",
             "A partir da recusa, o usuário registra o documento e, ao refazer a análise, recebe a prescrição citada."),
            ("Nenhum conselho sem fonte",
             "Nenhum texto de orientação técnica aparece na tela de recusa."),
        ],
        tasks=[
            "Implementar o componente de estado de cobertura com as três variantes",
            "Escrever os textos de cada variante alinhados ao enunciado",
            "Manter o painel de evidência visível no estado de recusa",
            "Ligar a ação de registrar documento com a família pré-preenchida",
            "Reexecutar a análise automaticamente após indexação bem-sucedida",
            "Ensaiar o ciclo completo recusa → upload → prescrição para a demonstração",
        ],
    ),
]
