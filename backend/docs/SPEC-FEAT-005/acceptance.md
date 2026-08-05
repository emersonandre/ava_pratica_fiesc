# SPEC-FEAT-005 — Critérios de aceite

**Feature:** Motor de similaridade histórica  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [x] **Acerto medido no holdout, não estimado**
  - *Verificação:* A família majoritária dos vizinhos é comparada ao rótulo real de todo o split `holdout`; a taxa e a matriz de confusão por família ficam em `backend/docs/analise/similaridade.md`.

- [ ] **Evento fora de distribuição não é forçado**
  - *Verificação:* Um vetor sintético com valores muito acima da faixa observada retorna `out_of_distribution = True` e `diagnosed_family = None`.

- [x] **Estatísticas conferem com o banco**
  - *Verificação:* Para uma família escolhida, `family_counts`, `timeline` e `frequency_per_day` batem com consulta SQL direta sobre a mesma vizinhança.

- [x] **Sem vazamento na busca**
  - *Verificação:* Nenhum vizinho retornado tem `split = 'holdout'`.

- [x] **Confiança discrimina**
  - *Verificação:* Vizinhança unânime produz confiança alta; vizinhança dividida entre duas famílias produz confiança baixa.

- [ ] **Latência aceitável**
  - *Verificação:* `POST /api/events/similar` responde em menos de 300 ms no percentil 95, medido localmente.
