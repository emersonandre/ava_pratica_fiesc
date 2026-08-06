import { useFrequencia } from '../../api/queries'
import { Carregando, Erro } from '../../components/Estado'
import { corDaFamilia, dataCurta, numero, rotuloFamilia } from '../../lib/formato'
import './Recorrencia.css'

/** Com que frequência cada falha aparece.
 *
 * A seção 1 do enunciado pede "quantidade de ocorrências" e "frequência" na
 * saída do sistema. A resposta de um evento traz os dois números da família
 * diagnosticada; aqui eles aparecem lado a lado, que é a visão de quem decide
 * onde investir manutenção.
 *
 * Contado em dias, e não em leituras: o coletor amostra a cada poucos segundos
 * durante um ensaio, então "leituras por dia" mede a cadência do equipamento e
 * não a recorrência do defeito.
 */
export function Recorrencia() {
  const consulta = useFrequencia()

  return (
    <section className="cartao">
      <div className="cartao-topo">
        <div>
          <h2>Com que frequência cada falha aparece</h2>
          <p className="t3">
            Em quantos dias distintos o problema foi registrado, e de quanto em
            quanto tempo ele volta
          </p>
        </div>
      </div>

      <div className="cartao-corpo">
        {consulta.isLoading && <Carregando altura="16rem" />}
        {consulta.isError && (
          <Erro erro={consulta.error} aoTentarNovamente={consulta.refetch} />
        )}
        {consulta.data && <Tabela linhas={consulta.data.filter((f) => f.e_problema)} />}
      </div>
    </section>
  )
}

function Tabela({
  linhas,
}: {
  linhas: {
    familia: string
    leituras: number
    primeira: string
    ultima: string
    dias_com_ocorrencia: number
    leituras_por_dia: number
    intervalo_medio_dias: number | null
  }[]
}) {
  if (linhas.length === 0) return <p className="fraco">Sem ocorrências registradas.</p>

  const maximo = Math.max(...linhas.map((l) => l.dias_com_ocorrencia))

  return (
    <>
      <div className="recorrencia">
        {linhas.map((l) => (
          <div key={l.familia} className="recorrencia-linha">
            <span className="recorrencia-nome">
              <i style={{ background: corDaFamilia(l.familia) }} />
              {rotuloFamilia(l.familia)}
            </span>

            <div className="recorrencia-barra">
              <span
                style={{
                  width: `${(l.dias_com_ocorrencia / maximo) * 100}%`,
                  background: corDaFamilia(l.familia),
                }}
              />
            </div>

            <span className="recorrencia-dias">
              {l.dias_com_ocorrencia} {l.dias_com_ocorrencia === 1 ? 'dia' : 'dias'}
            </span>

            <span className="recorrencia-intervalo t3">
              {l.intervalo_medio_dias === null
                ? 'registrado num dia só'
                : `volta a cada ${l.intervalo_medio_dias.toFixed(1)} dias`}
            </span>

            <span className="recorrencia-periodo t3">
              {dataCurta(l.primeira)} — {dataCurta(l.ultima)}
            </span>

            <span className="recorrencia-total">{numero(l.leituras)}</span>
          </div>
        ))}
      </div>

      <p className="fraco grafico-nota">
        A barra mostra em quantos dias distintos a falha foi registrada. O número
        à direita é o total de leituras — alto porque o sensor amostra a cada
        poucos segundos enquanto o ensaio roda, e não porque a falha se repetiu
        esse tanto de vezes.
      </p>
    </>
  )
}
