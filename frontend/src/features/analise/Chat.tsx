import { useEffect, useRef, useState } from 'react'

import { useChat } from '../../api/queries'
import type { AmostraHoldout, Citacao, MensagemChat } from '../../api/types'
import './Chat.css'

/** Conversa com o assistente, ancorada na leitura analisada.
 *
 * Cada pergunta recupera trechos de novo na documentacao. O historico entra no
 * prompt, mas nao substitui a busca -- responder de memoria e onde o modelo
 * inventa.
 */
export function Chat({
  evento,
  limiar,
  aoResponder,
}: {
  evento: AmostraHoldout
  limiar: number
  aoResponder?: () => void
}) {
  const [mensagens, setMensagens] = useState<MensagemChat[]>([])
  const [rascunho, setRascunho] = useState('')
  const [sugestoes, setSugestoes] = useState<string[]>([
    'Como corrijo esta falha?',
    'Quais os sintomas desse defeito?',
    'Que ferramentas eu preciso?',
  ])

  const chat = useChat()
  const fim = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fim.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [mensagens, chat.isPending])

  function perguntar(texto: string) {
    const pergunta = texto.trim()
    if (!pergunta || chat.isPending) return

    const historico = mensagens
    setMensagens([...historico, { papel: 'operador', texto: pergunta }])
    setRascunho('')

    chat.mutate(
      { evento, mensagens: historico, pergunta, confianca_minima: limiar },
      {
        onSuccess: (resposta) => {
          setMensagens((atual) => [
            ...atual,
            {
              papel: 'assistente',
              texto: resposta.resposta,
              citacoes: resposta.citacoes,
              embasamento: resposta.embasamento?.score ?? null,
              recusou: resposta.recusou,
            },
          ])
          if (resposta.sugestoes.length) setSugestoes(resposta.sugestoes)
          aoResponder?.()
        },
        onError: (erro) => {
          setMensagens((atual) => [
            ...atual,
            {
              papel: 'assistente',
              texto: `Não consegui responder: ${(erro as Error).message}`,
              recusou: true,
            },
          ])
        },
      },
    )
  }

  return (
    <section className="cartao chat">
      <div className="chat-topo">
        <div>
          <h2>Assistente de manutenção</h2>
          <p className="t3">
            Responde apenas com base nos procedimentos cadastrados, citando página.
          </p>
        </div>
      </div>

      <div className="chat-conversa">
        {mensagens.length === 0 && !chat.isPending && (
          <div className="chat-inicio">
            <p className="t2">
              Pergunte o que fazer com esta leitura. O assistente consulta a
              documentação técnica da falha e responde citando a fonte.
            </p>
          </div>
        )}

        {mensagens.map((mensagem, indice) => (
          <Bolha key={indice} mensagem={mensagem} />
        ))}

        {chat.isPending && (
          <div className="bolha bolha--assistente">
            <div className="bolha-conteudo bolha-pensando">
              <span className="ponto" />
              <span className="ponto" />
              <span className="ponto" />
              <span className="t3">consultando a documentação…</span>
            </div>
          </div>
        )}

        <div ref={fim} />
      </div>

      {sugestoes.length > 0 && !chat.isPending && (
        <div className="chat-sugestoes">
          {sugestoes.map((sugestao) => (
            <button
              key={sugestao}
              type="button"
              className="sugestao"
              onClick={() => perguntar(sugestao)}
            >
              {sugestao}
            </button>
          ))}
        </div>
      )}

      <form
        className="chat-entrada"
        onSubmit={(e) => {
          e.preventDefault()
          perguntar(rascunho)
        }}
      >
        <input
          value={rascunho}
          onChange={(e) => setRascunho(e.target.value)}
          placeholder="Escreva uma pergunta…"
          aria-label="Pergunta"
          disabled={chat.isPending}
        />
        <button
          type="submit"
          className="botao botao-primario"
          disabled={!rascunho.trim() || chat.isPending}
        >
          Enviar
        </button>
      </form>
    </section>
  )
}

function Bolha({ mensagem }: { mensagem: MensagemChat }) {
  const doOperador = mensagem.papel === 'operador'

  return (
    <div className={`bolha bolha--${doOperador ? 'operador' : 'assistente'}`}>
      <div
        className={`bolha-conteudo ${mensagem.recusou ? 'bolha-conteudo--recusa' : ''}`}
      >
        <p className="bolha-texto">{mensagem.texto}</p>

        {mensagem.citacoes && mensagem.citacoes.length > 0 && (
          <div className="bolha-fontes">
            {mensagem.citacoes.map((citacao) => (
              <Fonte key={rotulo(citacao)} citacao={citacao} />
            ))}
          </div>
        )}

        {mensagem.embasamento !== null && mensagem.embasamento !== undefined && (
          <p className="bolha-embasamento t3">
            {Math.round(mensagem.embasamento * 100)}% do texto verificado contra a
            documentação
          </p>
        )}
      </div>
    </div>
  )
}

function Fonte({ citacao }: { citacao: Citacao }) {
  return (
    <span
      className={`distintivo distintivo--${citacao.metodo === 'ocr' ? 'atencao' : 'acento'}`}
      title={citacao.secao ?? undefined}
    >
      {rotulo(citacao)}
      {citacao.metodo === 'ocr' && ' · OCR'}
    </span>
  )
}

function rotulo(citacao: Citacao): string {
  const paginas =
    citacao.pagina_inicial === citacao.pagina_final
      ? `p. ${citacao.pagina_inicial}`
      : `p. ${citacao.pagina_inicial}–${citacao.pagina_final}`
  return `${citacao.documento}, ${paginas}`
}
