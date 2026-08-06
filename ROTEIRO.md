# Roteiro de demonstração
Todos os números foram medidos e conferidos contra o sistema rodando. Se algum divergir na
hora, o certo é o da tela: os relatórios são gerados do banco, não escritos à mão.

---

## Antes de começar

```bash
# 1. Banco
docker compose -f backend/docker-compose.yml up -d

# 2. API
cd backend && ../.venv/Scripts/activate && python manage.py runserver

# 3. Frontend, em outro terminal
cd frontend && npm run dev
```

Confira em `http://127.0.0.1:8001/api/health` antes de abrir a tela. Ele responde o estado real
de banco, eventos, documentos, scaler e provedor do modelo — se algo estiver faltando, aparece
aqui e não no meio da apresentação.

**Deixe aberto em abas separadas:** o painel (`localhost:5173`), o Swagger
(`127.0.0.1:8001/docs`) e este arquivo.

**Tenha o exemplo do enunciado à mão** — o botão "Preencher com o exemplo do enunciado" na tela
de análise já traz o JSON da seção 2 literal, não precisa copiar de lugar nenhum.

---

## O fio condutor

Tudo se resume a uma frase, e vale dizê-la logo no começo:

> O sistema só recomenda o que consegue citar. Quando não consegue, ele diz que não sabe — e
> diz por quê.

É o que separa esta entrega de um chatbot que responde qualquer coisa com confiança. Cada tela
do roteiro é uma evidência dessa frase.

---

## Parte 1 — Painel (2 min)

**Abra em `/`.**

O que dizer, na ordem em que a tela apresenta:

**A regra do sistema.** "6 de 9 tipos de falha têm procedimento cadastrado. Os outros 3 o
sistema sabe identificar, mas se recusa a prescrever. Vou mostrar isso funcionando."

**Os três passos.** 166.796 leituras entre 30/04 e 16/06 de 2026; 9 tipos de falha; 6
documentos técnicos indexados em 124 trechos pesquisáveis.

**Quando as falhas aconteceram.** Aponte a linha tracejada em 10/06: "tudo à direita foi
separado como conjunto de teste e nunca entra na busca. O corte é temporal, não sorteado — e
isso é deliberado. Sorteio aleatório colocaria leituras da mesma sessão de ensaio dos dois
lados, e o vizinho mais próximo de um evento de teste seria praticamente ele mesmo. A acurácia
sairia inflada e falsa."

**Com que frequência cada falha aparece.** "A seção 1 do enunciado pede quantidade e frequência
de ocorrências. Contado em dias, não em leituras: o coletor amostra a cada poucos segundos
durante um ensaio, então intervalo entre leituras mede a cadência do equipamento, não a
recorrência do defeito."

**Por que nem toda leitura tem diagnóstico.** Esta é a tela mais importante do painel. Troque a
métrica no seletor e mostre as faixas se sobrepondo. "Rolamento, desbalanceamento e polia
ocupam praticamente a mesma faixa de vibração. Nenhum método que compare esses números separa
as três com confiança. Eu testei: um classificador supervisionado treinado nos mesmos dados
chega a 39,8%, contra 40,2% da busca por similaridade. O teto é o sensor, não a técnica."

> Se perguntarem "40% não é pouco?": é exatamente por isso que a abstenção existe. Prescrever
> intervenção física com 40% de acerto é pior que admitir desconhecimento. Com o limiar em 0,70
> o sistema responde 47% dos casos a 59% de precisão; em 0,95, responde 19% a 73%. É um botão,
> e a escolha é do cliente.

---

## Parte 2 — O caminho feliz (4 min)

**Vá em Análise.** Deixe o seletor de condição em **"que produz prescrição"**.

### Passo 1 — a leitura

"É um evento real do conjunto de teste. O modelo nunca viu esta leitura."

### Passo 2 — identificar a falha

Clique em analisar. Volta em menos de um segundo — não passa pelo modelo de linguagem.

Aponte a frase: "100% dos 50 registros mais parecidos têm a mesma falha." E a barra de votação.
"A confiança não vem da distância ao vizinho. Vem da concordância da vizinhança."

> Vale contar por quê, se houver espaço: "O plano original era usar distância como sinal de
> confiança. A medição mostrou o oposto — filtrando por distância ≤ 0,5 a precisão **cai** para
> 18,4%, pior que não filtrar. Os vizinhos mais próximos caem no cluster dominante de
> rolamento, que é 36% do histórico. Proximidade alta muitas vezes significa absorção pela
> classe majoritária. Ter seguido o plano produziria alta confiança justamente nos casos mais
> enviesados."

