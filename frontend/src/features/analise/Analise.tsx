import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import type { Desfecho, PedidoAmostra } from '../../api/queries'
import { useAmostra, useAnalisar, useFamilias } from '../../api/queries'
import type { AmostraHoldout, EventoSensor, RespostaAnalise } from '../../api/types'
import { COLUNAS_SENSOR } from '../../api/types'
import { Erro } from '../../components/Estado'
import { corDaFamilia, porcento, rotuloFamilia } from '../../lib/formato'
import { Chat } from './Chat'
import { Detalhes } from './Detalhes'
import './Analise.css'

function paraEvento(amostra: AmostraHoldout): EventoSensor {
  const evento = {} as EventoSensor
  for (const coluna of COLUNAS_SENSOR) evento[coluna] = amostra[coluna]
  return evento
}

export function Analise() {
  const [parametros] = useSearchParams()
  const familiaAlvo = parametros.get('familia') ?? undefined

  const [leitura, setLeitura] = useState<AmostraHoldout | null>(null)
  const [familia, setFamilia] = useState(familiaAlvo ?? '')
  const [desfecho, setDesfecho] = useState<Desfecho>('prescricao')
  const [limiar, setLimiar] = useState(0.7)
  const [avancado, setAvancado] = useState(false)

  const familias = useFamilias()
  const amostra = useAmostra()
  const analise = useAnalisar()

  useEffect(() => {
    setFamilia(familiaAlvo ?? '')
    buscar({ familia: familiaAlvo, desfecho: 'prescricao', confiancaMinima: 0.7 })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [familiaAlvo])

  function buscar(pedido: PedidoAmostra) {
    analise.reset()
    amostra.mutate(pedido, { onSuccess: setLeitura })
  }

  function novaLeitura() {
    buscar({ familia: familia || undefined, desfecho, confiancaMinima: limiar })
  }

  function analisar() {
    if (!leitura) return
    analise.mutate({ ...paraEvento(leitura), confianca_minima: limiar })
  }

  const resultado = analise.data

  return (
    <>
      <header className="cabecalho">
        <h1>Analisar uma leitura</h1>
        <p className="t2">
          O sistema compara a leitura com o histórico da máquina, identifica a falha e
          consulta os procedimentos cadastrados para dizer o que fazer.
        </p>
      </header>

      {/* ---------------- passo 1 ---------------- */}
      <section className="passo">
        <div className="passo-marca">
          <span className="passo-numero">1</span>
          <span className="passo-linha" />
        </div>

        <div className="passo-conteudo">
          <h2>Escolher a leitura</h2>
          <p className="t2 passo-nota">
            Vem do conjunto de teste: dados reais de 10 a 16 de junho que o sistema
            nunca usou para aprender.
          </p>

          {amostra.isError && <Erro erro={amostra.error} aoTentarNovamente={novaLeitura} />}

          {leitura && (
            <div className="cartao leitura">
              <div className="leitura-topo">
                <div>
                  <span className="rotulo">Leitura</span>
                  <p className="leitura-id dado">#{leitura.id}</p>
                </div>
                <div className="leitura-verdade">
                  <span className="rotulo">Condição real anotada pelo operador</span>
                  <p
                    className="leitura-familia"
                    style={{ color: corDaFamilia(leitura.fault_family) }}
                  >
                    {rotuloFamilia(leitura.fault_family)}
                  </p>
                </div>
                <button
                  type="button"
                  className="botao"
                  onClick={novaLeitura}
                  disabled={amostra.isPending}
                >
                  {amostra.isPending ? 'Buscando…' : 'Trocar leitura'}
                </button>
              </div>

              <dl className="medidas">
                <Medida rotulo="Rotação" valor={leitura.rpm} unidade="rpm" />
                <Medida rotulo="Temperatura" valor={leitura.temperature_c} unidade="°C" />
                <Medida
                  rotulo="Vibração eixo Z"
                  valor={leitura.z_rms_velocity_mm_s}
                  unidade="mm/s"
                />
                <Medida
                  rotulo="Vibração eixo X"
                  valor={leitura.x_rms_velocity_mm_s}
                  unidade="mm/s"
                />
              </dl>

              <button
                type="button"
                className="botao-texto avancado-alternar"
                onClick={() => setAvancado(!avancado)}
                aria-expanded={avancado}
              >
                {avancado ? '− Ocultar' : '+ Mostrar'} opções de demonstração
              </button>

              {avancado && (
                <div className="avancado">
                  <label className="campo">
                    <span className="rotulo">Tipo de caso</span>
                    <select
                      value={desfecho}
                      onChange={(e) => setDesfecho(e.target.value as Desfecho)}
                    >
                      <option value="prescricao">Falha com procedimento cadastrado</option>
                      <option value="sem_documento">Falha sem procedimento</option>
                      <option value="sem_diagnostico">Sinal ambíguo</option>
                      <option value="qualquer">Sorteio livre</option>
                    </select>
                  </label>

                  <label className="campo">
                    <span className="rotulo">Falha</span>
                    <select value={familia} onChange={(e) => setFamilia(e.target.value)}>
                      <option value="">Todas</option>
                      {(familias.data ?? [])
                        .filter((f) => f.e_problema)
                        .map((f) => (
                          <option key={f.familia} value={f.familia}>
                            {rotuloFamilia(f.familia)}
                            {f.coberta ? '' : ' — sem procedimento'}
                          </option>
                        ))}
                    </select>
                  </label>

                  <label className="campo">
                    <span className="rotulo">
                      Certeza mínima para diagnosticar: {porcento(limiar)}
                    </span>
                    <input
                      type="range"
                      min="0.4"
                      max="0.95"
                      step="0.05"
                      value={limiar}
                      onChange={(e) => setLimiar(Number(e.target.value))}
                    />
                    <span className="t3 campo-dica">
                      Exigir mais certeza faz o sistema responder menos vezes e acertar
                      mais. Abaixo do limite, ele prefere não opinar.
                    </span>
                  </label>
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      {/* ---------------- passo 2 ---------------- */}
      <section className="passo">
        <div className="passo-marca">
          <span className={`passo-numero ${resultado ? 'passo-numero--feito' : ''}`}>
            2
          </span>
          <span className="passo-linha" />
        </div>

        <div className="passo-conteudo">
          <h2>Identificar a falha</h2>
          <p className="t2 passo-nota">
            Busca as leituras mais parecidas no histórico e vê em que elas concordam.
          </p>

          {!resultado && (
            <button
              type="button"
              className="botao botao-primario botao-grande"
              onClick={analisar}
              disabled={!leitura || analise.isPending}
            >
              {analise.isPending ? 'Comparando com o histórico…' : 'Identificar falha'}
            </button>
          )}

          {analise.isError && <Erro erro={analise.error} aoTentarNovamente={analisar} />}

          {resultado && leitura && (
            <Diagnostico resultado={resultado} verdade={leitura.fault_family} />
          )}
        </div>
      </section>

      {/* ---------------- passo 3 ---------------- */}
      {resultado && leitura && (
        <section className="passo passo--ultimo">
          <div className="passo-marca">
            <span className="passo-numero passo-numero--feito">3</span>
          </div>

          <div className="passo-conteudo">
            <h2>Perguntar o que fazer</h2>
            <p className="t2 passo-nota">
              O assistente responde consultando os procedimentos técnicos da falha
              identificada — e diz quando a documentação não cobre a pergunta.
            </p>

            {resultado.cobertura.coberta ? (
              <Chat evento={leitura} limiar={limiar} />
            ) : (
              <SemProcedimento resultado={resultado} />
            )}
          </div>
        </section>
      )}

      {resultado && <Detalhes resultado={resultado} />}
    </>
  )
}

function Diagnostico({
  resultado,
  verdade,
}: {
  resultado: RespostaAnalise
  verdade: string
}) {
  const { diagnostico, cobertura } = resultado
  const acertou = diagnostico.familia === verdade
  const vencedor = diagnostico.votos[0]

  return (
    <div className="cartao diagnostico">
      {diagnostico.familia ? (
        <>
          <div className="diagnostico-linha">
            <div>
              <span className="rotulo">Falha identificada</span>
              <p
                className="diagnostico-nome"
                style={{ color: corDaFamilia(diagnostico.familia) }}
              >
                {rotuloFamilia(diagnostico.familia)}
              </p>
            </div>
            <span className={`distintivo distintivo--${acertou ? 'ok' : 'atencao'}`}>
              {acertou ? 'confere com o rótulo real' : 'diverge do rótulo real'}
            </span>
          </div>

          <p className="diagnostico-frase">
            {vencedor?.vizinhos ?? 0} das {resultado.vizinhos.length} leituras mais
            parecidas do histórico apresentavam esta mesma falha
            <b> ({porcento(diagnostico.confianca)} de concordância)</b>.
          </p>
        </>
      ) : (
        <>
          <div className="diagnostico-linha">
            <div>
              <span className="rotulo">Resultado</span>
              <p className="diagnostico-nome diagnostico-nome--vazio">
                Sinal ambíguo
              </p>
            </div>
            <span className="distintivo distintivo--atencao">sem conclusão</span>
          </div>

          <p className="diagnostico-frase">
            As leituras parecidas do histórico não concordam entre si — a mais votada
            reúne só {porcento(diagnostico.confianca)}. O sistema prefere não opinar a
            arriscar um diagnóstico errado.
          </p>
        </>
      )}

      <div className="votacao">
        <div className="votacao-barra">
          {diagnostico.votos.map((voto) => (
            <span
              key={voto.fault_family}
              style={{
                width: `${voto.peso * 100}%`,
                background: corDaFamilia(voto.fault_family),
              }}
              title={`${rotuloFamilia(voto.fault_family)}: ${porcento(voto.peso)}`}
            />
          ))}
        </div>
        <div className="votacao-legenda">
          {diagnostico.votos.slice(0, 3).map((voto) => (
            <span key={voto.fault_family}>
              <i style={{ background: corDaFamilia(voto.fault_family) }} />
              {rotuloFamilia(voto.fault_family)} {porcento(voto.peso)}
            </span>
          ))}
        </div>
      </div>

      {cobertura.coberta && (
        <p className="diagnostico-fonte t2">
          Procedimento disponível:{' '}
          {cobertura.documentos.map((documento) => (
            <span key={documento.arquivo} className="distintivo distintivo--acento">
              {documento.arquivo}
            </span>
          ))}
        </p>
      )}
    </div>
  )
}

function SemProcedimento({ resultado }: { resultado: RespostaAnalise }) {
  const { recusa } = resultado

  return (
    <div className="cartao sem-procedimento">
      <span className="distintivo distintivo--atencao">Nenhuma recomendação</span>
      <p className="sem-procedimento-texto">
        {recusa?.mensagem ?? 'Não há procedimento cadastrado para esta falha.'}
      </p>
      {recusa?.sugestao && (
        <a href="/documentos" className="botao botao-primario">
          Cadastrar procedimento
        </a>
      )}
      <p className="t3 sem-procedimento-nota">
        O assistente não foi consultado. A decisão de não responder é tomada antes,
        por regra — não depende do modelo se comportar bem.
      </p>
    </div>
  )
}

function Medida({
  rotulo,
  valor,
  unidade,
}: {
  rotulo: string
  valor: number
  unidade: string
}) {
  return (
    <div>
      <dt className="rotulo">{rotulo}</dt>
      <dd className="dado medida-valor">
        {valor.toFixed(2).replace(/\.00$/, '')}
        <span className="t3"> {unidade}</span>
      </dd>
    </div>
  )
}
