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
export interface Etapa {
  texto: string
  /** Duracao relativa medida. Uma etapa de 0,7ms nao pode ocupar um terco. */
  peso: number
}

export function Progresso({
  etapas,
  estimativaSegundos,
}: {
  etapas: Etapa[]
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

  // A etapa sai do peso acumulado, e nao de dividir a barra em partes iguais:
  // com partes iguais o indicador anuncia a ultima etapa quando ela ainda nem
  // comecou, e quem espera acha que travou nela.
  const total = etapas.reduce((soma, etapa) => soma + etapa.peso, 0)
  let acumulado = 0
  let etapaAtual = etapas.length - 1
  for (const [indice, etapa] of etapas.entries()) {
    acumulado += etapa.peso
    if (fracao < acumulado / total) {
      etapaAtual = indice
      break
    }
  }

  const passouDoPrazo = decorrido > estimativaSegundos

  return (
    <div className="progresso" role="status" aria-live="polite">
      <div className="progresso-topo">
        <span className="progresso-etapa">{etapas[etapaAtual]?.texto}</span>
        <span className="dado t3">{decorrido.toFixed(0)} s</span>
      </div>

      <div className="progresso-trilha">
        <span className="progresso-barra" style={{ width: `${fracao * 100}%` }} />
      </div>

      <ol className="progresso-lista">
        {etapas.map((etapa, indice) => (
          <li
            key={etapa.texto}
            className={
              indice < etapaAtual
                ? 'progresso-item progresso-item--feito'
                : indice === etapaAtual
                  ? 'progresso-item progresso-item--atual'
                  : 'progresso-item'
            }
          >
            <span className="progresso-marca" />
            {etapa.texto}
          </li>
        ))}
      </ol>

      <p className="t3 progresso-nota">
        {passouDoPrazo
          ? 'Está demorando mais que o normal. Se passar de três minutos, a requisição é encerrada e o erro aparece aqui.'
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
