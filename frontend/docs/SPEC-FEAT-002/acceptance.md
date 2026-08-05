# SPEC-FEAT-002 — Critérios de aceite

**Feature:** Dashboard de indicadores  
Marque um item apenas quando ele tiver sido **verificado na prática**, não quando o código parecer pronto.

- [ ] **Indicadores conferem com o banco**
  - *Verificação:* Os valores dos cartões batem com consulta SQL direta sobre `sensor_events`.

- [ ] **Famílias sem documento saltam à vista**
  - *Verificação:* Elas aparecem visualmente destacadas no ranking e contabilizadas em um cartão próprio.

- [ ] **Estados não contam como problema**
  - *Verificação:* `normal`, `baseline`, `motor_desligado` e afins não entram no total de eventos-problema.

- [ ] **Carregamento não pisca**
  - *Verificação:* Enquanto carrega, os cartões mostram esqueleto de mesma dimensão — sem salto de layout.

- [ ] **Navegação encadeia**
  - *Verificação:* Clicar em uma família leva à análise já filtrada por ela.
