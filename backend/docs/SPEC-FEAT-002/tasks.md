# SPEC-FEAT-002 — Tarefas

**Feature:** Taxonomia canônica de falhas

- [x] Extrair os 151 rótulos distintos e classificar manualmente em famílias (planilha de apoio)
- [x] Implementar `app/core/taxonomy.py`: dicionário de typos, regras de sufixo, conjunto de estados
- [x] Definir as famílias canônicas e documentar cada uma com uma frase de descrição
- [x] Implementar `normalize_fault` e a exceção `UnknownFaultLabel`
- [x] Escrever `tests/test_taxonomy.py` cobrindo cada critério de aceite
- [x] Gerar `backend/docs/analise/taxonomia.md` por script, a partir do dataset real
- [x] Revisar a matriz final e confirmar que nenhuma família distinta foi fundida

---

Concluir esta feature exige marcar também todos os itens de [acceptance.md](acceptance.md).
