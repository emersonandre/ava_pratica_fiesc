# SPEC-FEAT-003 — Critérios de aceite

**Feature:** Gráficos analíticos  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [ ] **Distribuição temporal correta**
  - *Verificação:* Os picos da linha do tempo coincidem com os períodos de ensaio conhecidos de cada família.

- [ ] **Corte de holdout visível**
  - *Verificação:* A separação entre 09/jun e 10/jun aparece marcada no gráfico, com legenda explicando.

- [ ] **Cores consistentes**
  - *Verificação:* Uma família tem a mesma cor no dashboard, nos gráficos e no painel de similares.

- [ ] **Legível em volume**
  - *Verificação:* Com todas as famílias ativas, o gráfico permanece legível; famílias pouco frequentes são agrupadas ou filtráveis.

- [ ] **Eixos com unidade**
  - *Verificação:* Todo eixo de métrica física traz a unidade no rótulo.

- [ ] **Responsivo**
  - *Verificação:* Os gráficos se ajustam em telas a partir de 1280 px sem cortar rótulo.
