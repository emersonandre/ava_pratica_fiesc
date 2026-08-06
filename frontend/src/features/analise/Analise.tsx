import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { useAmostra, useAnalisar, useFamilias } from '../../api/queries'
import type { AmostraHoldout, EventoSensor, RespostaAnalise } from '../../api/types'
import { COLUNAS_SENSOR } from '../../api/types'
import { BarraDeVotos } from '../../components/BarraDeVotos'
import { Erro } from '../../components/Estado'
import { Selo } from '../../components/Selo'
import { duracao, porcento, rotuloFamilia } from '../../lib/formato'
import { Evidencia } from './Evidencia'
import { Prescricao } from './Prescricao'
import { Vizinhos } from './Vizinhos'
import './Analise.css'

function paraEvento(amostra: AmostraHoldout): EventoSensor {
  const evento = {} as EventoSensor
  for (const coluna of COLUNAS_SENSOR) evento[coluna] = amostra[coluna]
  return evento
}

export function Analise() {
  const [parametros] = useSearchParams()
  const familiaAlvo = parametros.get('familia') ?? undefined

  const [amostraAtual, setAmostraAtual] = useState<AmostraHoldout | null>(null)
  const [pergunta, setPergunta] = useState('Como corrigir esta falha?')

  const familias = useFamilias()
  const amostra = useAmostra()
  const analise = useAnalisar()

  // Carrega uma amostra ao abrir, ja filtrada pela familia vinda do painel.
  useEffect(() => {
    amostra.mutate(familiaAlvo, { onSuccess: setAmostraAtual })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [familiaAlvo])

  function sortear(familia?: string) {
    analise.reset()
    amostra.mutate(familia, { onSuccess: setAmostraAtual })
  }

  function analisar() {
    if (!amostraAtual) return
    analise.mutate({ ...paraEvento(amostraAtual), pergunta })
  }

  const resposta = analise.data

  return (
    <>
      <header className="pagina-cabecalho">
        <h1>Análise de evento</h1>
        <p>
          Cada leitura vem do conjunto de teste — dados de 10 a 16 de junho, que o
          sistema nunca usou para aprender. O rótulo real aparece ao lado do
          diagnóstico, acerto ou erro.
        </p>
      </header>

      <section className="painel entrada">
        <div className="painel-cabecalho">
          <h2>Leitura do sensor</h2>
          {familias.data && (
            <select
              className="seletor"
              value={familiaAlvo ?? ''}
              onChange={(e) => sortear(e.target.value || undefined)}
              aria-label="Filtrar por família"
            >
              <option value="">Qualquer família</option>
              {familias.data
                .filter((f) => f.e_problema)
                .map((f) => (
                  <option key={f.familia} value={f.familia}>
                    {rotuloFamilia(f.familia)}
                    {f.coberta ? '' : ' — sem documento'}
                  </option>
                ))}
            </select>
          )}
        </div>

        <div className="painel-corpo entrada-corpo">
          {amostra.isError && (
            <Erro erro={amostra.error} aoTentarNovamente={() => sortear(familiaAlvo)} />
          )}

          {amostraAtual && (
            <>
              <dl className="leitura">
                <Medida rotulo="Registro" valor={`#${amostraAtual.id}`} />
                <Medida rotulo="Rotação" valor={amostraAtual.rpm} unidade="rpm" />
                <Medida
                  rotulo="Temperatura"
                  valor={amostraAtual.temperature_c}
                  unidade="°C"
                />
                <Medida
                  rotulo="Velocidade RMS Z"
                  valor={amostraAtual.z_rms_velocity_mm_s}
                  unidade="mm/s"
                />
                <Medida
                  rotulo="Velocidade RMS X"
                  valor={amostraAtual.x_rms_velocity_mm_s}
                  unidade="mm/s"
                />
                <Medida rotulo="Kurtosis Z" valor={amostraAtual.z_kurtosis} />
                <Medida rotulo="Crest factor Z" valor={amostraAtual.z_crest_factor} />
                <Medida
                  rotulo="Freq. de pico Z"
                  valor={amostraAtual.z_peak_vel_comp_freq_hz}
                  unidade="Hz"
                />
              </dl>

              <div className="entrada-acoes">
                <label className="campo">
                  <span className="rotulo">Pergunta ao assistente</span>
                  <input
                    value={pergunta}
                    onChange={(e) => setPergunta(e.target.value)}
                    placeholder="Como corrigir esta falha?"
                  />
                </label>

                <button
                  type="button"
                  className="botao"
                  onClick={() => sortear(familiaAlvo)}
                  disabled={amostra.isPending}
                >
                  Outra leitura
                </button>

                <button
                  type="button"
                  className="botao botao-primario"
                  onClick={analisar}
                  disabled={analise.isPending || !amostraAtual}
                >
                  {analise.isPending ? 'Analisando…' : 'Analisar'}
                </button>
              </div>

              {analise.isPending && (
                <p className="aviso-espera">
                  A geração do procedimento leva de 30 a 70 segundos. O modelo usado
                  raciocina antes de escrever.
                </p>
              )}
            </>
          )}
        </div>
      </section>

      {analise.isError && <Erro erro={analise.error} aoTentarNovamente={analisar} />}

      {resposta && amostraAtual && (
        <Resultado resposta={resposta} rotuloReal={amostraAtual.fault_family} />
      )}
    </>
  )
}

function Resultado({
  resposta,
  rotuloReal,
}: {
  resposta: RespostaAnalise
  rotuloReal: string
}) {
  const { diagnostico, cobertura, tempos } = resposta
  const acertou = diagnostico.familia === rotuloReal

  return (
    <>
      <section className="painel diagnostico">
        <div className="painel-corpo">
          <div className="diagnostico-topo">
            <div>
              <p className="rotulo">Diagnóstico por similaridade</p>
              <p className="diagnostico-familia">
                {diagnostico.familia
                  ? rotuloFamilia(diagnostico.familia)
                  : 'Sem diagnóstico'}
              </p>
              <p className="diagnostico-comparacao">
                rótulo real:{' '}
                <b style={{ color: acertou ? 'var(--zona-a)' : 'var(--zona-c)' }}>
                  {rotuloFamilia(rotuloReal)}
                </b>
                <span className="fraco">
                  {' '}
                  · {acertou ? 'coincide' : 'não coincide'}
                </span>
              </p>
            </div>

            <div className="diagnostico-estado">
              <Selo motivo={cobertura.motivo} />
              <p className="diagnostico-confianca dado">
                {porcento(diagnostico.confianca)}
                <span className="rotulo"> concordância</span>
              </p>
            </div>
          </div>

          <BarraDeVotos votos={diagnostico.votos} />

          {diagnostico.aviso && <p className="diagnostico-aviso">{diagnostico.aviso}</p>}

          <dl className="tempos">
            <Tempo rotulo="Similaridade" ms={tempos.similaridade_ms} />
            <Tempo rotulo="Cobertura" ms={tempos.cobertura_ms} />
            <Tempo rotulo="Busca documental" ms={tempos.recuperacao_ms} />
            <Tempo rotulo="Geração" ms={tempos.geracao_ms} />
            <Tempo rotulo="Verificação" ms={tempos.verificacao_ms} />
            <Tempo rotulo="Total" ms={tempos.total_ms} destaque />
          </dl>
        </div>
      </section>

      <Prescricao resposta={resposta} />

      {resposta.evidencia && (
        <Evidencia evidencia={resposta.evidencia} familia={diagnostico.familia} />
      )}

      <Vizinhos vizinhos={resposta.vizinhos} rotuloReal={rotuloReal} />
    </>
  )
}

function Medida({
  rotulo,
  valor,
  unidade,
}: {
  rotulo: string
  valor: number | string
  unidade?: string
}) {
  return (
    <div className="medida">
      <dt className="rotulo">{rotulo}</dt>
      <dd className="dado">
        {typeof valor === 'number' ? valor.toFixed(3).replace(/\.?0+$/, '') : valor}
        {unidade && <span className="medida-unidade"> {unidade}</span>}
      </dd>
    </div>
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
    <div className={`tempo ${destaque ? 'tempo--destaque' : ''}`}>
      <dt>{rotulo}</dt>
      <dd className="dado">{ms > 0 ? duracao(ms) : '—'}</dd>
    </div>
  )
}
