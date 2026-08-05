# SPEC-FEAT-006 — Critérios de aceite

**Feature:** Painel de eventos similares  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [ ] **Todos os itens do enunciado presentes**
  - *Verificação:* A tela exibe quantidade de eventos similares, distribuição temporal, frequência e contexto operacional.

- [ ] **Vizinhos são do histórico**
  - *Verificação:* Nenhum vizinho listado pertence ao período de holdout.

- [ ] **Voto disputado é perceptível**
  - *Verificação:* Um caso com voto dividido é visualmente distinguível de um caso unânime.

- [ ] **Evento em análise localizado na linha do tempo**
  - *Verificação:* O marcador do evento analisado aparece posicionado corretamente entre os similares.

- [ ] **Contexto operacional comparável**
  - *Verificação:* As faixas de RPM e temperatura da vizinhança aparecem lado a lado com os valores do evento.

- [ ] **Tabela usável com muitos vizinhos**
  - *Verificação:* Com k = 50 a tabela permanece navegável, ordenável e sem quebra de layout.