### Passo 3 — o procedimento

Leva de 25 a 90 segundos. **Fale durante a espera** — a barra mostra a etapa e o cronômetro.

Enquanto roda: "Ele está buscando os trechos no manual da família diagnosticada e redigindo o
procedimento. O filtro por família é rígido, não um peso: os seis documentos compartilham quase
o mesmo vocabulário — vibração elevada, aquecimento nos mancais, desgaste — e sem filtro a
busca semântica erra 3 de 7 consultas, apontando o manual de correias para um defeito de
rolamento. Sairia fluente, citado, e errado."

Quando aparecer: **clique numa citação.** Abre o trecho exato do manual que foi entregue ao
modelo.

"Esta é a resposta para 'como sei que ele não inventou'. Não é o modelo dizendo de onde tirou —
é o texto que ele recebeu."

Aponte o selo de verificação. "Cada frase é conferida contra os trechos recuperados depois de
gerada. O que não tem fonte é removido, e o que foi removido aparece na tela."

### Passo 4 — chat

Perguntas que funcionam bem:

- "Que ferramentas eu preciso para fazer isso?"
- "Qual o risco se eu não corrigir agora?"
- "Posso fazer com a máquina em operação?"

E uma que **não** funciona, para mostrar o limite:

- "Qual a previsão do tempo amanhã?" — sai recusa, o filtro de domínio barra.

---

## Parte 3 — A recusa (3 min)

É o ponto alto. Não trate como caminho de erro.

**Abra "Opções de demonstração"** e baixe a concordância mínima para **50%**. Em seguida troque
o seletor para **"sem documento cadastrado"**.

> Por que 50%: as três famílias descobertas raramente são reconhecidas como elas mesmas — os
> vizinhos se dividem. Se ficar em 70% a busca não acha nenhuma e a tela mostra uma mensagem
> explicando exatamente isso. Vale mostrar de propósito, se sobrar tempo: o sistema explica a
> própria ausência de resultado em vez de devolver lista vazia.

O sistema identifica `eccentric_rotor` com 55% de concordância e **se recusa a prescrever**.

"Ele sabe qual é a falha. Não sabe o procedimento, porque ninguém cadastrou o manual. Então ele
não inventa: nomeia a lacuna e pede o documento."

**Clique em "cadastrar documento"** — leva direto para a tela de Documentos, com a família já
selecionada. "O ciclo fecha aqui: sobe o PDF, ele é indexado, e a próxima leitura dessa família
recebe procedimento."

### A família impossível

Se perguntarem sobre `falta_fase`: 800 registros no conjunto de teste, **zero no histórico**.
Nenhuma busca por similaridade poderia acertá-la — não existe vizinho para encontrar. O sistema
recusa 59% desses eventos.

"Isso não é uma falha do modelo. É uma propriedade do dado, e o comportamento correto diante
dela é recusar."

---

## Parte 4 — A entrada do enunciado (2 min)

Volte para Análise e clique em **"Colar JSON"** → **"Preencher com o exemplo do enunciado"**.

É o payload literal da seção 2. Analise.

O sistema levanta a hipótese **cocked_rotor com 56% de concordância** — que é o rótulo real do
exemplo — e **se abstém**, porque 56% está abaixo do limiar de 70%.

"Ele acertou e mesmo assim não prescreveu. É o comportamento correto: 56% de concordância não
sustenta uma ordem de manutenção. A hipótese aparece na tela para a equipe técnica avaliar, mas
não vira procedimento."

> Se quiser mostrar o outro lado: baixe o limiar para 50% e refaça. Agora prescreve. O
> parâmetro é explícito e a consequência é visível — não há mágica escondida.

---

## Parte 5 — A API (3 min)

**Abra `127.0.0.1:8001/docs`.**

Três endpoints externos, cada um com seu escopo no JWT:

| Rota | Escopo | Para quem |
| --- | --- | --- |
| `POST /api/v1/predict` | `predict` | Sistema que consulta um diagnóstico |
| `POST /api/v1/upload_doc` | `upload` | Quem cadastra procedimento |
| `POST /api/v1/events` | `ingest` | Coletor que envia leitura |

"Escopos separados de propósito: o coletor que envia leitura não obtém prescrição, e o
integrador somente-leitura não injeta documento na base que orienta intervenção física em
equipamento."

**Demonstre `/api/v1/events`.** Pegue o token em `/auth/token` e envie o mesmo JSON do
enunciado.

