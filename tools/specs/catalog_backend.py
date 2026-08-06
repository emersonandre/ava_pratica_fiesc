"""Catálogo de features do backend.

Fonte única das specs. O gerador (`tools/specs/gen.py`) materializa cada item em
`backend/docs/SPEC-FEAT-XXX/{spec.md,acceptance.md,tasks.md}`.
"""

APP = "backend"
DOCS_DIR = "backend/docs"
TITLE = "Backend — Manutenção Prescritiva"
STACK = "Python 3.13 · FastAPI · PostgreSQL 17 + pgvector · fastembed (ONNX) · OpenAI/DeepSeek"

EPICS = {
    "infra": "Infraestrutura e dados",
    "similaridade": "Similaridade e documentos",
    "rag": "RAG e LLM",
    "api": "API, seguranca e qualidade",
}

FEATURES = [
    # ------------------------------------------------------------------ 001
    dict(
        id="SPEC-FEAT-001",
        title="Infraestrutura local reproduzível",
        epic="infra",
        atende="DIF (Bancos de Dados, Soluções de Deploy)",
        depends=[],
        contexto="""
O projeto precisa subir na máquina do avaliador sem etapas manuais. Toda a persistência
— dados tabulares de sensor e vetores de embedding — fica em um único PostgreSQL com a
extensão `pgvector`, evitando um segundo serviço só para busca vetorial.
""",
        escopo="""
**Um `docker-compose.yml` por aplicação**, não um único na raiz:

| Arquivo | Serviços |
| --- | --- |
| `backend/docker-compose.yml` | `db` (PostgreSQL 17 + pgvector, volume nomeado) e `api` |
| `frontend/docker-compose.yml` | `web` |

Os dois se encontram pela rede externa `prescritiva-net`. O frontend é reconstruído ou
reiniciado sem tocar no banco, e o backend sobe sozinho para integração com sistemas da planta.

- Configuração centralizada em `app/settings/` via `pydantic-settings`, lida de `.env`.
- `.env.example` em cada app, documentando todas as variáveis.
- `manage.py`: CLI administrativa única — `runserver`, `initdb`, `ingest`, `secrets`,
  `report`, `check`, `shell`.
- `scripts/init_db.py`: cria extensão, schema e índices de forma idempotente.
- `scripts/gen_secrets.py`: gera os segredos de autenticação (SPEC-FEAT-016).

### Estrutura em camadas

Padrão MVC adaptado a uma API:

| Camada | Papel |
| --- | --- |
| `controllers/` | Rotas HTTP: autenticação, validação, tradução para o serviço |
| `services/` | Regra de negócio: similaridade, gate de cobertura, RAG, prescrição |
| `repositories/` | Todas as consultas ao banco |
| `models/` | Entidades e schema — um arquivo por tabela |
| `schemas/` | Contratos de entrada e saída da API |
| `core/` | Domínio puro (taxonomia, features), sem I/O |
| `integrations/` | Fronteiras externas: LLM, embeddings, OCR |

Regra que mantém a separação honesta: **um controller nunca monta consulta SQL, e um
repositório nunca chama LLM.**
""",
        fora_escopo="""
- Orquestração em Kubernetes (fica descrita no documento de arquitetura, não implementada).
- Cadastro e gestão de usuários finais — a autenticação é máquina-a-máquina (SPEC-FEAT-016).
""",
        decisoes="""
- **Um banco só (PostgreSQL + pgvector) em vez de banco vetorial dedicado.** O volume é de
  ~167 mil vetores de 18 dimensões e algumas centenas de chunks de documento; não justifica
  um segundo serviço, e permite fazer o `JOIN` entre similaridade de sensor e metadado de
  falha em uma única consulta SQL.
- **Compose por aplicação, não um só na raiz.** Backend e frontend têm ciclos de vida
  independentes: em planta, a API sobe junto do banco e a interface é implantada à parte.
  Um compose único acoplaria os dois e obrigaria a derrubar o banco para publicar a interface.
- **Sem migrations (Alembic) nesta entrega.** O schema é criado por script versionado; a
  base é reconstruída por ingestão, não evoluída em produção.
""",
        contrato="""
```
DATABASE_URL=postgresql+psycopg://prescritiva:...@localhost:5433/prescritiva
LLM_PROVIDER=openai|deepseek
LLM_API_KEY=...
LLM_MODEL=...
LLM_BASE_URL=...           # vazio para OpenAI
VISION_MODEL=...           # usado apenas no OCR (SPEC-FEAT-006)
EMBEDDING_MODEL=intfloat/multilingual-e5-small
JWT_SECRET= / API_CLIENT_ID= / API_CLIENT_SECRET=    # externo  (SPEC-FEAT-016)
INTERNAL_API_KEY=                                    # interno  (SPEC-FEAT-016)
```
""",
        acceptance=[
            ("O compose do backend deixa o banco pronto",
             "Após `docker compose -f backend/docker-compose.yml up -d`, "
             "`SELECT extversion FROM pg_extension WHERE extname='vector'` retorna uma versão."),
            ("Frontend e backend sobem de forma independente",
             "Derrubar e subir o compose do frontend não reinicia o container do banco nem o da API."),
            ("Inicialização é idempotente",
             "Rodar `init_db` duas vezes seguidas termina com código 0 e sem exceção nas duas execuções."),
            ("Nenhum segredo versionado",
             "`.env` está no `.gitignore`; cada app tem `.env.example` com todas as chaves e valores de exemplo."),
            ("Configuração falha cedo e com clareza",
             "Subir a API sem `LLM_API_KEY` produz erro de validação nomeando a variável ausente, não um erro em tempo de requisição."),
            ("Porta não conflita com Postgres local",
             "O compose expõe 5433 no host para não colidir com uma instalação existente na 5432."),
        ],
        tasks=[
            "Criar `backend/docker-compose.yml` com serviços `db` e `api`, volume, healthcheck e rede externa",
            "Criar `frontend/docker-compose.yml` com o serviço `web` na mesma rede externa",
            "Criar `backend/.env.example` e `frontend/.env.example` com todas as variáveis documentadas",
            "Implementar `app/config.py` com `Settings` (pydantic-settings) e cache de instância",
            "Implementar `app/db.py`: engine SQLAlchemy, sessão e verificação de conectividade",
            "Implementar `app/scripts/init_db.py` (extensão + tabelas + índices, idempotente)",
            "Implementar `app/scripts/gen_secrets.py` para gerar os segredos de autenticação",
            "Implementar `manage.py` com os comandos administrativos",
            "Criar `.gitignore` cobrindo `.venv`, `.env`, `__pycache__`, artefatos de modelo",
            "Escrever os `Dockerfile` de backend e frontend",
            "Validar: subir do zero em máquina limpa e registrar o tempo no README",
        ],
    ),
    # ------------------------------------------------------------------ 002
    dict(
        id="SPEC-FEAT-002",
        title="Taxonomia canônica de falhas",
        epic="infra",
        atende="§6 — Descrição dos dados (estados × problemas)",
        depends=["SPEC-FEAT-001"],
        contexto="""
A coluna `fault` do `banner.csv` contém **151 rótulos distintos**, anotados manualmente por
operadores. Eles não representam 151 falhas: colapsam em ~15 famílias, poluídas por sufixos
de sessão de ensaio e por erros de digitação. Sem normalização, qualquer contagem de
"eventos similares" e qualquer mapa falha→documento nasce errado.
""",
        escopo="""
Normalizador determinístico que produz, para cada registro:

| Campo | Descrição |
| --- | --- |
| `raw_fault` | rótulo original, preservado para auditoria |
| `canonical_fault` | slug canônico (ex.: `rolamento_inner`) |
| `fault_family` | família agregadora (ex.: `rolamento`) |
| `is_problem` | `false` para estados operacionais, `true` para falhas |

**Três classes de ruído a tratar:**

1. **Sufixos de sessão de coleta** — `_2`, `_3`, `_4`, `_novo`, `_teste`, `_carga`, `_carga_2`,
   `_carga_3`, `_pos_2`, `_adxl_0`, `_adxl_1` e o prefixo `new_`. Indicam repetição do ensaio,
   mudança de carga ou troca de acelerômetro (ADXL) — **não** uma falha diferente.
2. **Erros de digitação do operador** — confirmados no dataset: `desabalanceado_3`,
   `desbanlanceado_carga_3_2`, `ddesbalanceado_adxl_0`, `dedesbalanceado_adxl_1`,
   `new_desabanceado_1`, `mortor_desligado_novo`, `normla_carga_3_3`, `cockecocked_adxl_0`,
   `new_tes`.
3. **Estado × Problema** — `normal`, `baseline`, `teste`, `acelerando` e `motor_desligado`
   (e variantes) são estados do sistema, conforme §6. Ficam fora do universo de prescrição.
""",
        fora_escopo="""
- Inferir família por similaridade de sinal (isso é a SPEC-FEAT-005); aqui a normalização é
  puramente léxica e auditável.
- Corrigir rótulos que o operador errou de *falha* (não só de grafia) — não há como saber.
""",
        decisoes="""
- **Normalização léxica determinística, não fuzzy matching automático.** Um `difflib` cego
  aproximaria `desalinhado` de `desbalanceado` (distância pequena, falhas distintas). Os typos
  são poucos e conhecidos: viram um dicionário explícito, revisável e testável.
- **`raw_fault` nunca é descartado.** Auditoria e defesa na entrevista dependem de mostrar o
  antes e o depois.
- **Falhar alto em rótulo desconhecido.** Um rótulo novo que não case com nenhuma regra
  levanta erro na ingestão em vez de virar `unknown` silencioso.
""",
        contrato="""
```python
@dataclass(frozen=True)
class FaultLabel:
    raw: str
    canonical: str
    family: str
    is_problem: bool

def normalize_fault(raw: str) -> FaultLabel: ...
```
""",
        acceptance=[
            ("Cobertura total dos rótulos",
             "Os 151 rótulos distintos do `banner.csv` são mapeados; nenhum cai em `unknown`."),
            ("Estados não são tratados como falha",
             "`normal`, `normal_2`, `baseline`, `new_baseline`, `teste`, `new_teste`, `acelerando`, "
             "`motor_desligado`, `mortor_desligado_novo` retornam `is_problem = False`."),
            ("Typos convergem para o canônico correto",
             "`desabalanceado_3`, `desbanlanceado_carga_3_2`, `ddesbalanceado_adxl_0`, "
             "`dedesbalanceado_adxl_1` e `new_desabanceado_1` retornam família `desbalanceamento`."),
            ("Sufixos de sessão não criam famílias novas",
             "`rolamento_inner`, `rolamento_inner_2`, `rolamento_inner_carga`, `rolamento_inner_adxl_0` "
             "e `new_rolamento_inner_0` compartilham a mesma família `rolamento`."),
            ("Famílias distintas não se fundem",
             "`desalinhado` e `desbalanceado` produzem famílias diferentes."),
            ("Rótulo desconhecido é erro, não silêncio",
             "`normalize_fault('xpto_999')` levanta `UnknownFaultLabel`."),
            ("Relatório auditável publicado",
             "`backend/docs/analise/taxonomia.md` traz a matriz rótulo bruto → canônico → família, "
             "com contagem de registros por linha."),
        ],
        tasks=[
            "Extrair os 151 rótulos distintos e classificar manualmente em famílias (planilha de apoio)",
            "Implementar `app/core/taxonomy.py`: dicionário de typos, regras de sufixo, conjunto de estados",
            "Definir as famílias canônicas e documentar cada uma com uma frase de descrição",
            "Implementar `normalize_fault` e a exceção `UnknownFaultLabel`",
            "Escrever `tests/test_taxonomy.py` cobrindo cada critério de aceite",
            "Gerar `backend/docs/analise/taxonomia.md` por script, a partir do dataset real",
            "Revisar a matriz final e confirmar que nenhuma família distinta foi fundida",
        ],
    ),
    # ------------------------------------------------------------------ 003
    dict(
        id="SPEC-FEAT-003",
        title="Feature engineering dos sinais de vibração",
        epic="infra",
        atende="§3 — análise de novos conjuntos de dados",
        depends=["SPEC-FEAT-002"],
        contexto="""
O dataset traz 24 colunas numéricas, mas várias são **a mesma grandeza física em outra
unidade**. Auditoria sobre os 166.796 registros confirmou:

| Par | Correlação | Razão |
| --- | ---: | ---: |
| `z_rms_velocity_in_s` × `z_rms_velocity_mm_s` | 0,999999 | 25,4114 |
| `x_rms_velocity_in_s` × `x_rms_velocity_mm_s` | 0,999999 | 25,4079 |
| `z_peak_velocity_in_s` × `z_peak_velocity_mm_s` | 1,000000 | 25,4081 |
| `x_peak_velocity_in_s` × `x_peak_velocity_mm_s` | 1,000000 | 25,4056 |
| `temperature_f` × `temperature_c` | 0,999999 | relação afim |

Em uma busca por distância, manter as duas versões dá peso dobrado àquela grandeza e
enviesa o vizinho mais próximo.
""",
        escopo="""
- Auditoria de redundância: verificar numericamente cada par suspeito no dataset completo.
- Seleção do vetor de features — **18 dimensões**, sistema métrico: velocidade RMS e de pico,
  aceleração de pico e RMS, aceleração RMS de alta frequência, kurtosis, crest factor e
  frequência da componente de pico, nos eixos X e Z (16), mais temperatura em °C e RPM.
- Padronização com `StandardScaler` ajustado **apenas no split de treino** e persistido
  em `artifacts/scaler.joblib`.
- A mesma função de transformação serve ingestão e inferência (sem código duplicado).
""",
        fora_escopo="""
- Redução de dimensionalidade (PCA): 18 dimensões não pressionam o índice HNSW e a
  interpretabilidade por sensor vale mais na entrevista.
- Extração de features a partir de forma de onda bruta — o dataset já entrega agregados.
""",
        decisoes="""
- **Descartar as colunas imperiais e Fahrenheit.** São transformações lineares exatas das
  métricas; carregam zero informação nova e distorcem a distância.
- **`StandardScaler` em vez de min-max.** As caudas são pesadas (kurtosis, crest factor);
  min-max deixaria a escala refém de outliers.
- **RPM entra como feature.** Vibração escala com rotação (F = m·r·ω², conforme o Doc3);
  comparar um evento a 1000 rpm com outro a 0 rpm sem esse eixo produz vizinho sem sentido.
- **Registros com `motor_desligado` (RPM = 0) ficam fora do ajuste do scaler**, mas seguem
  no banco: são estado válido, não amostra representativa de operação.
""",
        contrato="""
```python
FEATURE_COLUMNS: tuple[str, ...]   # ordem estável — define o layout do vetor

def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame: ...
def fit_scaler(df: pd.DataFrame) -> StandardScaler: ...
def to_vector(payload: dict) -> np.ndarray: ...   # usado na inferência
```
""",
        acceptance=[
            ("Redundância comprovada, não presumida",
             "Relatório mostra correlação ≈ 1,0 e razão constante (≈25,4) entre cada par `in_s`/`mm_s`, "
             "e a relação linear entre `temperature_f` e `temperature_c`."),
            ("Vetor final sem duplicidade de grandeza",
             "`FEATURE_COLUMNS` não contém nenhuma coluna `_in_s` nem `temperature_f`."),
            ("Ordem das features é estável",
             "`to_vector` produz o mesmo layout de `build_feature_frame`; teste compara índice a índice."),
            ("Scaler é reutilizado, não reajustado",
             "A inferência carrega `artifacts/scaler.joblib`; alterar o dado de entrada não altera média/desvio salvos."),
            ("Motor desligado não contamina a escala",
             "A média de RPM do scaler ajustado é calculada sem os registros `motor_desligado`."),
            ("Sem NaN no vetor final",
             "A ingestão do dataset completo produz zero valores nulos no vetor; qualquer nulo é reportado com o `id` do registro."),
        ],
        tasks=[
            "Script de auditoria: correlação e razão entre pares de unidade, salvo em `backend/docs/analise/features.md`",
            "Implementar `app/core/features.py` com `FEATURE_COLUMNS` e `build_feature_frame`",
            "Implementar ajuste e persistência do `StandardScaler` excluindo `motor_desligado`",
            "Implementar `to_vector` para o payload de inferência (JSON do §2 do desafio)",
            "Escrever `tests/test_features.py` (ordem estável, ausência de NaN, reuso do scaler)",
            "Documentar em `backend/docs/analise/features.md` cada coluna descartada e o porquê",
        ],
    ),
    # ------------------------------------------------------------------ 004
    dict(
        id="SPEC-FEAT-004",
        title="Ingestão do banner.csv com split temporal",
        epic="infra",
        atende="§2, §3 — dados dos equipamentos monitorados",
        depends=["SPEC-FEAT-002", "SPEC-FEAT-003"],
        contexto="""
166.796 registros precisam ir para o banco já normalizados e vetorizados, com um recorte de
avaliação honesto. O dataset oferece um corte temporal natural: **todo rótulo com prefixo
`new_` ocorre entre 10 e 16/jun/2026, e todo o restante é ≤ 09/jun/2026**. Isso permite um
holdout sem vazamento e sem sorteio artificial.
""",
        escopo="""
- Leitura em chunks de `dados/banner.csv` (evita carregar 31 MB de uma vez sem necessidade).
- Aplicação de SPEC-FEAT-002 (taxonomia) e SPEC-FEAT-003 (features).
- Gravação em `sensor_events`: identificação, timestamp, rótulos bruto e canônico, família,
  `is_problem`, colunas métricas originais e o vetor padronizado em `vector(13)`.
- Marcação de `split`: `train` (≤ 09/jun) e `holdout` (rótulos `new_*`, 10–16/jun).
- Índice HNSW com operador de distância cosseno sobre a coluna vetorial.
- Upsert por `id` — reexecução não duplica.
""",
        fora_escopo="""
- Ingestão em streaming/tempo real (descrita na arquitetura de implantação).
- Uso do `banner.xlsx` — mesma base, formato menos adequado a ETL.
""",
        decisoes="""
- **Split temporal, nunca aleatório.** Sorteio embaralharia amostras da mesma sessão de
  ensaio (coletadas com segundos de diferença) entre treino e teste; o vizinho mais próximo
  seria praticamente o mesmo registro e a acurácia sairia inflada e falsa.
- **`holdout` definido pelo prefixo `new_` E pela data**, não só pelo nome — a regra é
  verificada na ingestão, não assumida. Divergência aborta a carga.
- **Distância cosseno.** Interessa o *padrão* de vibração (forma do vetor), com magnitude já
  tratada pela padronização.
- **Índice HNSW parcial, restrito a `split = 'train'`.** O HNSW do pgvector faz *pós-filtro*:
  encontra os k vizinhos e só depois aplica o `WHERE`. Com índice sobre a tabela inteira e
  consulta partindo de um evento do holdout, os vizinhos mais próximos são os próprios
  registros do holdout (mesma sessão de ensaio) — todos descartados pelo filtro, e a busca
  **retorna vazio**. Comprovado na prática durante a implementação. Como buscar dentro do
  holdout seria vazamento, o filtro entra no próprio índice: corrige o resultado e ainda
  deixa o índice menor.
""",
        contrato="""
```sql
CREATE TABLE sensor_events (
    id              BIGINT PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL,
    raw_fault       TEXT NOT NULL,
    canonical_fault TEXT NOT NULL,
    fault_family    TEXT NOT NULL,
    is_problem      BOOLEAN NOT NULL,
    split           TEXT NOT NULL CHECK (split IN ('train','holdout')),
    rpm             REAL, temperature_c REAL, ...
    features        VECTOR(18) NOT NULL
);

-- Indice PARCIAL: toda busca por similaridade e restrita ao historico.
CREATE INDEX ix_sensor_events_features_hnsw
    ON sensor_events USING hnsw (features vector_cosine_ops)
    WHERE split = 'train';
```
""",
        acceptance=[
            ("Volume íntegro",
             "`SELECT count(*) FROM sensor_events` retorna 166.796 e a contagem por família bate com o relatório de EDA."),
            ("Split sem vazamento temporal",
             "`MAX(created_at)` do split `train` é anterior ao `MIN(created_at)` do split `holdout`."),
            ("Holdout corresponde aos rótulos `new_*`",
             "Todo registro com `split='holdout'` tem `raw_fault` começando com `new_`, e vice-versa."),
            ("Reexecução é idempotente",
             "Rodar a ingestão duas vezes mantém a contagem em 166.796."),
            ("Busca vetorial é rápida",
             "KNN (k=50) sobre os 166k vetores responde em menos de 100 ms com o índice HNSW ativo."),
            ("Busca filtrada retorna resultado",
             "KNN partindo de um evento do holdout, filtrado por `split='train'`, retorna k vizinhos — "
             "nunca lista vazia (regressão do pós-filtro do HNSW)."),
            ("Falha de rótulo interrompe a carga",
             "Um rótulo fora da taxonomia aborta a ingestão com mensagem citando o `id` e o valor bruto."),
        ],
        tasks=[
            "Definir o schema de `sensor_events` em `app/models.py`",
            "Implementar `app/scripts/ingest_csv.py` com leitura em chunks e barra de progresso",
            "Aplicar taxonomia e features; abortar em rótulo desconhecido",
            "Implementar a regra de split e validá-la contra as datas reais",
            "Criar o índice HNSW e medir a latência de KNN antes/depois",
            "Implementar upsert por `id` e testar a reexecução",
            "Gerar `backend/docs/analise/dataset.md` com contagens, período e distribuição por família",
        ],
    ),
    # ------------------------------------------------------------------ 005
    dict(
        id="SPEC-FEAT-005",
        title="Motor de similaridade histórica",
        epic="similaridade",
        atende="§3 — localizar ocorrências passadas com características próximas",
        depends=["SPEC-FEAT-004"],
        contexto="""
É o coração do desafio: dado um evento novo, encontrar no histórico os registros de
comportamento semelhante e devolver o contexto que o desafio pede — quantidade de eventos
similares, distribuição ao longo do tempo, frequência de ocorrência e contexto operacional.
O desafio é explícito: a solução **não depende de classificação prévia de falhas conhecidas**,
e sim de identificação de padrões similares.
""",
        escopo="""
- KNN por distância cosseno no pgvector, restrito a `split = 'train'`.
- Agregações sobre a vizinhança:
  - contagem de eventos similares por família;
  - série temporal das ocorrências (diária);
  - frequência de ocorrência e intervalo médio entre eventos (MTBF empírico);
  - contexto operacional (faixa de RPM e de temperatura dos vizinhos).
- Diagnóstico por **voto ponderado pela similaridade** dos `k` vizinhos.
- Confiança = concentração do voto (a família vencedora domina ou o voto está dividido?).
- **Detecção de fora de distribuição:** se a distância do vizinho mais próximo ultrapassa o
  limiar calibrado, o evento é reportado como *padrão não observado no histórico* — não é
  empurrado para a família mais próxima.
""",
        fora_escopo="""
- Treinar classificador supervisionado. O enunciado pede similaridade, não classificação —
  e um classificador não conseguiria responder "quantos eventos parecidos já aconteceram".
""",
        decisoes="""
- **Voto ponderado por similaridade, não maioria simples.** Com `k` fixo, vizinhos distantes
  votariam com o mesmo peso dos próximos.
- **Limiar de fora de distribuição calibrado empiricamente**, a partir da distribuição de
  distâncias intra-família no split de treino (ex.: percentil alto), e registrado no relatório.
- **Vizinhos vêm só do treino.** Buscar dentro do holdout durante a demonstração seria
  vazamento e invalidaria a métrica apresentada na entrevista.
""",
        contrato="""
```python
class SimilarityResult(BaseModel):
    diagnosed_family: str | None      # None quando fora de distribuição
    confidence: float
    out_of_distribution: bool
    neighbors: list[Neighbor]         # id, created_at, family, similarity
    family_counts: dict[str, int]
    timeline: list[TimelinePoint]     # data, contagem
    frequency_per_day: float
    mean_interval_hours: float | None
    operating_context: OperatingContext   # faixas de rpm e temperatura
```
""",
        acceptance=[
            ("Acerto medido no holdout, não estimado",
             "A família majoritária dos vizinhos é comparada ao rótulo real de todo o split `holdout`; "
             "a taxa e a matriz de confusão por família ficam em `backend/docs/analise/similaridade.md`."),
            ("Evento fora de distribuição não é forçado",
             "Um vetor sintético com valores muito acima da faixa observada retorna "
             "`out_of_distribution = True` e `diagnosed_family = None`."),
            ("Estatísticas conferem com o banco",
             "Para uma família escolhida, `family_counts`, `timeline` e `frequency_per_day` batem com "
             "consulta SQL direta sobre a mesma vizinhança."),
            ("Sem vazamento na busca",
             "Nenhum vizinho retornado tem `split = 'holdout'`."),
            ("Confiança discrimina",
             "Vizinhança unânime produz confiança alta; vizinhança dividida entre duas famílias produz confiança baixa."),
            ("Latência aceitável",
             "`POST /api/events/similar` responde em menos de 300 ms no percentil 95, medido localmente."),
        ],
        tasks=[
            "Implementar `app/ml/similarity.py`: consulta KNN parametrizada por `k`",
            "Implementar voto ponderado e cálculo de confiança",
            "Calibrar o limiar de fora de distribuição a partir das distâncias intra-família",
            "Implementar as agregações (contagem, timeline, frequência, MTBF, contexto operacional)",
            "Script de avaliação sobre o holdout, gerando a matriz de confusão por família",
            "Escrever `tests/test_similarity.py` (vazamento, fora de distribuição, confiança)",
            "Documentar resultados e limitações em `backend/docs/analise/similaridade.md`",
        ],
    ),
    # ------------------------------------------------------------------ 006
    dict(
        id="SPEC-FEAT-006",
        title="Extração de texto e OCR dos documentos",
        epic="similaridade",
        atende="§3 — tratamento dos documentos fornecidos",
        depends=["SPEC-FEAT-001"],
        contexto="""
Foram fornecidos 6 PDFs. **Doc2 a Doc6 têm camada de texto** e já foram identificados:
Doc2 = desalinhamento, Doc3 = desbalanceamento, Doc4 = correias, Doc5 = polias,
Doc6 = cocked rotor (rotor inclinado).

**Doc1.pdf é o caso difícil: 17 páginas e zero caractere extraível.** É um documento gerado
no Word com imagens coladas (metadado `/Creator: Microsoft® Word LTSC`). Ignorá-lo deixaria
um documento entregue pela empresa fora da solução.
""",
        escopo="""
- Detecção automática de camada de texto por documento (densidade de caracteres por página).
- Caminho A (texto): extração com `pypdf`.
- Caminho B (imagem): renderização das páginas com `pypdfium2` → OCR por modelo de visão →
  texto normalizado.
- Normalização comum: junção de hifenização, colapso de espaços, remoção de cabeçalho e
  rodapé repetidos, preservação dos títulos de seção numerados.
- Cada trecho carrega proveniência: `documento`, `página`, `método` (`text` | `ocr`) e,
  no OCR, um score de confiança.
- Cache em disco do OCR — reprocessar não repete chamadas pagas.
""",
        fora_escopo="""
- Interpretar figuras e diagramas técnicos além do texto neles contido.
- Tesseract local (não instalado na máquina; o modelo de visão dá qualidade melhor em
  português e não exige binário externo).
""",
        decisoes="""
- **OCR por modelo de visão em vez de Tesseract.** Sem dependência de binário no Windows,
  melhor resultado em português e em texto dentro de imagem de baixo contraste.
- **OCR é etapa offline, de build.** Roda uma vez, resultado versionado em `artifacts/ocr/`.
  Nenhuma requisição do usuário dispara OCR — a restrição de §5 vale para a operação.
- **Proveniência obrigatória desde a extração.** Citação com página só é possível se o
  número da página for carregado desde o primeiro passo.
""",
        contrato="""
```python
@dataclass
class ExtractedPage:
    document: str
    page: int
    text: str
    method: Literal["text", "ocr"]
    confidence: float | None

def extract_document(path: Path) -> list[ExtractedPage]: ...
```
""",
        acceptance=[
            ("Detecção de camada de texto acerta os 6 arquivos",
             "Doc2–Doc6 são classificados como `text`; Doc1 é classificado como `ocr`."),
            ("Doc1 produz texto útil",
             "As 17 páginas geram texto legível e a falha-alvo do documento é identificada e registrada "
             "em `backend/docs/analise/documentos.md`."),
            ("Proveniência completa",
             "Todo `ExtractedPage` tem `document`, `page` e `method` preenchidos; nenhum trecho anônimo."),
            ("Páginas de OCR ruim são sinalizadas",
             "Página com confiança abaixo do limiar entra no relatório de revisão em vez de ser aceita em silêncio."),
            ("Cache evita retrabalho",
             "Segunda execução da extração não faz nenhuma chamada ao provider de visão."),
            ("Títulos de seção sobrevivem à normalização",
             "Os cabeçalhos numerados (ex.: `3. Sintomas Comuns`) permanecem no texto — são as fronteiras de chunk da SPEC-FEAT-007."),
        ],
        tasks=[
            "Implementar `app/docs/extract.py` com detecção de camada de texto",
            "Implementar caminho de texto com `pypdf` preservando número de página",
            "Implementar renderização de páginas com `pypdfium2` em resolução adequada a OCR",
            "Implementar OCR por modelo de visão, com cache em `artifacts/ocr/` por hash de página",
            "Implementar normalização de texto (hifenização, cabeçalho/rodapé, espaços)",
            "Rodar sobre os 6 PDFs e identificar a falha-alvo do Doc1",
            "Gerar `backend/docs/analise/documentos.md` com um resumo por documento",
        ],
    ),
    # ------------------------------------------------------------------ 007
    dict(
        id="SPEC-FEAT-007",
        title="Indexação semântica dos documentos",
        epic="similaridade",
        atende="§3 — integrar-se à base documental; §5 — executar em estação de trabalho",
        depends=["SPEC-FEAT-006"],
        contexto="""
Os procedimentos seguem estrutura regular ("1. Objetivo", "3. Sintomas Comuns",
"5. Procedimento de Correção", "Validação"). Essa estrutura é uma dádiva para o chunking:
as fronteiras de seção são fronteiras semânticas reais, muito melhores que cortar a cada N
caracteres no meio de um passo de procedimento.
""",
        escopo="""
- Chunking guiado por seção, com limite de tamanho e sobreposição para seções longas.
- Cada chunk guarda: documento, páginas cobertas, título da seção, posição e texto.
- Embeddings **locais** via `fastembed` (ONNX Runtime, modelo multilíngue) — sem rede,
  sem GPU, coerente com a restrição de §5.
- Persistência em `document_chunks` com índice HNSW.
- Metadado do índice (nome do modelo e dimensão) gravado; troca de modelo exige reindexação
  explícita em vez de corromper o índice.
""",
        fora_escopo="""
- Embeddings por API. Manter local reforça a restrição de operação e elimina custo por consulta.
- Reranker dedicado (cross-encoder) — o filtro por família da SPEC-FEAT-010 já elimina a
  maior fonte de ruído.
""",
        decisoes="""
- **Chunking por seção, não por janela fixa.** Um procedimento cortado ao meio gera resposta
  prescritiva incompleta — exatamente o erro mais caro nesta aplicação.
- **`fastembed`/ONNX em vez de `sentence-transformers`/PyTorch.** Dependência de ~50 MB em vez
  de ~2,5 GB, roda em CPU, e sustenta melhor a narrativa de "opera na workstation".
- **Modelo multilíngue.** Documentos e perguntas dos operadores são em português.
""",
        contrato="""
```sql
CREATE TABLE document_chunks (
    id            SERIAL PRIMARY KEY,
    document_id   INT REFERENCES documents(id) ON DELETE CASCADE,
    section       TEXT,
    page_start    INT NOT NULL,
    page_end      INT NOT NULL,
    ordinal       INT NOT NULL,
    content       TEXT NOT NULL,
    embedding     VECTOR(384) NOT NULL
);
```
""",
        acceptance=[
            ("Recuperação faz sentido no domínio",
             "A consulta \"como corrigir desalinhamento de motor\" retorna trechos do Doc2 nas primeiras posições."),
            ("Chunks não cortam procedimento ao meio",
             "Inspeção dos chunks das seções de procedimento mostra passos completos; caso de teste registrado."),
            ("Indexação roda em CPU em tempo aceitável",
             "A indexação completa dos 6 documentos termina em menos de 2 minutos, sem GPU, e o tempo fica no README."),
            ("Reindexação é idempotente",
             "Rodar a indexação duas vezes mantém a contagem de chunks."),
            ("Índice é autodescritivo",
             "O modelo de embedding e a dimensão estão gravados em tabela de metadados; divergência de dimensão é bloqueada com erro claro."),
            ("Sem chamada de rede",
             "A indexação completa com a rede desativada termina com sucesso."),
        ],
        tasks=[
            "Definir schema de `documents` e `document_chunks`",
            "Implementar `app/docs/chunking.py` com detecção de seções numeradas + fallback por tamanho",
            "Implementar `app/rag/embeddings.py` encapsulando o `fastembed`",
            "Implementar `app/scripts/ingest_docs.py` (extrai → chunka → embeda → grava)",
            "Criar índice HNSW e tabela de metadados do índice",
            "Testar recuperação com 5 consultas-sonda, uma por documento conhecido",
            "Medir e registrar o tempo de indexação em CPU",
        ],
    ),
    # ------------------------------------------------------------------ 008
    dict(
        id="SPEC-FEAT-008",
        title="Mapa falha→documento e gate de cobertura",
        epic="similaridade",
        atende="§3 — regra explícita de recusa quando não há documento",
        depends=["SPEC-FEAT-002", "SPEC-FEAT-007"],
        contexto="""
O enunciado é literal: *"O sistema deve se deter unicamente a problemas que possuem
documentos, caso contrário deve reportar que ainda não existe o problema identificado e
sugerir ao usuário para registrar um novo documento para o defeito."*

Isso é regra de negócio, e regra de negócio não se implementa como pedido educado no prompt.

Cobertura conhecida pela leitura dos PDFs:

| Família | Documento | Situação |
| --- | --- | --- |
| `desalinhamento` | Doc2 | coberto |
| `desbalanceamento` | Doc3 | coberto |
| `correia` | Doc4 | coberto |
| `polia` | Doc5 | coberto |
| `cocked_rotor` | Doc6 | coberto |
| `rolamento` | Doc1 — a confirmar via OCR (SPEC-FEAT-006) | a confirmar |
| `eccentric_rotor`, `ventoinha`, `falta_fase` | — | **descoberto** |

A família `rolamento` sozinha soma ~37 mil registros — a maior massa do dataset. Se o Doc1
não a cobrir, o caso de recusa é **real**, não fabricado para a demonstração.
""",
        escopo="""
- Tabela `fault_document_coverage` ligando família canônica → documentos que a cobrem.
- Montagem por âncoras semânticas (consultas-sonda por família contra o índice) **com
  revisão explícita registrada** — não por inferência do LLM.
- Função `check_coverage(family) -> Coverage` chamada **antes** de qualquer chamada ao LLM.
- Resposta estruturada de recusa quando não há cobertura, incluindo o que se sabe do evento
  (família diagnosticada, número de ocorrências similares) e a orientação de registrar documento.
- Recálculo automático da cobertura após upload de documento (SPEC-FEAT-014).
""",
        fora_escopo="""
- Deixar o LLM decidir se tem informação suficiente. É justamente o comportamento que a
  entrevista avalia como alucinação.
""",
        decisoes="""
- **Gate determinístico em código, antes do LLM.** Se não há cobertura, o modelo sequer é
  chamado — não há como alucinar o que não foi perguntado.
- **Mapa revisado por humano e versionado.** Auditável e defensável na entrevista.
- **Recusa é informativa, não um beco sem saída.** Devolve a análise estatística que o
  sistema *tem* e pede o documento que falta.
""",
        contrato="""
```python
class Coverage(BaseModel):
    family: str
    is_covered: bool
    documents: list[DocumentRef]
    reason: Literal["covered", "no_document", "state_not_problem", "out_of_distribution"]
```
""",
        acceptance=[
            ("Gate roda antes do LLM",
             "Com família sem cobertura, o log da requisição não registra nenhuma chamada ao provider de LLM."),
            ("Recusa segue o texto do enunciado",
             "A resposta informa que não há documento para o problema identificado e sugere registrar um novo documento."),
            ("Recusa ainda entrega valor",
             "O payload de recusa traz a família diagnosticada, a contagem de eventos similares e a distribuição temporal."),
            ("Estado não vira prescrição",
             "Evento diagnosticado como `normal` ou `motor_desligado` retorna `reason = state_not_problem`, sem prescrição."),
            ("Fora de distribuição é distinguido de falta de documento",
             "Evento fora de distribuição retorna `reason = out_of_distribution`, com mensagem diferente da de documento ausente."),
            ("Cobertura se atualiza sozinha",
             "Após upload de documento para uma família descoberta, `check_coverage` passa a retornar `is_covered = True` sem reiniciar a API."),
            ("Mapa é auditável",
             "`backend/docs/analise/cobertura.md` lista cada família, o documento vinculado e a evidência que sustentou o vínculo."),
        ],
        tasks=[
            "Confirmar a falha-alvo do Doc1 após o OCR e fechar a tabela de cobertura",
            "Definir schema de `fault_document_coverage`",
            "Implementar consultas-sonda por família e registrar a evidência de cada vínculo",
            "Implementar `app/rag/coverage.py` com `check_coverage` e os quatro motivos de retorno",
            "Integrar o gate ao fluxo de análise, antes do retriever e do LLM",
            "Escrever `tests/test_coverage.py` cobrindo os quatro motivos",
            "Gerar `backend/docs/analise/cobertura.md`",
        ],
    ),
    # ------------------------------------------------------------------ 009
    dict(
        id="SPEC-FEAT-009",
        title="Provider de LLM plugável",
        epic="rag",
        atende="§5 — restrição de infraestrutura de operação",
        depends=["SPEC-FEAT-001"],
        contexto="""
A entrega usa API externa (OpenAI ou DeepSeek). Os dois falam o mesmo protocolo, então uma
única implementação cobre ambos trocando `base_url` e `model`. A camada de abstração
também é o ponto onde um provider local (servidor compatível com OpenAI, rodando modelo
quantizado nos 16 GB de VRAM de §5) entra sem tocar em regra de negócio.
""",
        escopo="""
- Interface `LLMProvider` com `complete(messages, **opts)` e `vision(images, prompt)`.
- Implementação única sobre o SDK `openai`, parametrizada por `.env`.
- Timeout, retry com backoff exponencial (`tenacity`) e teto de tokens.
- Log estruturado por chamada: modelo, tokens de entrada/saída, latência e custo estimado.
- Degradação controlada: falha do provider vira erro de negócio tratado, não 500 com stack trace.
""",
        fora_escopo="""
- Servir modelo local nesta entrega — o caminho fica documentado e o código, preparado.
- Fine-tuning.
""",
        decisoes="""
- **Um cliente, dois providers.** DeepSeek é compatível com o protocolo da OpenAI; duplicar
  implementação seria custo sem retorno.
- **Visão só onde existe.** O OCR (SPEC-FEAT-006) exige visão; o provider declara a capacidade
  e o pipeline falha cedo, com mensagem clara, se o modelo configurado não a tiver.
- **Temperatura baixa.** A tarefa é reproduzir procedimento técnico, não redigir com criatividade.
""",
        contrato="""
```python
class LLMProvider(Protocol):
    name: str
    supports_vision: bool
    def complete(self, messages: list[Message], *, max_tokens: int, temperature: float) -> LLMResponse: ...
    def vision(self, images: list[bytes], prompt: str) -> LLMResponse: ...

def get_provider() -> LLMProvider: ...   # resolvido por LLM_PROVIDER no .env
```
""",
        acceptance=[
            ("Troca de provider é só configuração",
             "Alternar `LLM_PROVIDER` entre `openai` e `deepseek` no `.env` muda o provider efetivo sem alterar código de negócio."),
            ("Falta de capacidade falha cedo",
             "Configurar um modelo sem visão e disparar o OCR produz erro na inicialização do pipeline, com mensagem nomeando a capacidade ausente."),
            ("Indisponibilidade não derruba a API",
             "Com credencial inválida, `/api/chat` retorna erro de negócio com mensagem acionável e a API continua respondendo `/api/stats/overview`."),
            ("Retry é limitado e observável",
             "Falha transitória é repetida com backoff até o teto configurado; cada tentativa aparece no log."),
            ("Consumo é rastreável",
             "Cada chamada registra modelo, tokens de entrada/saída e latência em log estruturado."),
        ],
        tasks=[
            "Implementar `app/llm/provider.py` com o protocolo e a implementação OpenAI-compatível",
            "Adicionar resolução por `.env` e declaração de capacidades (visão)",
            "Adicionar timeout, retry com `tenacity` e teto de tokens",
            "Implementar log estruturado de uso (tokens, latência, custo estimado)",
            "Mapear exceções do SDK para erros de negócio da API",
            "Testar com provider inválido e confirmar degradação controlada",
        ],
    ),
    # ------------------------------------------------------------------ 010
    dict(
        id="SPEC-FEAT-010",
        title="Recuperação de contexto para prescrição",
        epic="rag",
        atende="§3 — consultar manuais e procedimentos relacionados",
        depends=["SPEC-FEAT-007", "SPEC-FEAT-008"],
        contexto="""
Busca puramente semântica erra de um jeito específico e perigoso neste domínio: os seis
documentos compartilham vocabulário quase idêntico ("vibração elevada", "aquecimento nos
mancais", "desgaste de rolamentos", "afrouxamento de parafusos"). Uma consulta sobre correia
recupera com folga trechos de desbalanceamento. A resposta sairia fluente, citada — e errada.
""",
        escopo="""
- Busca híbrida: **filtro rígido** pelos documentos que cobrem a família diagnosticada
  (SPEC-FEAT-008) + ranqueamento semântico dentro desse subconjunto.
- Priorização das seções acionáveis (procedimento, correção, validação) sobre as
  introdutórias, quando a intenção é prescritiva.
- Limite de contexto por orçamento de tokens, mantendo chunks inteiros.
- Cada trecho retornado carrega documento, página, seção e score.
""",
        fora_escopo="""
- Busca cross-família ("veja também documentos relacionados") — contraria a regra de §3.
""",
        decisoes="""
- **Filtro por família é rígido, não um reforço de score.** Um peso alto ainda deixaria passar
  documento errado; o corte duro elimina a classe inteira de erro.
- **Ordenação por seção depende da intenção.** Pergunta de diagnóstico privilegia "Sintomas";
  pedido de correção privilegia "Procedimento".
""",
        contrato="""
```python
class RetrievedChunk(BaseModel):
    document: str
    page_start: int
    page_end: int
    section: str | None
    content: str
    score: float

def retrieve(query: str, family: str, *, budget_tokens: int) -> list[RetrievedChunk]: ...
```
""",
        acceptance=[
            ("Nenhum vazamento entre famílias",
             "Consulta sobre falha de correia retorna apenas trechos do Doc4; nenhum chunk do Doc3 aparece."),
            ("Seções acionáveis vêm primeiro em pedido de correção",
             "Para \"como corrigir\", os três primeiros trechos pertencem a seções de procedimento/correção."),
            ("Orçamento de tokens respeitado sem truncar chunk",
             "O contexto montado fica dentro do orçamento e nenhum chunk aparece cortado ao meio."),
            ("Proveniência completa",
             "Todo `RetrievedChunk` tem documento e faixa de páginas — pré-requisito da citação."),
            ("Família sem cobertura não chega aqui",
             "Chamar `retrieve` com família descoberta levanta erro; o gate deveria ter interrompido antes."),
        ],
        tasks=[
            "Implementar `app/rag/retriever.py` com filtro por documentos da cobertura",
            "Implementar classificação leve de intenção (diagnóstico × correção)",
            "Implementar priorização por seção conforme a intenção",
            "Implementar montagem de contexto por orçamento de tokens",
            "Escrever `tests/test_retriever.py` com o caso correia × desbalanceamento",
            "Medir a latência da recuperação e incluir no log de etapas",
        ],
    ),
    # ------------------------------------------------------------------ 011
    dict(
        id="SPEC-FEAT-011",
        title="Geração prescritiva com citações",
        epic="rag",
        atende="§3 — demonstrar como corrigir o problema ocorrido",
        depends=["SPEC-FEAT-005", "SPEC-FEAT-009", "SPEC-FEAT-010"],
        contexto="""
A saída precisa ser **prescritiva**, não descritiva: o operador quer saber o que fazer, em que
ordem, e como validar que o problema foi resolvido. Texto corrido dificulta a leitura em chão
de fábrica e dificulta a verificação automática de embasamento.
""",
        escopo="""
Resposta estruturada, com campos fixos:

| Campo | Conteúdo |
| --- | --- |
| `diagnostico` | Família identificada e o raciocínio a partir dos vizinhos históricos |
| `evidencia` | Quantidade de eventos similares, período, frequência e contexto operacional |
| `inspecao` | Verificações a fazer antes de intervir, cada uma com citação |
| `correcao` | Passos de correção ordenados, cada um com citação |
| `validacao` | Critérios para confirmar que a falha foi corrigida |
| `citacoes` | Lista de `{documento, página, seção}` referenciada no texto |
| `avisos` | Limitações e pontos que exigem julgamento humano |

Prompt em português, com instrução explícita de responder **somente** a partir do contexto
recuperado e de se abster quando o contexto não sustentar a afirmação.
""",
        fora_escopo="""
- Estimar custo, tempo de parada ou peças — não há dado que sustente.
- Emitir ordem de serviço em sistema de manutenção.
""",
        decisoes="""
- **Saída estruturada, não texto livre.** Permite verificar embasamento por campo
  (SPEC-FEAT-012), renderizar bem no frontend e reduzir divagação.
- **Citação por passo, não por resposta.** Uma citação global no rodapé não prova que
  *aquele* passo veio do manual.
- **Evidência estatística e prescrição textual em campos separados.** Os números vêm do
  banco (SPEC-FEAT-005), não do modelo; separar deixa explícito o que o LLM não inventou.
""",
        contrato="""
```python
class PrescriptiveAnswer(BaseModel):
    diagnostico: str
    evidencia: EvidenceBlock          # preenchido por código, não pelo LLM
    inspecao: list[ActionStep]        # texto + citações
    correcao: list[ActionStep]
    validacao: list[ActionStep]
    citacoes: list[Citation]
    avisos: list[str]
```
""",
        acceptance=[
            ("Todo passo é citado",
             "Nenhum item de `inspecao`, `correcao` ou `validacao` fica sem ao menos uma citação."),
            ("Citações são verificáveis",
             "Cada citação aponta para um documento e página existentes; o trecho correspondente é recuperável."),
            ("Números não vêm do modelo",
             "Os valores de `evidencia` batem exatamente com a resposta de `/api/events/similar` para o mesmo evento."),
            ("Sem contexto, o modelo não é chamado",
             "Recuperação vazia resulta em resposta de recusa, sem nenhuma chamada ao provider."),
            ("Resposta em português técnico",
             "As respostas usam a terminologia dos manuais (mancal, acoplamento, crest factor), sem mistura de idiomas."),
            ("Formato sempre válido",
             "Sobre 20 execuções variadas, o parse do schema não falha; falha de formato dispara uma reexecução e é registrada."),
        ],
        tasks=[
            "Escrever o prompt de sistema em português, com regra de abstenção",
            "Implementar `app/rag/generator.py` com saída estruturada e validação por schema",
            "Montar `evidencia` a partir do resultado de similaridade (código, não LLM)",
            "Implementar retentativa em caso de saída fora do schema",
            "Implementar extração e deduplicação da lista de citações",
            "Avaliar 20 casos variados e registrar os resultados em `backend/docs/analise/geracao.md`",
        ],
    ),
    # ------------------------------------------------------------------ 012
    dict(
        id="SPEC-FEAT-012",
        title="Guarda anti-alucinação",
        epic="rag",
        atende="Critério de entrevista: \"Alucinação do modelo\"",
        depends=["SPEC-FEAT-008", "SPEC-FEAT-011"],
        contexto="""
"Alucinação do modelo" é critério **explícito** de avaliação da entrevista. Confiar apenas na
instrução do prompt é frágil e indefensável sob questionamento. A defesa aqui é em
profundidade, com um caso de teste para cada camada.
""",
        escopo="""
**Camada 1 — Gate determinístico (SPEC-FEAT-008).** Sem documento, o LLM não é chamado.

**Camada 2 — Prompt restritivo.** Contexto delimitado, instrução de responder somente a
partir dele e de declarar quando a informação não está disponível.

**Camada 3 — Verificação de embasamento pós-geração.** Cada afirmação técnica gerada é
conferida contra os trechos recuperados; afirmação sem suporte é removida da resposta e
registrada em `avisos`.

**Camada 4 — Recusa de fora de domínio.** Pergunta alheia à manutenção industrial é recusada
com educação e sem tentativa de resposta.

Suíte adversarial versionada, com o resultado publicado no README.
""",
        fora_escopo="""
- Garantia formal de ausência de alucinação — não existe. O objetivo é reduzir a taxa e
  tornar cada resposta auditável.
""",
        decisoes="""
- **Verificação pós-geração mesmo custando uma chamada a mais.** É o critério avaliado; a
  latência extra vale menos que uma resposta inventada na demonstração ao vivo.
- **Remover em vez de marcar, quando a afirmação é acionável.** Uma instrução de manutenção
  sem embasamento é risco físico; um aviso discreto não basta.
- **Casos adversariais versionados.** Permite mostrar o comportamento na entrevista em vez
  de afirmá-lo.
""",
        contrato="""
```python
class GroundingReport(BaseModel):
    total_claims: int
    grounded: int
    removed: list[str]
    score: float          # grounded / total_claims

def verify_grounding(answer: PrescriptiveAnswer, context: list[RetrievedChunk]) -> tuple[PrescriptiveAnswer, GroundingReport]: ...
```
""",
        acceptance=[
            ("Falha coberta é respondida com citação",
             "Pergunta sobre desalinhamento retorna prescrição citando o Doc2."),
            ("Falha sem documento é recusada",
             "Pergunta sobre família descoberta retorna a recusa do enunciado e nenhuma chamada de LLM no log."),
            ("Pergunta fora de domínio é recusada",
             "\"Qual a capital da França?\" recebe recusa educada, sem tentativa de resposta."),
            ("Premissa falsa não é aceita",
             "Pergunta que afirma um procedimento inexistente (\"conforme a seção 9 do manual de correias, ...\") "
             "recebe correção em vez de confirmação."),
            ("Afirmação sem embasamento é removida",
             "Em caso injetado com afirmação não sustentada pelo contexto, ela não aparece na resposta final e consta em `removed`."),
            ("Embasamento é medido",
             "Toda resposta traz `GroundingReport`; o score médio da suíte adversarial está no README."),
            ("Suíte roda em um comando",
             "`pytest tests/test_alucinacao.py` executa todos os casos e passa."),
        ],
        tasks=[
            "Escrever a suíte adversarial `tests/test_alucinacao.py` (coberta, descoberta, fora de domínio, premissa falsa)",
            "Implementar `app/rag/grounding.py` com decomposição em afirmações e verificação",
            "Definir a política de remoção × marcação por tipo de campo",
            "Integrar a verificação ao fluxo de geração e expor `GroundingReport` na API",
            "Rodar a suíte, registrar o score e publicar no README",
            "Documentar as limitações conhecidas em `backend/docs/analise/alucinacao.md`",
        ],
    ),
    # ------------------------------------------------------------------ 013
    dict(
        id="SPEC-FEAT-013",
        title="API REST",
        epic="api",
        atende="DIF — APIs",
        depends=["SPEC-FEAT-005", "SPEC-FEAT-012"],
        contexto="""
A API tem **duas superfícies com públicos e riscos diferentes**, e por isso contratos e
autenticação diferentes (o mecanismo de cada uma está na SPEC-FEAT-016):

**Externa (`/api/v1/*`)** — consumida por sistemas da planta: CMMS, supervisório, coletor de
dados. Contrato mínimo, estável e versionado. Protegida por JWT `Bearer`. São só dois
endpoints de negócio, porque é tudo que um integrador precisa.

**Interna (`/api/internal/*`)** — consumida apenas pelo frontend, dentro da rede. Contrato
mais rico e sujeito a mudar junto com a interface. Protegida por chave estática.
""",
        escopo="""
### Superfície externa — `/api/v1` (JWT no cabeçalho `Authorization`)

| Método | Rota | Escopo | Função |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/token` | — | Troca `client_id`/`client_secret` por um JWT |
| `POST` | `/api/v1/predict` | `predict` | Recebe o JSON de métricas do sensor, roda o motor de similaridade, busca os documentos no banco vetorial, chama o LLM e devolve um JSON consolidado |
| `POST` | `/api/v1/upload_doc` | `upload` | Envia novo documento orientativo (PDF/texto), processa e injeta no banco vetorial |

O payload de `/api/v1/predict` aceita exatamente o JSON de exemplo do §2 do desafio.

### Superfície interna — `/api/internal` (cabeçalho `X-Internal-Key`)

| Método | Rota | Função |
| --- | --- | --- |
| `POST` | `/api/internal/events/similar` | Somente similaridade, sem LLM |
| `POST` | `/api/internal/chat` | Chat prescritivo com histórico e citações |
| `GET` | `/api/internal/stats/overview` | KPIs do dashboard |
| `GET` | `/api/internal/stats/timeline` | Distribuição temporal por família |
| `GET` | `/api/internal/faults` | Famílias canônicas e status de cobertura |
| `GET` | `/api/internal/documents` | Documentos indexados e estado da indexação |
| `GET` | `/api/internal/events/sample` | Amostra do holdout `new_*` para demonstração |

### Pública

| Método | Rota | Função |
| --- | --- | --- |
| `GET` | `/api/health` | Estado de banco, índice e provider |
""",
        fora_escopo="""
- Cadastro de usuários finais — a autenticação é máquina-a-máquina.
- Limite de requisições por cliente (rate limiting) — citado na arquitetura como próximo passo.
""",
        decisoes="""
- **Superfície externa enxuta: `/predict` e `/upload_doc`.** Um integrador industrial precisa
  de duas operações — perguntar sobre um evento e ensinar um documento novo. Expor as dez
  rotas internas ao mundo criaria compromisso de compatibilidade sobre coisas que existem
  só para a interface.
- **`/api/v1` versionado só na superfície externa.** O contrato externo tem cliente de
  terceiro e não pode quebrar; o interno muda junto com o frontend, no mesmo repositório.
- **`/events/similar` separado do `/predict`.** Permite demonstrar a camada de dados sem
  custo nem latência de LLM, e deixa evidente na entrevista o que é estatística e o que é geração.
- **Tempo por etapa em toda resposta.** Similaridade, recuperação, geração e verificação —
  transparência e material de discussão sobre desempenho.
""",
        contrato="""
```http
POST /api/v1/auth/token
{ "client_id": "...", "client_secret": "..." }
200 → { "access_token": "...", "token_type": "bearer", "expires_in": 3600, "scopes": [...] }

POST /api/v1/predict
Authorization: Bearer <token>
{ "id": 114387, "created_at": "...", "z_rms_velocity_mm_s": 1.517, ..., "rpm": 1000.0 }
200 → { diagnosis, evidence, coverage, prescription | refusal, grounding, timings }

POST /api/v1/upload_doc      (multipart: file, fault_family, title)
Authorization: Bearer <token>
201 → { document_id, status, chunks, pages, method, coverage_updated }

POST /api/internal/chat
X-Internal-Key: <chave>
```
""",
        acceptance=[
            ("OpenAPI publicada e separada por superfície",
             "`/docs` lista as rotas com schemas de entrada e saída, agrupadas por tag (`v1` e `internal`)."),
            ("Payload do enunciado funciona sem adaptação",
             "O JSON de exemplo do §2 é aceito por `/api/v1/predict` exatamente como está."),
            ("`/predict` devolve JSON consolidado",
             "Uma única resposta traz diagnóstico, evidência estatística, cobertura documental, "
             "prescrição (ou recusa) e citações — sem exigir chamadas extras."),
            ("`/upload_doc` injeta no banco vetorial",
             "Após o upload, os chunks do documento novo aparecem em `document_chunks` e passam a ser recuperáveis."),
            ("Campo faltante gera erro útil",
             "Payload sem uma feature obrigatória retorna 422 nomeando o campo."),
            ("Erro de negócio não vaza stack trace",
             "Provider indisponível retorna código e mensagem acionáveis, com o stack trace apenas no log."),
            ("Tempos por etapa presentes",
             "Toda resposta de `/predict` traz `timings` com similaridade, recuperação, geração e verificação."),
            ("CORS liberado para o frontend",
             "O frontend em `localhost` chama a API pelo navegador sem erro de CORS."),
            ("Health é honesto",
             "`/api/health` reporta falha quando o banco está fora, em vez de responder OK."),
        ],
        tasks=[
            "Definir os schemas Pydantic de request e response em `app/schemas.py`",
            "Implementar o roteador externo `app/api/v1/` (`auth`, `predict`, `upload_doc`)",
            "Implementar o roteador interno `app/api/internal/` (events, chat, stats, documents)",
            "Implementar middleware de tempo por etapa e log estruturado por requisição",
            "Implementar tratamento de exceções de negócio",
            "Configurar CORS a partir do `.env`",
            "Implementar `/api/health` com verificação real de banco, índice e provider",
            "Criar coleção de exemplos (`.http`) com uma chamada por rota, incluindo o fluxo de token",
        ],
    ),
    # ------------------------------------------------------------------ 014
    dict(
        id="SPEC-FEAT-014",
        title="Registro de novo documento de falha",
        epic="api",
        atende="§3 — sugerir ao usuário registrar um novo documento para o defeito",
        depends=["SPEC-FEAT-007", "SPEC-FEAT-008"],
        contexto="""
O enunciado não pede só recusar: pede **sugerir ao usuário registrar um novo documento**.
Fechar esse ciclo transforma a recusa em fluxo de trabalho, e dá a demonstração mais forte
da entrevista — a mesma pergunta, recusada antes e respondida depois do upload.
""",
        escopo="""
- `POST /api/documents` com upload de PDF + família de falha alvo.
- Pipeline reaproveitado: extração/OCR (SPEC-FEAT-006) → chunking + embeddings (SPEC-FEAT-007)
  → vínculo de cobertura (SPEC-FEAT-008).
- Estado de indexação consultável (`pending` → `processing` → `indexed` | `failed`).
- Deduplicação por hash de conteúdo — reenviar o mesmo arquivo não duplica chunks.
- Recálculo da cobertura ao final, sem reiniciar a API.
""",
        fora_escopo="""
- Fluxo de aprovação/revisão editorial do documento.
- Versionamento de documento (substituir revisão anterior).
""",
        decisoes="""
- **Indexação síncrona nesta entrega.** Os documentos são pequenos (~10 páginas); uma fila
  (Celery/RQ) adicionaria infraestrutura sem ganho perceptível. A alternativa assíncrona fica
  registrada no documento de arquitetura.
- **Família informada pelo usuário, não inferida.** Quem registra sabe a que defeito o
  documento se refere; inferir seria introduzir erro justamente no mecanismo antialucinação.
""",
        contrato="""
```
POST /api/documents  (multipart)
  file: application/pdf
  fault_family: str
  title: str

201 → { document_id, status, chunks, pages, method, coverage_updated: bool }
```
""",
        acceptance=[
            ("Ciclo completo demonstrável",
             "Pergunta sobre família descoberta é recusada; após o upload de documento para ela, a mesma "
             "pergunta é respondida com citação ao documento novo."),
            ("Cobertura atualiza sem reinício",
             "`GET /api/faults` reflete a nova cobertura na chamada seguinte ao upload."),
            ("Reenvio não duplica",
             "Enviar o mesmo arquivo duas vezes mantém a contagem de chunks e retorna referência ao documento existente."),
            ("Arquivo inválido é rejeitado",
             "Upload de arquivo não-PDF ou corrompido retorna 400 com mensagem clara e não deixa registro parcial."),
            ("PDF sem camada de texto também funciona",
             "Um PDF escaneado passa pelo caminho de OCR e é indexado."),
            ("Estado é consultável",
             "`GET /api/documents` mostra o estado de indexação e, em caso de falha, o motivo."),
        ],
        tasks=[
            "Implementar a rota de upload com validação de tipo e tamanho",
            "Reaproveitar o pipeline de extração/chunking/embedding para um documento avulso",
            "Implementar deduplicação por hash de conteúdo",
            "Implementar máquina de estados de indexação e persistência do erro",
            "Implementar recálculo de cobertura e invalidação de cache",
            "Testar o ciclo recusa → upload → resposta ponta a ponta",
            "Registrar o roteiro dessa demonstração em `backend/docs/analise/demo.md`",
        ],
    ),
    # ------------------------------------------------------------------ 017
    dict(
        id="SPEC-FEAT-017",
        title="Ingestão de leituras do chão de fábrica",
        epic="api",
        atende="§2 — dados enviados continuamente ao banco corporativo; DIF — Integrações em ambiente industrial",
        depends=["SPEC-FEAT-002", "SPEC-FEAT-003", "SPEC-FEAT-016"],
        contexto="""
A seção 2 do enunciado descreve o fluxo real: os sensores enviam leituras
**continuamente** para o banco corporativo, e a equipe de IA consome esse banco.

A entrega inicial tinha só a porta de saída. `/predict` consulta o histórico mas
não escreve nele, e a única forma de alimentar a base era a carga em lote do CSV.
Um sistema instalado na planta não tem como funcionar assim: a máquina gera
leitura o tempo todo, e uma falha nova precisa entrar na base para virar
histórico das próximas.
""",
        escopo="""
- `POST /api/v1/events` com escopo próprio `ingest`.
- Aceita o JSON de exemplo do §2 **literalmente**, incluindo `fault`, `id`,
  `created_at` e as colunas em unidade imperial.
- Uma leitura ou lote de até 1000.
- Normalização pela taxonomia canônica (SPEC-FEAT-002) e cálculo do vetor
  (SPEC-FEAT-003), no mesmo caminho da carga em lote.
- Upsert por `id`: reenvio por falha de rede não duplica, e o operador pode
  anotar depois uma leitura que chegou sem rótulo.
- `analisar: true` devolve também o diagnóstico da última leitura do lote.
- Novo valor de `split`: `producao`.
""",
        fora_escopo="""
- Ingestão por MQTT ou OPC-UA — descrita no documento de arquitetura; aqui o
  contrato é HTTP, que qualquer coletor moderno fala.
- Fila de mensagens entre o coletor e a API.
""",
        decisoes="""
- **Leitura sem rótulo é gravada, não recusada.** O sensor mede o tempo todo; o
  operador classifica depois, ou nunca. Descartar a medição por falta da anotação
  seria jogar fora o dado mais caro para preservar o metadado. Ela entra com
  `fault_family` nulo e fica **fora** do índice de similaridade — sem condição
  anotada, não há como votar.
- **Rótulo fora da taxonomia recebe o mesmo tratamento**, e volta em
  `rotulos_desconhecidos` para alguém decidir se vira família nova. A ingestão em
  lote não pode parar por causa de um rótulo. Isso difere da carga inicial
  (`scripts/ingest_csv`), que **aborta**: lá é arquivo fechado, revisável antes de
  rodar de novo; aqui é fluxo contínuo.
- **Split `producao` participa da busca por similaridade.** O índice HNSW parcial
  passou de `WHERE split = 'train'` para
  `WHERE split <> 'holdout' AND fault_family IS NOT NULL`. Leituras novas viram
  histórico — é o objetivo do sistema; o holdout continua isolado para a
  avaliação não ser corrompida.
- **`excluir_id` na busca.** Uma leitura recém-gravada apareceria como vizinha de
  si mesma, com similaridade 1,0, dominando a votação. O identificador é excluído
  da consulta quando a análise acompanha a ingestão.
- **Escopo `ingest` separado de `predict`.** Quem só consulta não escreve na base
  que alimenta o diagnóstico dos outros.
""",
        contrato="""
```http
POST /api/v1/events
Authorization: Bearer <token com escopo ingest>

{ "leituras": [ { ...JSON do §2 do enunciado... } ], "analisar": false }

201 → {
  gravadas, anotadas, atualizadas,
  leituras: [{ id, condicao_bruta, condicao_canonica, familia, anotada, ja_existia }],
  rotulos_desconhecidos: [],
  analise: PredictResponse | null
}
```
""",
        acceptance=[
            ("O JSON do enunciado é aceito sem adaptação",
             "O exemplo do §2 copiado literalmente retorna 201, e `cocked_rotor_2` é normalizado para a família `cocked_rotor`."),
            ("Reenvio atualiza em vez de duplicar",
             "Enviar o mesmo `id` duas vezes retorna `atualizadas = 1` e não cria segundo registro."),
            ("Leitura sem rótulo é preservada",
             "Payload sem `fault` retorna 201 com `anotada = false` e `familia = null`."),
            ("Rótulo desconhecido não derruba o lote",
             "Um rótulo fora da taxonomia retorna 201, o rótulo aparece em `rotulos_desconhecidos` e a leitura fica não anotada."),
            ("Leitura sem rótulo não vira vizinha",
             "Nenhum registro com `fault_family` nulo aparece entre os vizinhos de uma busca."),
            ("A leitura recém-gravada não é vizinha de si mesma",
             "Com `analisar: true`, o `id` recém-inserido não consta na lista de vizinhos."),
            ("Identificador é gerado quando ausente",
             "Um lote de 3 leituras sem `id` recebe três identificadores distintos."),
            ("Escopo é exigido",
             "Token emitido apenas com escopo `predict` recebe 403 ao enviar leitura."),
            ("Lote vazio é recusado",
             "`{\"leituras\": []}` retorna 422."),
        ],
        tasks=[
            "Tornar `canonical_fault`, `fault_family` e `is_problem` nulos no modelo",
            "Adicionar o valor `producao` à restrição de `split`",
            "Reescrever o índice HNSW parcial para `split <> 'holdout' AND fault_family IS NOT NULL`",
            "Ajustar as consultas do repositório ao novo critério de histórico",
            "Implementar `excluir_id` em `buscar_vizinhos`, `similarity` e `pipeline`",
            "Implementar `schemas/ingest.py` com o payload do enunciado",
            "Implementar `services/ingestion.py` com upsert e tolerância a rótulo desconhecido",
            "Implementar `POST /api/v1/events` com o escopo `ingest`",
            "Adicionar o escopo `ingest` à emissão de token",
            "Escrever os testes de aceite em `tests/test_api.py`",
        ],
    ),
    # ------------------------------------------------------------------ 016
    dict(
        id="SPEC-FEAT-016",
        title="Autenticação: JWT externo e chave interna",
        epic="api",
        atende="DIF — APIs, Integrações em ambiente industrial",
        depends=["SPEC-FEAT-001"],
        contexto="""
As duas superfícies da API (SPEC-FEAT-013) têm riscos diferentes e recebem mecanismos
diferentes. Em ambiente industrial, uma API de manutenção exposta sem autenticação é um
problema sério: `/upload_doc` escreve na base de conhecimento que orienta intervenção
física em equipamento. Quem consegue injetar documento consegue influenciar o que o
sistema recomenda ao técnico.
""",
        escopo="""
### Externo — JWT `Bearer`

- `POST /api/v1/auth/token`: troca `client_id` + `client_secret` (do `.env`) por um JWT
  assinado em HS256, com expiração curta (padrão 60 min).
- Token carrega `sub`, `iss`, `exp` e **escopos**: `predict` e `upload`.
- `/api/v1/predict` exige escopo `predict`; `/api/v1/upload_doc` exige escopo `upload`.
- Erros distintos e informativos: token ausente, expirado, inválido e sem escopo.

### Interno — chave estática

- Cabeçalho `X-Internal-Key`, comparado com `INTERNAL_API_KEY` do `.env`.
- A chave vive no proxy do container do frontend e é injetada no cabeçalho ali;
  **nunca é enviada ao navegador**.

### Transversal

- Comparação de segredos em tempo constante (`hmac.compare_digest`).
- `Settings.require_auth()` impede a API de subir sem segredo configurado.
- `app/scripts/gen_secrets.py` gera os valores; não escreve no `.env` automaticamente.
""",
        fora_escopo="""
- OAuth2 completo com refresh token e revogação — desproporcional para dois clientes de
  máquina; o caminho fica registrado na arquitetura.
- Login de usuário final, papéis e permissões por pessoa.
- Rotação automática de segredos.
""",
        decisoes="""
- **Escopo por endpoint, não um token que abre tudo.** Um coletor de dados que só consulta
  não deve conseguir injetar documento na base de conhecimento — é o caminho mais direto
  para envenenar as recomendações entregues ao técnico.
- **Chave estática no interno em vez de JWT.** O frontend não é um cliente autenticável: a
  chave fica no proxy do servidor, nunca no navegador. Emissão e renovação de token ali
  seriam cerimônia sem ganho de segurança real.
- **HS256 com segredo compartilhado, não RS256.** Emissor e verificador são o mesmo serviço;
  par de chaves assimétricas só faria sentido com emissor separado.
- **Falhar na inicialização sem segredo.** Uma API industrial no ar sem autenticação é pior
  que uma API fora do ar: o problema só é descoberto depois.
""",
        contrato="""
```python
def require_scope(scope: Literal["predict", "upload"]) -> Callable   # externo
def require_internal_key(...) -> None                                # interno
```
```
Authorization: Bearer <jwt>     # /api/v1/*
X-Internal-Key: <chave>         # /api/internal/*
```
""",
        acceptance=[
            ("Endpoint externo sem token é recusado",
             "`POST /api/v1/predict` sem `Authorization` retorna 401 com mensagem indicando o cabeçalho esperado."),
            ("Token válido é aceito",
             "Token obtido em `/api/v1/auth/token` com credencial correta dá acesso a `/api/v1/predict`."),
            ("Credencial errada não emite token",
             "`client_secret` incorreto retorna 401 e nenhum token é gerado."),
            ("Escopo é verificado",
             "Token emitido apenas com escopo `predict` recebe 403 ao chamar `/api/v1/upload_doc`."),
            ("Token expirado é rejeitado",
             "Token com `exp` no passado retorna 401 com mensagem de expiração, distinta da de token inválido."),
            ("Assinatura adulterada é rejeitada",
             "Token assinado com outro segredo retorna 401."),
            ("Endpoint interno exige a chave",
             "`/api/internal/stats/overview` sem `X-Internal-Key` retorna 401; com a chave correta, 200."),
            ("Segredos não vazam",
             "Nenhum segredo aparece em log, em resposta de erro ou no bundle do frontend."),
            ("API não sobe sem segredo",
             "Iniciar a aplicação com `JWT_SECRET` vazio falha na inicialização nomeando as variáveis ausentes."),
        ],
        tasks=[
            "Implementar `app/security.py` (emissão, verificação, escopos, chave interna)",
            "Adicionar as variáveis de autenticação ao `config.py` e aos dois `.env.example`",
            "Implementar `app/scripts/gen_secrets.py`",
            "Implementar `POST /api/v1/auth/token` com comparação em tempo constante",
            "Aplicar `require_scope` nos endpoints externos e `require_internal_key` nos internos",
            "Implementar `require_auth()` na inicialização da aplicação",
            "Configurar o proxy do frontend para injetar `X-Internal-Key` sem expô-la ao navegador",
            "Escrever `tests/test_security.py` cobrindo cada critério de aceite",
        ],
    ),
    # ------------------------------------------------------------------ 015
    dict(
        id="SPEC-FEAT-015",
        title="Testes, qualidade e observabilidade",
        epic="api",
        atende="Critérios: organização do código, qualidade da implementação, versionamento",
        depends=[],
        contexto="""
"Organização do código", "Qualidade da implementação" e "Versionamento" são critérios
avaliados diretamente. Esta feature é transversal e acompanha as demais, não uma etapa final.
""",
        escopo="""
- Suíte `pytest` cobrindo taxonomia, features, similaridade, cobertura, recuperação e alucinação.
- `ruff` para lint e formatação, com configuração versionada.
- Log estruturado (JSON) com tempo por etapa e identificador de requisição.
- Repositório Git com histórico legível: commits pequenos, mensagens no padrão Conventional Commits.
- README com instalação, execução, resultados medidos e roteiro de demonstração.
""",
        fora_escopo="""
- Cobertura de testes por percentual como meta — a prioridade é cobrir as regras de negócio
  críticas (taxonomia, gate, alucinação), não inflar número.
- CI em nuvem.
""",
        decisoes="""
- **Testar as regras que sustentam a defesa na entrevista.** Taxonomia, gate de cobertura e
  antialucinação são o que será questionado; é onde os testes valem.
- **Commits incrementais desde o primeiro dia.** Um único commit "projeto completo" perde
  ponto explícito de versionamento.
""",
        contrato="""
```
pytest -q                # suíte completa
ruff check . && ruff format --check .
```
""",
        acceptance=[
            ("Suíte roda em um comando e passa",
             "`pytest -q` termina com todos os testes verdes na máquina limpa."),
            ("Lint sem pendências",
             "`ruff check .` e `ruff format --check .` terminam sem erro."),
            ("Regras críticas cobertas",
             "Existem testes para taxonomia, features, gate de cobertura e casos adversariais de alucinação."),
            ("Histórico de commits conta a construção",
             "O `git log` mostra commits incrementais com mensagens no padrão Conventional Commits, não um commit único."),
            ("Observabilidade real",
             "Toda requisição registra identificador, rota, tempo por etapa e resultado em log JSON."),
            ("README permite reproduzir do zero",
             "Um leitor sem contexto sobe o ambiente, ingere os dados e executa a demonstração seguindo apenas o README."),
        ],
        tasks=[
            "Inicializar o repositório Git e definir a convenção de commits",
            "Configurar `ruff` (lint + format) em `pyproject.toml`",
            "Estruturar `tests/` com fixtures de banco e de dados de exemplo",
            "Implementar log estruturado com identificador de requisição e tempo por etapa",
            "Escrever o README com instalação, execução, resultados e roteiro de demo",
            "Revisar a organização final de pastas e nomes contra a spec",
        ],
    ),
]
