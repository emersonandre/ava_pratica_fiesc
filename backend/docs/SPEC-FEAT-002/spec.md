# SPEC-FEAT-002 — Taxonomia canônica de falhas

| | |
| --- | --- |
| **App** | backend |
| **Épico** | Infraestrutura e dados |
| **Atende** | §6 — Descrição dos dados (estados × problemas) |
| **Depende de** | `SPEC-FEAT-001` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

A coluna `fault` do `banner.csv` contém **151 rótulos distintos**, anotados manualmente por
operadores. Eles não representam 151 falhas: colapsam em ~15 famílias, poluídas por sufixos
de sessão de ensaio e por erros de digitação. Sem normalização, qualquer contagem de
"eventos similares" e qualquer mapa falha→documento nasce errado.

## Escopo

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

## Fora de escopo

- Inferir família por similaridade de sinal (isso é a SPEC-FEAT-005); aqui a normalização é
  puramente léxica e auditável.
- Corrigir rótulos que o operador errou de *falha* (não só de grafia) — não há como saber.

## Decisões técnicas

- **Normalização léxica determinística, não fuzzy matching automático.** Um `difflib` cego
  aproximaria `desalinhado` de `desbalanceado` (distância pequena, falhas distintas). Os typos
  são poucos e conhecidos: viram um dicionário explícito, revisável e testável.
- **`raw_fault` nunca é descartado.** Auditoria e defesa na entrevista dependem de mostrar o
  antes e o depois.
- **Falhar alto em rótulo desconhecido.** Um rótulo novo que não case com nenhuma regra
  levanta erro na ingestão em vez de virar `unknown` silencioso.

## Contrato

```python
@dataclass(frozen=True)
class FaultLabel:
    raw: str
    canonical: str
    family: str
    is_problem: bool

def normalize_fault(raw: str) -> FaultLabel: ...
```
