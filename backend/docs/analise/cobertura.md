# Cobertura documental das falhas

> Gerado por `python manage.py report documentos`.
> Evidencia das [SPEC-FEAT-008](../SPEC-FEAT-008/spec.md) e [SPEC-FEAT-010](../SPEC-FEAT-010/spec.md).

## Mapa familia -> documento

O vinculo e **explicito e revisado**, nunca inferido pelo modelo. E o que sustenta a regra da secao 3 do enunciado: sem linha aqui, o LLM nao e chamado.

| Familia | Descricao | Documento | Situacao |
| --- | --- | --- | --- |
| `cocked_rotor` | Rotor inclinado em relacao ao eixo de rotacao | `Doc6.pdf` | coberta |
| `correia` | Defeito no sistema de transmissao por correia | `Doc4.pdf` | coberta |
| `desalinhamento` | Eixos do motor e da carga fora de alinhamento | `Doc2.pdf` | coberta |
| `desbalanceamento` | Distribuicao desigual de massa no rotor | `Doc3.pdf` | coberta |
| `eccentric_rotor` | Centro geometrico do rotor deslocado do centro de rotacao | — | **sem documento** |
| `falta_fase` | Operacao com falta de fase na alimentacao eletrica | — | **sem documento** |
| `polia` | Defeito em polia (excentricidade, desbalanceamento, desgaste) | `Doc5.pdf` | coberta |
| `rolamento` | Defeito em rolamento (pista interna, externa, esferas ou combinado) | `Doc1.pdf` | coberta |
| `ventoinha` | Defeito na ventoinha do motor | — | **sem documento** |

**6 de 9 familias de problema cobertas.**

## Familias sem documentacao

- `eccentric_rotor`
- `falta_fase`
- `ventoinha`

Sao o caso de recusa exigido pelo enunciado — **reais, nao fabricados para a demonstracao**. Ao receber um evento dessas familias, o sistema informa que ainda nao existe documentacao para o problema identificado e sugere registrar um novo documento, sem chamar o modelo de linguagem.

## Desfechos do gate

| Motivo | Quando ocorre | O LLM e chamado? |
| --- | --- | :---: |
| `coberto` | Ha documento para a familia diagnosticada | sim |
| `sem_documento` | Falha identificada, nenhum documento a cobre | **nao** |
| `estado_operacional` | O padrao e um estado (normal, motor parado), nao falha | **nao** |
| `sem_diagnostico` | A vizinhanca nao sustenta um diagnostico | **nao** |

Colapsar os quatro em um generico "nao sei" desperdicaria a informacao mais util da solucao: o motivo pelo qual o sistema se absteve.

## Por que o filtro por familia e rigido

Os seis documentos compartilham quase o mesmo vocabulario tecnico — "vibracao elevada", "aquecimento nos mancais", "desgaste de rolamentos", "afrouxamento de parafusos". Busca puramente semantica erra, e erra com confianca.

Medicao com sete consultas-sonda, uma por assunto conhecido:

| Consulta | Sem filtro | Com filtro | Esperado |
| --- | --- | --- | --- |
| como corrigir desalinhamento de motor eletrico | `Doc2.pdf` | `Doc2.pdf` | `Doc2.pdf` |
| rotor desbalanceado, vibracao radial elevada | `Doc6.pdf` ✗ | `Doc3.pdf` | `Doc3.pdf` |
| correia frouxa escorregando na polia | `Doc5.pdf` ✗ | `Doc4.pdf` | `Doc4.pdf` |
| polia excentrica, oscilacao da correia | `Doc5.pdf` | `Doc5.pdf` | `Doc5.pdf` |
| rotor inclinado em relacao ao eixo | `Doc6.pdf` | `Doc6.pdf` | `Doc6.pdf` |
| defeito na pista interna do rolamento | `Doc1.pdf` | `Doc1.pdf` | `Doc1.pdf` |
| ruido de impacto nas esferas do rolamento | `Doc4.pdf` ✗ | `Doc1.pdf` | `Doc1.pdf` |

**Acerto: 4/7 sem filtro, 7/7 com filtro.**

Sem o filtro, "ruido de impacto nas esferas do rolamento" recupera o manual de **correias**. A resposta sairia fluente, citada — e apontando o procedimento errado. Em manutencao industrial isso e pior que nao responder.

O filtro e rigido, nao um reforco de score: um peso alto ainda deixaria passar documento errado; o corte duro elimina a classe inteira de erro.
