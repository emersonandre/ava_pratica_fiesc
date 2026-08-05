# SPEC-FEAT-009 — Provider de LLM plugável

| | |
| --- | --- |
| **App** | backend |
| **Épico** | RAG e LLM |
| **Atende** | §5 — restrição de infraestrutura de operação |
| **Depende de** | `SPEC-FEAT-001` |

> Documentos irmãos: [acceptance.md](acceptance.md) · [tasks.md](tasks.md)

## Contexto

A entrega usa API externa (OpenAI ou DeepSeek). Os dois falam o mesmo protocolo, então uma
única implementação cobre ambos trocando `base_url` e `model`. A camada de abstração
também é o ponto onde um provider local (servidor compatível com OpenAI, rodando modelo
quantizado nos 16 GB de VRAM de §5) entra sem tocar em regra de negócio.

## Escopo

- Interface `LLMProvider` com `complete(messages, **opts)` e `vision(images, prompt)`.
- Implementação única sobre o SDK `openai`, parametrizada por `.env`.
- Timeout, retry com backoff exponencial (`tenacity`) e teto de tokens.
- Log estruturado por chamada: modelo, tokens de entrada/saída, latência e custo estimado.
- Degradação controlada: falha do provider vira erro de negócio tratado, não 500 com stack trace.

## Fora de escopo

- Servir modelo local nesta entrega — o caminho fica documentado e o código, preparado.
- Fine-tuning.

## Decisões técnicas

- **Um cliente, dois providers.** DeepSeek é compatível com o protocolo da OpenAI; duplicar
  implementação seria custo sem retorno.
- **Visão só onde existe.** O OCR (SPEC-FEAT-006) exige visão; o provider declara a capacidade
  e o pipeline falha cedo, com mensagem clara, se o modelo configurado não a tiver.
- **Temperatura baixa.** A tarefa é reproduzir procedimento técnico, não redigir com criatividade.

## Contrato

```python
class LLMProvider(Protocol):
    name: str
    supports_vision: bool
    def complete(self, messages: list[Message], *, max_tokens: int, temperature: float) -> LLMResponse: ...
    def vision(self, images: list[bytes], prompt: str) -> LLMResponse: ...

def get_provider() -> LLMProvider: ...   # resolvido por LLM_PROVIDER no .env
```
