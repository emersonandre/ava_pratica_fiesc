import { useEffect, useRef, useState } from 'react'

import type { Citacao } from '../../api/types'
import './Citacoes.css'

/** Citacao clicavel: abre o trecho que o modelo realmente leu.
 *
 * Uma citacao que so aponta documento e pagina pede confianca. Como o trecho
 * recuperado ja vem na resposta -- e o mesmo texto que foi para o prompt --, um
 * clique mostra a fonte e o operador confere se a frase esta mesmo la, sem sair
 * da tela nem abrir o PDF.
 */

export function rotuloCitacao(citacao: Citacao): string {
  const paginas =
    citacao.pagina_inicial === citacao.pagina_final
      ? `p. ${citacao.pagina_inicial}`
      : `p. ${citacao.pagina_inicial}–${citacao.pagina_final}`
  return `${citacao.documento}, ${paginas}`
}

export function FonteCitacao({
  citacao,
  chaves = false,
}: {
  citacao: Citacao
  /** Rotulo entre colchetes, como aparece no meio do texto de um passo. */
  chaves?: boolean
}) {
  const [aberto, setAberto] = useState(false)
  const temTrecho = Boolean(citacao.trecho?.trim())
  const texto = chaves ? `[${rotuloCitacao(citacao)}]` : rotuloCitacao(citacao)

  // Sem trecho nao ha o que abrir; vira rotulo comum em vez de um botao que
  // nao faz nada.
  if (!temTrecho) {
    return (
      <span
        className={`fonte fonte--${citacao.metodo === 'ocr' ? 'ocr' : 'texto'}`}
        title={citacao.secao ?? undefined}
      >
        {texto}
      </span>
    )
  }

  return (
    <>
      <button
        type="button"
        className={`fonte fonte--acionavel fonte--${citacao.metodo === 'ocr' ? 'ocr' : 'texto'}`}
        onClick={() => setAberto(true)}
        title="Ver o trecho citado"
      >
        {texto}
        {citacao.metodo === 'ocr' && <span className="fonte-ocr">OCR</span>}
      </button>
      {aberto && <PainelTrecho citacao={citacao} aoFechar={() => setAberto(false)} />}
    </>
  )
}

function PainelTrecho({
  citacao,
  aoFechar,
}: {
  citacao: Citacao
  aoFechar: () => void
}) {
  const fechar = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    fechar.current?.focus()
    function aoTeclar(evento: KeyboardEvent) {
      if (evento.key === 'Escape') aoFechar()
    }
    document.addEventListener('keydown', aoTeclar)
    return () => document.removeEventListener('keydown', aoTeclar)
  }, [aoFechar])

  return (
    <div
      className="trecho-fundo"
      role="presentation"
      onClick={(evento) => {
        if (evento.target === evento.currentTarget) aoFechar()
      }}
    >
      <div className="trecho" role="dialog" aria-modal="true" aria-label="Trecho citado">
        <header className="trecho-topo">
          <div>
            <p className="rotulo">Trecho citado</p>
            <h3 className="trecho-titulo">{rotuloCitacao(citacao)}</h3>
            {citacao.secao && <p className="trecho-secao t3">{citacao.secao}</p>}
          </div>
          <button ref={fechar} type="button" className="botao-texto" onClick={aoFechar}>
            Fechar
          </button>
        </header>

        <blockquote className="trecho-corpo">{citacao.trecho}</blockquote>

        <footer className="trecho-rodape t3">
          {citacao.metodo === 'ocr'
            ? 'Página em imagem, transcrita automaticamente por OCR. Confira valores críticos no documento original.'
            : 'Texto extraído diretamente do PDF. É este o conteúdo que foi entregue ao modelo.'}
        </footer>
      </div>
    </div>
  )
}
