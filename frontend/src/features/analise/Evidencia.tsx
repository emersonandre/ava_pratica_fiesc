import type { Evidencia as TipoEvidencia } from '../../api/types'
import { dataCurta, numero, rotuloFamilia } from '../../lib/formato'
import './Evidencia.css'

/** Os numeros que a secao 3 do enunciado pede: quantos eventos semelhantes ja
 * ocorreram, como se distribuem no tempo, com que frequencia e em que condicao
 * operacional.
 *
 * Todos vem do banco. Nenhum passa pelo modelo de linguagem -- e a razao de
 * ficarem em um painel proprio, separado do procedimento gerado.
 */
export function Evidencia({
  evidencia,
  familia,
}: {
  evidencia: TipoEvidencia
  familia: string | null
}) {
  const contexto = evidencia.contexto_operacional
  const maximo = Math.max(...evidencia.linha_do_tempo.map((p) => p.total), 1)

  return (
    <section className="painel">
      <div className="painel-cabecalho">
        <h2>Histórico da família</h2>
        <span className="fraco">medido no banco, sem passar pelo modelo</span>
      </div>

      <div className="painel-corpo evidencia">
        <dl className="evidencia-numeros">
          <Numero
            rotulo="Vizinhos da família"
            valor={String(evidencia.vizinhos_da_familia)}
            nota="entre os mais próximos"
          />
          <Numero
            rotulo="Ocorrências no histórico"
            valor={numero(evidencia.eventos_da_familia)}
            nota={
              familia ? `leituras de ${rotuloFamilia(familia).toLowerCase()}` : 'leituras'
            }
          />
          <Numero
            rotulo="Frequência"
            valor={numero(Math.round(evidencia.frequencia_por_dia))}
            nota="leituras por dia"
          />
          <Numero
            rotulo="Intervalo médio"
            valor={
              evidencia.intervalo_medio_horas !== null
                ? `${(evidencia.intervalo_medio_horas * 60).toFixed(1)}`
                : '—'
            }
            nota="minutos entre leituras"
          />
        </dl>

        <div className="evidencia-periodo">
          <p className="rotulo">Distribuição no histórico</p>
          <div className="faixas">
            {evidencia.linha_do_tempo.map((ponto) => (
              <span key={ponto.dia} className="faixa" title={`${dataCurta(ponto.dia)}: ${numero(ponto.total)} leituras`}>
                <span
                  className="faixa-barra"
                  style={{
                    height: `${(ponto.total / maximo) * 100}%`,
                    background: familia ? `var(--f-${familia}, var(--instrumento))` : 'var(--instrumento)',
                  }}
                />
                <span className="faixa-rotulo dado">{dataCurta(ponto.dia)}</span>
              </span>
            ))}
          </div>
          {evidencia.primeiro_registro && evidencia.ultimo_registro && (
            <p className="fraco evidencia-nota">
              De {dataCurta(evidencia.primeiro_registro)} a{' '}
              {dataCurta(evidencia.ultimo_registro)}.
            </p>
          )}
        </div>

        {contexto && (
          <div className="evidencia-contexto">
            <p className="rotulo">Condição operacional das ocorrências</p>
            <dl className="faixa-valores">
              <div>
                <dt>Rotação</dt>
                <dd className="dado">
                  {contexto.rpm_min.toFixed(0)} – {contexto.rpm_max.toFixed(0)}{' '}
                  <span className="fraco">rpm · média {contexto.rpm_medio.toFixed(0)}</span>
                </dd>
              </div>
              <div>
                <dt>Temperatura</dt>
                <dd className="dado">
                  {contexto.temp_min.toFixed(1)} – {contexto.temp_max.toFixed(1)}{' '}
                  <span className="fraco">°C · média {contexto.temp_media.toFixed(1)}</span>
                </dd>
              </div>
            </dl>
          </div>
        )}
      </div>
    </section>
  )
}

function Numero({
  rotulo,
  valor,
  nota,
}: {
  rotulo: string
  valor: string
  nota: string
}) {
  return (
    <div className="evidencia-numero">
      <dt className="rotulo">{rotulo}</dt>
      <dd>
        <span className="dado evidencia-valor">{valor}</span>
        <span className="fraco evidencia-unidade">{nota}</span>
      </dd>
    </div>
  )
}
