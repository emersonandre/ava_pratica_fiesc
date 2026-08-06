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

async function requisitar<T>(caminho: string, init?: RequestInit): Promise<T> {
  let resposta: Response
  try {
    resposta = await fetch(caminho, init)
  } catch {
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

export function enviar<T>(caminho: string, corpo: unknown): Promise<T> {
  return requisitar<T>(caminho, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(corpo),
  })
}

export function enviarArquivo<T>(caminho: string, formulario: FormData): Promise<T> {
  return requisitar<T>(caminho, { method: 'POST', body: formulario })
}
