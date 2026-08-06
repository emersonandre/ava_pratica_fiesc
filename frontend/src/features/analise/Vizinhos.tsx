import type { Vizinho } from '../../api/types'
import { corDaFamilia, dataHora, porcento } from '../../lib/formato'
import './Vizinhos.css'

/** Os eventos historicos mais parecidos com a leitura analisada.
 *
 * A similaridade aparece em barra e em numero: a barra da leitura imediata, o
 * numero permite comparacao precisa na discussao tecnica.
 */
export function Vizinhos({
  vizinhos,
  rotuloReal,
}: {
  vizinhos: Vizinho[]
  rotuloReal: string
}) {
  if (vizinhos.length === 0) return null

  return (
    <section className="painel">
      <div className="painel-cabecalho">
        <h2>Eventos históricos semelhantes</h2>
        <span className="fraco">
          {vizinhos.length} mais próximos, todos anteriores a 10/06
        </span>
      </div>

      <div className="painel-corpo painel-corpo--tabela">
        <table className="tabela-vizinhos">
          <thead>
            <tr>
              <th>Registro</th>
              <th>Data</th>
              <th>Condição anotada</th>
              <th>Semelhança</th>
              <th className="num">rpm</th>
              <th className="num">°C</th>
            </tr>
          </thead>
          <tbody>
            {vizinhos.slice(0, 15).map((vizinho) => (
              <tr key={vizinho.id}>
                <td className="dado fraco">#{vizinho.id}</td>
                <td className="dado">{dataHora(vizinho.created_at)}</td>
                <td>
                  <span className="vizinho-familia">
                    <span
                      className="familia-marca"
                      style={{ background: corDaFamilia(vizinho.fault_family) }}
                    />
                    {vizinho.canonical_fault}
                    {vizinho.fault_family === rotuloReal && (
                      <span className="vizinho-igual" title="mesma família do rótulo real">
                        =
                      </span>
                    )}
                  </span>
                </td>
                <td>
                  <span className="semelhanca">
                    <span className="semelhanca-trilha">
                      <span
                        className="semelhanca-barra"
                        style={{
                          width: `${Math.max(0, (vizinho.similarity - 0.8) / 0.2) * 100}%`,
                          background: corDaFamilia(vizinho.fault_family),
                        }}
                      />
                    </span>
                    <b className="dado">{porcento(vizinho.similarity, 1)}</b>
                  </span>
                </td>
                <td className="num">{vizinho.rpm.toFixed(0)}</td>
                <td className="num">{vizinho.temperature_c.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {vizinhos.length > 15 && (
          <p className="fraco tabela-nota">
            Mostrando 15 de {vizinhos.length}. A votação considera todos.
          </p>
        )}
        <p className="fraco tabela-nota">
          A barra tem escala de 80% a 100% de semelhança. Numa escala de 0 a 100 as
          diferenças entre vizinhos ficariam invisíveis — todos passam de 0,85.
        </p>
      </div>
    </section>
  )
}
