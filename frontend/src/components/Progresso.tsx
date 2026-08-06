import { useEffect, useState } from 'react'

import './Progresso.css'

/** Indicador de progresso para operacoes longas.
 *
 * A geracao do procedimento leva cerca de 45 segundos e nao ha como reportar
 * progresso real -- o modelo nao emite eventos de etapa. Em vez de fingir uma
 * porcentagem, o componente mostra as etapas do pipeline e avanca por tempo
 * estimado, com o cronometro a vista.
 *
 * Mostrar o tempo decorrido e mais honesto que uma barra que finge saber quanto
 * falta: quem espera consegue julgar se travou.
 */
export function Progresso({
  etapas,
  estimativaSegundos,
}: {
  etapas: string[]
  estimativaSegundos: number
}) {
  const [decorrido, setDecorrido] = useState(0)

  useEffect(() => {
    const inicio = Date.now()
    const relogio = setInterval(() => {
      setDecorrido((Date.now() - inicio) / 1000)
    }, 200)
    return () => clearInterval(relogio)
  }, [])

  const fracao = Math.min(decorrido / estimativaSegundos, 0.97)
  const etapaAtual = Math.min(
    Math.floor(fracao * etapas.length),
    etapas.length - 1,
  )
  const passouDoPrazo = decorrido > estimativaSegundos

  return (
    <div className="progresso" role="status" aria-live="polite">
      <div className="progresso-topo">
        <span className="progresso-etapa">{etapas[etapaAtual]}</span>
        <span className="dado t3">{decorrido.toFixed(0)} s</span>
      </div>

      <div className="progresso-trilha">
        <span className="progresso-barra" style={{ width: `${fracao * 100}%` }} />
      </div>

      <ol className="progresso-lista">
        {etapas.map((etapa, indice) => (
          <li
            key={etapa}
            className={
              indice < etapaAtual
                ? 'progresso-item progresso-item--feito'
                : indice === etapaAtual
                  ? 'progresso-item progresso-item--atual'
                  : 'progresso-item'
            }
          >
            <span className="progresso-marca" />
            {etapa}
          </li>
        ))}
      </ol>

      <p className="t3 progresso-nota">
        {passouDoPrazo
          ? 'Está demorando mais que o normal, mas continua processando.'
          : `Leva cerca de ${estimativaSegundos} segundos. O modelo raciocina antes de escrever.`}
      </p>
    </div>
  )
}

/** Indicador curto, para operacoes de poucos segundos. */
export function Girando({ texto }: { texto: string }) {
  return (
    <span className="girando" role="status">
      <span className="girando-anel" aria-hidden="true" />
      {texto}
    </span>
  )
}
