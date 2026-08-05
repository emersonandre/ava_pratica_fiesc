# Arquitetura do Projeto: Manutenção Prescritiva com IA

## 1. O Desafio Proposto
Desenvolver o pipeline completo de uma solução de Manutenção Prescritiva para uma indústria de grande porte.

### Objetivos Principais:
- **Análise de Dados:** Receber dados de sensores e identificar registros históricos que apresentem comportamento semelhante.
- **Integração Documental:** Consultar manuais e relatórios técnicos associados aos eventos identificados.
- **Assistente de IA:** Construir um modelo de linguagem para interagir via chat e sugerir ações corretivas baseadas unicamente na documentação existente. Se o problema não estiver documentado, avisar e sugerir o registro de um novo documento.
- **Visualização:** Apresentar os resultados, ocorrências e frequências através de dashboards e chat interativo.

### Restrições:
- Uso obrigatório da linguagem Python.
- A inferência/execução do modelo final deve rodar em uma máquina com até 32 GB de RAM e GPU de 16 GB.

## 2. A Solução Arquitetada
Com base na liberdade de escolha de ferramentas e buscando focar nos diferenciais da vaga (APIs, Banco de Dados, Dashboards), definimos uma stack Full Stack robusta e realista para o ambiente industrial:

### Backend: Django + Django REST Framework (DRF)
- **Papel:** Maestro da aplicação. Gerencia as APIs, a regra de negócio do RAG, a comunicação com o banco de dados e as chamadas para o LLM local.
- **Por que Django?** Framework Python robusto e seguro, excelente integração com PostgreSQL e permite estruturação profissional do projeto.

### Frontend: React
- **Papel:** Interface do usuário (UI). Consumirá a API do Django.
- **Funcionalidades:** 
  - Dashboard para apresentar os dados visuais (frequência, quantidade de ocorrências).
  - Interface de Chat interativo com o operador.
- **Por que React?** Criação de interfaces ricas, componentizadas e profissionais.

### Banco de Dados: PostgreSQL + `pgvector`
- **Papel:** Armazenamento unificado.
- **Dados Tabulares:** Armazena o histórico dos sensores, separando estados normais de falhas reais.
- **Embeddings:** A extensão `pgvector` armazenará as representações vetoriais dos manuais e documentos para a busca semântica (RAG).

### Inteligência Artificial (ML + GenAI)
- **Motor de Similaridade:** Algoritmo clássico (ex: KNN/Cosine) ou consultas SQL para cruzar o novo evento com o histórico do banco de dados relacional e identificar defeitos passados.
- **LLM Local (Ollama):** Para respeitar o limite de 16GB de VRAM da GPU, utilizaremos o Ollama rodando um modelo quantizado (como Llama 3 8B ou Mistral).
- **RAG com Restrição Anti-Alucinação:** O pipeline recuperará trechos dos manuais via `pgvector` e injetará no prompt, orientando o LLM a responder apenas com base na documentação.

## 3. Estrutura do Repositório Sugerida
A organização do repositório é um critério de avaliação direto.

```text
projeto-manutencao-prescritiva/
│
├── backend/                # Projeto Django e DRF
│   ├── manage.py
│   ├── requirements.txt
│   └── app_core/           # Lógica de ML, RAG, pgvector e APIs
│
├── frontend/               # Projeto React
│   ├── package.json
│   ├── src/
│   │   ├── components/     # Chat, gráficos
│   │   └── pages/          # Dashboard principal
│
├── dados/                  # Scripts de ETL
│   ├── ingestao_csv.py     # Processa banner.csv
│   └── ingestao_docs.py    # Chunking e embeddings dos PDFs
│
├── docker-compose.yml      # Opcional: Levanta BD, Backend e Frontend
└── README.md               # Documentação detalhada da arquitetura