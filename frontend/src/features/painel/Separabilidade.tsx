import { useState } from 'react'

import { useDistribuicao } from '../../api/queries'
import { Carregando, Erro } from '../../components/Estado'
import { corDaFamilia, rotuloFamilia } from '../../lib/formato'
import './Separabilidade.css'

/** Por que o sistema erra: as faixas se sobrepoem.
 *
 * Este e o grafico que sustenta o numero mais desconfortavel do projeto -- 40%
 * de acerto. A leitura de uma falha de rolamento e a de um desbalanceamento
 * ocupam quase a mesma faixa de vibracao, entao nenhum metodo que compare
 * numeros separa as duas de forma confiavel.
 *
 * Um classificador supervisionado treinado nos mesmos dados chega a 39,8%: o
 * teto e o sensor, nao a tecnica. Mostrar isso vale mais que esconder.
 */

const METRICAS: { coluna: string; rotulo: string }[] = [
  { coluna: 'z_rms_velocity_mm_s', rotulo: 'Vibração (velocidade RMS)' },
  { coluna: 'z_peak_acceleration_g', rotulo: 'Impacto (aceleração de pico)' },
  { coluna: 'z_kurtosis', rotulo: 'Curtose' },
  { coluna: 'z_crest_factor', rotulo: 'Fator de crista' },
  { coluna: 'z_high_freq_rms_accel_g', rotulo: 'Alta frequência' },
  { coluna: 'temperature_c', rotulo: 'Temperatura' },
]

export function Separabilidade() {
  const [metrica, setMetrica] = useState('z_rms_velocity_mm_s')
  const consulta = useDistribuicao(metrica)

  return (
    <section className="cartao">
      <div className="cartao-topo">
        <div>
          <h2>Por que nem toda leitura tem diagnóstico</h2>
          <p className="t3">
            Faixa de valores de cada tipo de falha. Quanto mais as barras se
            sobrepõem, mais difícil separar uma falha da outra pelo sensor.
          </p>
        </div>
        <select
          aria-label="Métrica exibida"
          value={metrica}
          onChange={(evento) => setMetrica(evento.target.value)}
        >
          {METRICAS.map((item) => (
            <option key={item.coluna} value={item.coluna}>
              {item.rotulo}
            </option>
          ))}
        </select>
      </div>

      <div className="cartao-corpo">
        {consulta.isLoading && <Carregando altura="18rem" />}
        {consulta.isError && (
          <Erro erro={consulta.error} aoTentarNovamente={consulta.refetch} />
        )}
        {consulta.data && <Faixas dados={consulta.data} />}
      </div>
    </section>
  )
}

function Faixas({
  dados,
}: {
  dados: {
    unidade: string
    familias: {
      familia: string
      leituras: number
      p10: number
      p25: number
      mediana: number
      p75: number
      p90: number
    }[]
  }
}) {
  const familias = dados.familias
  if (familias.length === 0) return <p className="fraco">Sem dados.</p>

  // Escala comum a todas as linhas: e a sobreposicao que interessa, e cada
  // familia com sua propria escala esconderia exatamente isso.
  const minimo = Math.min(...familias.map((f) => f.p10))
  const maximo = Math.max(...familias.map((f) => f.p90))
  const faixa = maximo - minimo || 1
  const posicao = (valor: number) => ((valor - minimo) / faixa) * 100

  const casas = maximo < 10 ? 2 : maximo < 100 ? 1 : 0
  const formatar = (valor: number) =>
    `${valor.toFixed(casas)}${dados.unidade ? ` ${dados.unidade}` : ''}`

  return (
    <>
      <div className="faixas">
        {familias.map((f) => (
          <div key={f.familia} className="faixa">
            <span className="faixa-nome">{rotuloFamilia(f.familia)}</span>

            <div
              className="faixa-trilho"
              title={`${rotuloFamilia(f.familia)} — mediana ${formatar(f.mediana)}, metade das leituras entre ${formatar(f.p25)} e ${formatar(f.p75)}`}
            >
              {/* p10-p90: onde caem nove em cada dez leituras. */}
              <span
                className="faixa-extremos"
                style={{
                  left: `${posicao(f.p10)}%`,
                  width: `${posicao(f.p90) - posicao(f.p10)}%`,
                  background: corDaFamilia(f.familia),
                }}
              />
              {/* p25-p75: a metade central, opaca por cima. */}
              <span
                className="faixa-central"
                style={{
                  left: `${posicao(f.p25)}%`,
                  width: `${posicao(f.p75) - posicao(f.p25)}%`,
                  background: corDaFamilia(f.familia),
                }}
              />
              <span
                className="faixa-mediana"
                style={{ left: `${posicao(f.mediana)}%` }}
              />
            </div>

            <span className="faixa-valor">{formatar(f.mediana)}</span>
          </div>
        ))}
      </div>

      <div className="faixa-escala">
        <span>{formatar(minimo)}</span>
        <span>{formatar(maximo)}</span>
      </div>

      <p className="fraco grafico-nota">
        A barra escura marca a metade central das leituras; a clara, nove em cada
        dez. O traço é a mediana. Onde duas barras ocupam o mesmo espaço, as duas
        falhas produzem leituras parecidas — e é por isso que o sistema prefere
        dizer que não sabe a arriscar um palpite.
      </p>
    </>
  )
}
