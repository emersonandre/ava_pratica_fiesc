import type { VotoFamilia } from '../api/types'
import { corDaFamilia, porcento, rotuloFamilia } from '../lib/formato'
import './BarraDeVotos.css'

/** Distribuicao do voto da vizinhanca, com o limiar de decisao marcado.
 *
 * Este e o componente central da interface, e ele existe porque a confianca do
 * sistema **e** a concentracao deste voto -- nao uma barra de progresso abstrata.
 *
 * Mostrar so a familia vencedora esconderia a informacao que mais importa: um
 * diagnostico de 51% contra 49% e um de 98% contra 2% nao merecem a mesma
 * leitura. Com as bandas lado a lado e o marcador do limiar, quem olha entende
 * na hora por que o sistema decidiu ou se absteve.
 */
export function BarraDeVotos({
  votos,
  limiar = 0.7,
}: {
  votos: VotoFamilia[]
  limiar?: number
}) {
  if (votos.length === 0) return null

  const vencedor = votos[0]!
  const decidiu = vencedor.peso >= limiar

  return (
    <figure className="votos">
      <div
        className="votos-trilha"
        role="img"
        aria-label={`Voto da vizinhanca: ${votos
          .slice(0, 4)
          .map((v) => `${rotuloFamilia(v.fault_family)} ${porcento(v.peso)}`)
          .join(', ')}. Limiar de decisao em ${porcento(limiar)}.`}
      >
        {votos.map((voto) => (
          <span
            key={voto.fault_family}
            className="votos-banda"
            style={{
              width: `${voto.peso * 100}%`,
              background: corDaFamilia(voto.fault_family),
            }}
            title={`${rotuloFamilia(voto.fault_family)} — ${voto.vizinhos} vizinhos, ${porcento(voto.peso, 1)}`}
          />
        ))}

        <span
          className={`votos-limiar ${decidiu ? 'votos-limiar--cruzado' : ''}`}
          style={{ left: `${limiar * 100}%` }}
        >
          <span className="votos-limiar-rotulo">limiar {porcento(limiar)}</span>
        </span>
      </div>

      <figcaption className="votos-legenda">
        {votos.slice(0, 4).map((voto) => (
          <span key={voto.fault_family} className="votos-item">
            <span
              className="votos-marca"
              style={{ background: corDaFamilia(voto.fault_family) }}
            />
            {rotuloFamilia(voto.fault_family)}
            <b className="dado">{porcento(voto.peso)}</b>
            <span className="fraco">{voto.vizinhos} viz.</span>
          </span>
        ))}
        {votos.length > 4 && (
          <span className="votos-item fraco">+{votos.length - 4} familias</span>
        )}
      </figcaption>
    </figure>
  )
}
