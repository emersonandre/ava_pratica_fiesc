# SPEC-FEAT-017 — Critérios de aceite

**Feature:** Ingestão de leituras do chão de fábrica  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [x] **O JSON do enunciado é aceito sem adaptação**
  - *Verificação:* O exemplo do §2 copiado literalmente retorna 201, e `cocked_rotor_2` é normalizado para a família `cocked_rotor`.

- [x] **Reenvio atualiza em vez de duplicar**
  - *Verificação:* Enviar o mesmo `id` duas vezes retorna `atualizadas = 1` e não cria segundo registro.

- [x] **Leitura sem rótulo é preservada**
  - *Verificação:* Payload sem `fault` retorna 201 com `anotada = false` e `familia = null`.

- [x] **Rótulo desconhecido não derruba o lote**
  - *Verificação:* Um rótulo fora da taxonomia retorna 201, o rótulo aparece em `rotulos_desconhecidos` e a leitura fica não anotada.

- [x] **Leitura sem rótulo não vira vizinha**
  - *Verificação:* Nenhum registro com `fault_family` nulo aparece entre os vizinhos de uma busca.

- [x] **A leitura recém-gravada não é vizinha de si mesma**
  - *Verificação:* Com `analisar: true`, o `id` recém-inserido não consta na lista de vizinhos.

- [x] **Identificador é gerado quando ausente**
  - *Verificação:* Um lote de 3 leituras sem `id` recebe três identificadores distintos.

- [x] **Escopo é exigido**
  - *Verificação:* Token emitido apenas com escopo `predict` recebe 403 ao enviar leitura.

- [x] **Lote vazio é recusado**
  - *Verificação:* `{"leituras": []}` retorna 422.
