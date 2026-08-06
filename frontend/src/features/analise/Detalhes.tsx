import { useState } from 'react'

import type { RespostaAnalise } from '../../api/types'
import { corDaFamilia, dataHora, duracao, numero, porcento } from '../../lib/formato'
import './Detalhes.css'

/** Dados que sustentam o diagnostico.
 *
 * Recolhido por padrao. Quem opera precisa da conclusao; quem audita precisa da
 * evidencia. Deixar tudo aberto o tempo todo serve mal aos dois.
 */
export function Detalhes({ resultado }: { resultado: RespostaAnalise }) {
  const [aberto, setAberto] = useState(false)
  const { evidencia, vizinhos, tempos } = resultado

  return (
    <section className="detalhes">
      <button
        type="button"
        className="detalhes-alternar"
        onClick={() => setAberto(!aberto)}
        aria-expanded={aberto}
      >
        <span>{aberto ? '−' : '+'}</span>
        Dados que sustentam este resultado
        <span className="t3">
          {vizinhos.length} leituras comparadas · {duracao(tempos.total_ms)}
        </span>
      </button>

      {aberto && (
        <div className="detalhes-corpo">
          {evidencia && (
            <div className="cartao detalhes-bloco">
              <h3>Histórico desta falha</h3>
              <dl className="detalhes-numeros">
                <div>
                  <dt className="rotulo">Ocorrências registradas</dt>
                  <dd className="dado">{numero(evidencia.eventos_da_familia)}</dd>
                </div>
                <div>
                  <dt className="rotulo">Entre as mais parecidas</dt>
                  <dd className="dado">{evidencia.vizinhos_da_familia}</dd>
                </div>
                <div>
                  <dt className="rotulo">Média por dia</dt>
                  <dd className="dado">{numero(Math.round(evidencia.frequencia_por_dia))}</dd>
                </div>
                {evidencia.contexto_operacional && (
                  <div>
                    <dt className="rotulo">Faixa de rotação</dt>
                    <dd className="dado">
                      {evidencia.contexto_operacional.rpm_min.toFixed(0)}–
                      {evidencia.contexto_operacional.rpm_max.toFixed(0)}
                      <span className="t3"> RPM</span>
                    </dd>
                  </div>
                )}
              </dl>
              <p className="t3 detalhes-nota">
                Números vindos direto do banco. Nenhum passou pelo modelo de linguagem.
              </p>
            </div>
          )}

          <div className="cartao detalhes-bloco">
            <h3>Leituras mais parecidas</h3>
            <table>
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Condição anotada</th>
                  <th className="num">Semelhança</th>
                  <th className="num">RPM</th>
                </tr>
              </thead>
              <tbody>
                {vizinhos.slice(0, 8).map((vizinho) => (
                  <tr key={vizinho.id}>
                    <td className="dado t2">{dataHora(vizinho.created_at)}</td>
                    <td>
                      <span className="vizinho">
                        <i style={{ background: corDaFamilia(vizinho.fault_family) }} />
                        {vizinho.canonical_fault}
                      </span>
                    </td>
                    <td className="num">{porcento(vizinho.similarity, 1)}</td>
                    <td className="num t2">{vizinho.rpm.toFixed(0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="t3 detalhes-nota">
              Mostrando 8 das {vizinhos.length} usadas na votação. Todas anteriores a
              10/06 — o sistema nunca compara uma leitura com ela mesma.
            </p>
          </div>

          <div className="cartao detalhes-bloco">
            <h3>Tempo de cada etapa</h3>
            <dl className="detalhes-tempos">
              <Tempo rotulo="Comparar com o histórico" ms={tempos.similaridade_ms} />
              <Tempo rotulo="Verificar documentação" ms={tempos.cobertura_ms} />
              <Tempo rotulo="Buscar trechos" ms={tempos.recuperacao_ms} />
              <Tempo rotulo="Redigir resposta" ms={tempos.geracao_ms} />
              <Tempo rotulo="Conferir citações" ms={tempos.verificacao_ms} />
              <Tempo rotulo="Total" ms={tempos.total_ms} destaque />
            </dl>
          </div>
        </div>
      )}
    </section>
  )
}

function Tempo({
  rotulo,
  ms,
  destaque,
}: {
  rotulo: string
  ms: number
  destaque?: boolean
}) {
  return (
    <div className={destaque ? 'tempo--destaque' : ''}>
      <dt className="rotulo">{rotulo}</dt>
      <dd className="dado">{ms > 0 ? duracao(ms) : '—'}</dd>
    </div>
  )
}
