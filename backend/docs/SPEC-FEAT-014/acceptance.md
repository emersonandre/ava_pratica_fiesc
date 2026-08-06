# SPEC-FEAT-014 — Critérios de aceite

**Feature:** Registro de novo documento de falha  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [x] **Ciclo completo demonstrável**
  - *Verificação:* Pergunta sobre família descoberta é recusada; após o upload de documento para ela, a mesma pergunta é respondida com citação ao documento novo.

- [x] **Cobertura atualiza sem reinício**
  - *Verificação:* `GET /api/faults` reflete a nova cobertura na chamada seguinte ao upload.

- [x] **Reenvio não duplica**
  - *Verificação:* Enviar o mesmo arquivo duas vezes mantém a contagem de chunks e retorna referência ao documento existente.

- [x] **Arquivo inválido é rejeitado**
  - *Verificação:* Upload de arquivo não-PDF ou corrompido retorna 400 com mensagem clara e não deixa registro parcial.

- [x] **PDF sem camada de texto também funciona**
  - *Verificação:* Um PDF escaneado passa pelo caminho de OCR e é indexado.

- [x] **Estado é consultável**
  - *Verificação:* `GET /api/documents` mostra o estado de indexação e, em caso de falha, o motivo.
