# SPEC-FEAT-007 — Critérios de aceite

**Feature:** Indexação semântica dos documentos  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [x] **Recuperação faz sentido no domínio**
  - *Verificação:* A consulta "como corrigir desalinhamento de motor" retorna trechos do Doc2 nas primeiras posições.

- [x] **Chunks não cortam procedimento ao meio**
  - *Verificação:* Inspeção dos chunks das seções de procedimento mostra passos completos; caso de teste registrado.

- [ ] **Indexação roda em CPU em tempo aceitável**
  - *Verificação:* A indexação completa dos 6 documentos termina em menos de 2 minutos, sem GPU, e o tempo fica no README.

- [x] **Reindexação é idempotente**
  - *Verificação:* Rodar a indexação duas vezes mantém a contagem de chunks.

- [x] **Índice é autodescritivo**
  - *Verificação:* O modelo de embedding e a dimensão estão gravados em tabela de metadados; divergência de dimensão é bloqueada com erro claro.

- [x] **Sem chamada de rede**
  - *Verificação:* A indexação completa com a rede desativada termina com sucesso.