"Este endpoint é o que fecha o ciclo da Figura 01. A leitura chega do supervisório e passa a
fazer parte do histórico consultado nas próximas análises — o sistema aprende com o que
acontece na planta, sem reprocessar nada."

Mostre o comportamento com dado incompleto: **retire o campo `fault`** e envie de novo. Grava
igual.

"A medição do sensor vale mais que a anotação do operador. Sem rótulo, a leitura entra no
histórico para registro mas não participa da votação. Com rótulo fora da taxonomia, idem — e o
rótulo desconhecido volta na resposta, para alguém decidir se vira família nova. Recusar seria
perder o dado."

---

## Parte 6 — Como foi construído (2 min)

Se houver interesse no processo:

**Spec-driven.** 25 features, cada uma com `spec.md`, `acceptance.md` e `tasks.md`. O status não
é escrito à mão — um gerador conta os checkboxes e reconstrói o índice. Uma feature só fecha
quando tarefas e critérios de aceite estão marcados, e um critério só é marcado depois de
verificado na prática.

**Nada roda em nuvem além do LLM.** Embeddings em ONNX na CPU, OCR local com PP-OCR. Um dos seis
documentos não tem camada de texto — é imagem — e o OCR resolve isso sem enviar o manual da
empresa para fora.

**Arquitetura de implantação.** [`ARQUITETURA.md`](ARQUITETURA.md) cobre segmentação de rede
ISA-95, dimensionamento com medições reais, degradação, ciclo de vida do modelo, as oito
alternativas descartadas e por quê.

---

## Perguntas prováveis

**"Por que não usou um modelo treinado?"**
Usei, para medir: HistGradientBoosting, 200 iterações, 78,8% no treino e 39,8% no holdout —
abaixo da busca por similaridade. Existe deslocamento de distribuição real entre o histórico e
as sessões novas: a família rolamento desloca 0,45 desvios em média, 1,46 na temperatura, e o
holdout opera num regime de RPM quase ausente do histórico. Além disso, um classificador não
explica a decisão. A busca por similaridade entrega os 50 eventos que sustentam o diagnóstico.

**"E se o modelo alucinar?"**
Quatro camadas. O filtro por família impede que o manual errado entre no contexto. A citação
inventada é removida antes de a resposta sair — se o rótulo não corresponde a nenhum trecho
recuperado, ele some. A verificação confere cada afirmação contra os trechos e derruba o que
não tem fonte, mostrando na tela o que foi derrubado. E o gate de cobertura impede que a
pergunta chegue ao modelo se não houver documento.

**"Quanto custa rodar isso?"**
Uma chamada por análise, 1.288 tokens de entrada e cerca de 4.250 de saída. Embeddings e OCR
são locais, custo zero. O dimensionamento está em ARQUITETURA.md, incluindo o cenário sem
provedor externo.

**"Por que PostgreSQL com pgvector e não um banco vetorial dedicado?"**
São 166 mil vetores de 384 dimensões — 57 MB. Um banco vetorial dedicado seria um segundo
sistema para operar, monitorar e fazer backup, para um volume que o PostgreSQL resolve com um
índice. E os dados relacionais e vetoriais ficam na mesma transação.

**"O que você faria com mais tempo?"**
Analisaria o espectro de vibração, não só as métricas agregadas. As 16 features são estatísticas
resumidas; a assinatura de um defeito de pista externa de rolamento está numa frequência
específica — BPFO — que só aparece no espectro. É aí que está o ganho real de acurácia, e é
limitação do dado fornecido, não do método.

---

## Se algo der errado

| Sintoma | Causa provável | O que fazer |
| --- | --- | --- |
| Procedimento não volta, cronômetro subindo | Provedor do modelo lento ou sem crédito | A requisição é encerrada em 3 min com mensagem. Siga para a recusa (Parte 3), que não usa o modelo |
| "sem diagnóstico" em tudo | Limiar alto para a leitura sorteada | Abra "Opções de demonstração" e baixe a concordância mínima |
| 404 ao buscar amostra | Nenhum evento produz aquele desfecho no limiar atual | A própria mensagem diz qual limiar tentar |
| Tela em branco | API fora | `http://127.0.0.1:8001/api/health` |

**Se o modelo cair no meio da apresentação**, não improvise: as Partes 1, 2 (até o passo 2), 3 e
5 funcionam inteiras sem ele. Só o passo 3 e o chat dependem do provedor externo — e isso é, em
si, um ponto de arquitetura que vale dizer em voz alta.
