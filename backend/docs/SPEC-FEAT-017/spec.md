# SPEC-FEAT-017 — Ingestão de leituras do chão de fábrica

| | |
| --- | --- |
| **App** | backend |
| **Épico** | API, seguranca e qualidade |
| **Atende** | §2 — dados enviados continuamente ao banco corporativo; DIF — Integrações em ambiente industrial |
| **Depende de** | `SPEC-FEAT-002`, `SPEC-FEAT-003`, `SPEC-FEAT-016` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

A seção 2 do enunciado descreve o fluxo real: os sensores enviam leituras
**continuamente** para o banco corporativo, e a equipe de IA consome esse banco.

A entrega inicial tinha só a porta de saída. `/predict` consulta o histórico mas
não escreve nele, e a única forma de alimentar a base era a carga em lote do CSV.
Um sistema instalado na planta não tem como funcionar assim: a máquina gera
leitura o tempo todo, e uma falha nova precisa entrar na base para virar
histórico das próximas.

## Escopo

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

## Fora de escopo

- Ingestão por MQTT ou OPC-UA — descrita no documento de arquitetura; aqui o
  contrato é HTTP, que qualquer coletor moderno fala.
- Fila de mensagens entre o coletor e a API.

## Decisões técnicas

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

## Contrato

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
