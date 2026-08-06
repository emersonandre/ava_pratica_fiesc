# Guarda anti-alucinacao -- comportamento observado

> Gerado por `python manage.py report alucinacao`. Os cenarios sao executados de
> verdade, inclusive as chamadas ao modelo. Evidencia da
> [SPEC-FEAT-012](../SPEC-FEAT-012/spec.md).

## Defesa em quatro camadas

| Camada | Mecanismo | O que impede |
| --- | --- | --- |
| 1 | Gate de cobertura, antes do LLM | Responder sobre falha sem documentacao. O modelo nao e chamado — nao ha como alucinar o que nao foi perguntado |
| 2 | Filtro rigido por familia na recuperacao | Citar o procedimento errado. Medido: 4/7 de acerto sem filtro, 7/7 com ele |
| 3 | Prompt restritivo + descarte de citacao inventada | Alucinacao de fonte — a mais perigosa, porque parece verificavel |
| 4 | Verificacao de embasamento pos-geracao | Passo redigido sem origem no texto recuperado |

## Divisao de trabalho

```
numeros (quantos eventos, desde quando, frequencia)  -> banco
qual documento consultar                             -> codigo
quais trechos entram no contexto                     -> codigo
redacao dos passos a partir desses trechos           -> MODELO
verificacao de que cada passo tem respaldo           -> codigo
```

O modelo so redige. Nao escolhe fonte, nao inventa numero e nao decide se pode
responder.

## Cenarios executados

| Cenario | Esperado | Observado | LLM chamado | Embasamento |
| --- | --- | --- | :---: | ---: |
| Falha coberta por documento com camada de texto | prescricao citada | prescricao com 15 passos | sim | 100% |
| Falha coberta por documento vindo de OCR | prescricao citada + aviso de OCR | prescricao com 26 passos | sim | 100% |
| Falha identificada, sem documentacao | recusa `sem_documento`, LLM nao chamado | recusa `sem_documento` | **nao** | — |
| Estado operacional, nao falha | recusa `estado_operacional`, LLM nao chamado | recusa `estado_operacional` | **nao** | — |
| Vizinhanca dividida | recusa, LLM nao chamado | recusa `sem_diagnostico` | **nao** | — |

## Recusa de pergunta fora de dominio

| Pergunta | No dominio? |
| --- | :---: |
| Como corrigir o desalinhamento do motor? | sim |
| Qual a temperatura aceitavel do mancal? | sim |
| O rolamento esta com ruido de impacto. | sim |
| Qual a capital da Franca? | **nao** |
| Me conte uma piada. | **nao** |
| Quem ganhou a copa de 2022? | **nao** |
| Escreva um poema sobre o mar. | **nao** |

---

## Detalhamento

### Falha coberta por documento com camada de texto

Desalinhamento, coberto pelo Doc2.

- Rotulo real: `desalinhamento`
- Diagnostico: `desalinhamento` (confianca 86%)
- Cobertura: `coberto`
- Documentos: ['Doc2.pdf']
- LLM chamado: **sim**
- Tempo total: 26700 ms

**Diagnostico:** Falha de desalinhamento: eixos do motor e da máquina acionada não estão corretamente alinhados, causando vibração, aquecimento, ruído, desgaste de rolamentos e redução da vida útil. [Doc2.pdf, p. 1]

**Passos:** 6 de inspecao, 6 de correcao, 3 de validacao.

Exemplo de passo com citacao:

> Desligue o motor elétrico, bloqueie e etiquete a fonte de energia, confirme ausência de tensão, aguarde a parada completa das partes girantes e garanta que não exista partida automática. [Doc2.pdf, p. 2]
> [Doc2.pdf, p. 2]

**Embasamento:** 15/15 = 100%

Avisos declarados pelo sistema:

- A documentação não especifica valores de tolerância de alinhamento nem torque de aperto; esses parâmetros exigem julgamento humano ou normas complementares.
- O diagnóstico por similaridade tem confiança de 86%; recomenda-se confirmar a falha por medições diretas na máquina.
- O documento descreve apenas desalinhamento paralelo; não há procedimento explícito para desalinhamento angular.

### Falha coberta por documento vindo de OCR

