# SPEC-FEAT-015 — Testes, qualidade e observabilidade

| | |
| --- | --- |
| **App** | backend |
| **Épico** | API, seguranca e qualidade |
| **Atende** | Critérios: organização do código, qualidade da implementação, versionamento |
| **Depende de** | — |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

"Organização do código", "Qualidade da implementação" e "Versionamento" são critérios
avaliados diretamente. Esta feature é transversal e acompanha as demais, não uma etapa final.

## Escopo

- Suíte `pytest` cobrindo taxonomia, features, similaridade, cobertura, recuperação e alucinação.
- `ruff` para lint e formatação, com configuração versionada.
- Log estruturado (JSON) com tempo por etapa e identificador de requisição.
- Repositório Git com histórico legível: commits pequenos, mensagens no padrão Conventional Commits.
- README com instalação, execução, resultados medidos e roteiro de demonstração.

## Fora de escopo

- Cobertura de testes por percentual como meta — a prioridade é cobrir as regras de negócio
  críticas (taxonomia, gate, alucinação), não inflar número.
- CI em nuvem.

## Decisões técnicas

- **Testar as regras que sustentam a defesa na entrevista.** Taxonomia, gate de cobertura e
  antialucinação são o que será questionado; é onde os testes valem.
- **Commits incrementais desde o primeiro dia.** Um único commit "projeto completo" perde
  ponto explícito de versionamento.

## Contrato

```
pytest -q                # suíte completa
ruff check . && ruff format --check .
```
