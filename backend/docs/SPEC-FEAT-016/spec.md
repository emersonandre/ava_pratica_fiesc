# SPEC-FEAT-016 — Autenticação: JWT externo e chave interna

| | |
| --- | --- |
| **App** | backend |
| **Épico** | API, seguranca e qualidade |
| **Atende** | DIF — APIs, Integrações em ambiente industrial |
| **Depende de** | `SPEC-FEAT-001` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

As duas superfícies da API (SPEC-FEAT-013) têm riscos diferentes e recebem mecanismos
diferentes. Em ambiente industrial, uma API de manutenção exposta sem autenticação é um
problema sério: `/upload_doc` escreve na base de conhecimento que orienta intervenção
física em equipamento. Quem consegue injetar documento consegue influenciar o que o
sistema recomenda ao técnico.

## Escopo

### Externo — JWT `Bearer`

- `POST /api/v1/auth/token`: troca `client_id` + `client_secret` (do `.env`) por um JWT
  assinado em HS256, com expiração curta (padrão 60 min).
- Token carrega `sub`, `iss`, `exp` e **escopos**: `predict` e `upload`.
- `/api/v1/predict` exige escopo `predict`; `/api/v1/upload_doc` exige escopo `upload`.
- Erros distintos e informativos: token ausente, expirado, inválido e sem escopo.

### Interno — chave estática

- Cabeçalho `X-Internal-Key`, comparado com `INTERNAL_API_KEY` do `.env`.
- A chave vive no proxy do container do frontend e é injetada no cabeçalho ali;
  **nunca é enviada ao navegador**.

### Transversal

- Comparação de segredos em tempo constante (`hmac.compare_digest`).
- `Settings.require_auth()` impede a API de subir sem segredo configurado.
- `app/scripts/gen_secrets.py` gera os valores; não escreve no `.env` automaticamente.

## Fora de escopo

- OAuth2 completo com refresh token e revogação — desproporcional para dois clientes de
  máquina; o caminho fica registrado na arquitetura.
- Login de usuário final, papéis e permissões por pessoa.
- Rotação automática de segredos.

## Decisões técnicas

- **Escopo por endpoint, não um token que abre tudo.** Um coletor de dados que só consulta
  não deve conseguir injetar documento na base de conhecimento — é o caminho mais direto
  para envenenar as recomendações entregues ao técnico.
- **Chave estática no interno em vez de JWT.** O frontend não é um cliente autenticável: a
  chave fica no proxy do servidor, nunca no navegador. Emissão e renovação de token ali
  seriam cerimônia sem ganho de segurança real.
- **HS256 com segredo compartilhado, não RS256.** Emissor e verificador são o mesmo serviço;
  par de chaves assimétricas só faria sentido com emissor separado.
- **Falhar na inicialização sem segredo.** Uma API industrial no ar sem autenticação é pior
  que uma API fora do ar: o problema só é descoberto depois.

## Contrato

```python
def require_scope(scope: Literal["predict", "upload"]) -> Callable   # externo
def require_internal_key(...) -> None                                # interno
```
```
Authorization: Bearer <jwt>     # /api/v1/*
X-Internal-Key: <chave>         # /api/internal/*
```