Rolamento, coberto pelo Doc1 (17 paginas em imagem).

- Rotulo real: `rolamento`
- Diagnostico: `rolamento` (confianca 100%)
- Cobertura: `coberto`
- Documentos: ['Doc1.pdf']
- LLM chamado: **sim**
- Tempo total: 97559 ms

**Diagnostico:** Falha na família de rolamentos identificada, requerendo inspeção para determinar o tipo de defeito e aplicação do procedimento de correção adequado.

**Passos:** 12 de inspecao, 9 de correcao, 5 de validacao.

Exemplo de passo com citacao:

> Verificar marcas de desgaste após a desmontagem.
> [Doc1.pdf, p. 12-14]

**Embasamento:** 26/26 = 100%

Avisos declarados pelo sistema:

- A documentação não especifica qual tipo de defeito de rolamento (pista interna, externa, elementos rolantes ou gaiola) está presente; a inspeção deve determinar o tipo.
- A documentação não fornece valores de referência para vibração, temperatura, ruído ou torque de instalação.
- Se a inspeção identificar contaminação ou falta de lubrificação como causa raiz, os procedimentos dos Casos 1 e 2 (limpeza, substituição de vedações, troca de lubrificante) devem ser aplicados além da substituição do rolamento.
- O contexto operacional informado (RPM, temperatura) não é abordado na documentação fornecida.
- Parte da documentacao consultada foi obtida por OCR de paginas em imagem. Confirme os valores criticos no documento original.

### Falha identificada, sem documentacao

Rotor excentrico. Diagnostico confiavel, nenhum documento cobre.

- Rotulo real: `eccentric_rotor`
- Diagnostico: `eccentric_rotor` (confianca 70%)
- Cobertura: `sem_documento`
- Documentos: —
- LLM chamado: **nao**
- Tempo total: 22 ms

**Recusa (`sem_documento`):**

> O problema identificado foi `eccentric_rotor` (Centro geometrico do rotor deslocado do centro de rotacao), mas ainda nao existe documentacao cadastrada para esse defeito. O sistema nao emite recomendacao sem procedimento documentado.

Registre um novo documento para este defeito em POST /api/v1/upload_doc para que futuras ocorrencias recebam orientacao de correcao.

> Registre um documento para este defeito em POST /api/v1/upload_doc.

### Estado operacional, nao falha

Motor desligado.

- Rotulo real: `motor_desligado`
- Diagnostico: `motor_desligado` (confianca 100%)
- Cobertura: `estado_operacional`
- Documentos: —
- LLM chamado: **nao**
- Tempo total: 11 ms

**Recusa (`estado_operacional`):**

> O padrao corresponde ao estado operacional `motor_desligado` (Motor parado), que nao representa uma falha. Nenhuma acao de manutencao e indicada.

### Vizinhanca dividida

Ventoinha. O sinal nao sustenta diagnostico.

- Rotulo real: `ventoinha`
- Diagnostico: `None` (confianca 36%)
- Cobertura: `sem_diagnostico`
- Documentos: —
- LLM chamado: **nao**
- Tempo total: 19 ms

**Recusa (`sem_diagnostico`):**

> O padrao observado nao corresponde de forma consistente a nenhuma familia do historico. Nao ha diagnostico confiavel, entao nenhuma acao de manutencao e recomendada. Os eventos similares encontrados estao disponiveis para analise da equipe tecnica.

## Limitacoes assumidas

- **Nao existe garantia formal de ausencia de alucinacao.** O objetivo e reduzir a
  taxa e tornar cada afirmacao auditavel ate a pagina do PDF.
- A verificacao de embasamento e **lexica**, nao semantica. Ela prova que o passo
  tem origem no texto recuperado, nao que o passo esta tecnicamente correto.
  Usar um LLM como juiz teria custo, latencia e o problema de que o juiz alucina
  igual.
- Documentos vindos de OCR carregam risco maior: o motor perde diacriticos e
  confunde caracteres. Toda prescricao baseada neles traz aviso explicito.
- O limiar de confianca da similaridade e uma escolha de projeto. Mais cobertura
  significa mais erro; a tabela de precisao x cobertura esta em
  [similaridade.md](similaridade.md).
