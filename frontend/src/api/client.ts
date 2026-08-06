/** Cliente HTTP.
 *
 * As chamadas vao para `/api/*` no proprio host. Quem encaminha para a API e
 * injeta o cabecalho `X-Internal-Key` e o proxy -- nginx em producao, o dev
 * server do Vite em desenvolvimento.
 *
 * A chave nunca entra no bundle. Qualquer segredo que chegue ao navegador e
 * publico: basta abrir o DevTools.
 */

export class ErroDaApi extends Error {
  constructor(
    readonly status: number,
    mensagem: string,
    readonly detalhe?: unknown,
  ) {
    super(mensagem)
    this.name = 'ErroDaApi'
  }
}

interface CorpoDeErro {
  detail?: string | { msg?: string; loc?: (string | number)[] }[]
}

function mensagemDoErro(status: number, corpo: CorpoDeErro | null): string {
  const detalhe = corpo?.detail

  if (typeof detalhe === 'string') return detalhe

  if (Array.isArray(detalhe)) {
    // Erro de validacao do FastAPI: nomeia o campo problematico em vez de
    // devolver um "422" seco.
    return detalhe
      .map((item) => {
        const campo = item.loc?.filter((p) => p !== 'body').join('.')
        return campo ? `${campo}: ${item.msg ?? 'invalido'}` : (item.msg ?? 'invalido')
      })
      .join('; ')
  }

  if (status === 401) return 'Sem autorizacao para falar com a API.'
  if (status === 503) return 'A API esta no ar, mas sem os dados necessarios.'
  return `A API respondeu ${status}.`
}

/** Teto de espera de uma requisicao, em milissegundos.
 *
 * `fetch` sem sinal espera para sempre. Se o backend travar, a interface fica
 * com o cronometro subindo e nenhuma saida -- foi o que aconteceu numa geracao
 * de procedimento que passou dos dois minutos.
 *
 * O padrao serve para as chamadas rapidas. A geracao passa o seu proprio teto,
 * folgado o bastante para caber o orcamento de tentativas do backend
 * (LLM_BUDGET_SECONDS, 180s) mais a busca de trechos.
 */
const ESPERA_PADRAO_MS = 20_000
export const ESPERA_GERACAO_MS = 210_000

async function requisitar<T>(
  caminho: string,
  init?: RequestInit,
  esperaMs: number = ESPERA_PADRAO_MS,
): Promise<T> {
  let resposta: Response
  try {
    resposta = await fetch(caminho, { ...init, signal: AbortSignal.timeout(esperaMs) })
  } catch (erro) {
    if (erro instanceof DOMException && erro.name === 'TimeoutError') {
      throw new ErroDaApi(
        0,
        `A API nao respondeu em ${Math.round(esperaMs / 1000)}s. ` +
          'Pode ser o provedor do modelo fora do ar ou sem credito.',
      )
    }
    throw new ErroDaApi(0, 'Nao foi possivel falar com a API. Ela esta no ar?')
  }

  if (!resposta.ok) {
    const corpo = (await resposta.json().catch(() => null)) as CorpoDeErro | null
    throw new ErroDaApi(resposta.status, mensagemDoErro(resposta.status, corpo), corpo)
  }

  return (await resposta.json()) as T
}

export function obter<T>(caminho: string): Promise<T> {
  return requisitar<T>(caminho)
}

export function enviar<T>(caminho: string, corpo: unknown, esperaMs?: number): Promise<T> {
  return requisitar<T>(
    caminho,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(corpo),
    },
    esperaMs,
  )
}

export function enviarArquivo<T>(caminho: string, formulario: FormData): Promise<T> {
  // OCR de PDF grande passa folgado dos 20s do padrao.
  return requisitar<T>(caminho, { method: 'POST', body: formulario }, ESPERA_GERACAO_MS)
}
