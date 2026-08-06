import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import type { Desfecho, PedidoAmostra } from '../../api/queries'
import { useAmostra, useAnalisar, useFamilias } from '../../api/queries'
import type { AmostraHoldout, EventoSensor, RespostaAnalise } from '../../api/types'
import { COLUNAS_SENSOR } from '../../api/types'
import { Erro } from '../../components/Estado'
import { Girando, Progresso } from '../../components/Progresso'
import { corDaFamilia, porcento, rotuloFamilia } from '../../lib/formato'
import { Chat } from './Chat'
import { ColarJson } from './ColarJson'
import { Detalhes } from './Detalhes'
import { Prescricao } from './Prescricao'
import './Analise.css'

const ETAPAS_PROCEDIMENTO = [
  'Buscando trechos nos manuais',
  'Redigindo o procedimento',
  'Conferindo cada citação',
]

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
  const [colando, setColando] = useState(false)

  const familias = useFamilias()
  const amostra = useAmostra()

  // Duas chamadas separadas de proposito: identificar a falha responde em
  // milissegundos, redigir o procedimento leva ~45 s. Juntar as duas obrigaria a
  // esperar a geracao so para ver o diagnostico.
  const diagnose = useAnalisar()
  const procedimento = useAnalisar()

  useEffect(() => {
    setFamilia(familiaAlvo ?? '')
    buscar({ familia: familiaAlvo, desfecho: 'prescricao', confiancaMinima: 0.7 })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [familiaAlvo])

  function buscar(pedido: PedidoAmostra) {
    diagnose.reset()
    procedimento.reset()
    amostra.mutate(pedido, {
      onSuccess: setLeitura,
      onError: () => {
        // A combinacao pedida pode nao existir -- por exemplo, uma falha sem
        // procedimento que ainda assim seja diagnosticada com alta certeza.
        // Nesse caso vale mais mostrar uma leitura daquela condicao do que
        // devolver um erro: o filtro de desfecho e conveniencia de demonstracao,
        // a condicao e o que o usuario pediu.
        if (pedido.desfecho && pedido.desfecho !== 'qualquer') {
          amostra.mutate({ ...pedido, desfecho: 'qualquer' }, { onSuccess: setLeitura })
        }
      },
    })
  }

  function trocarCondicao(novaFamilia: string) {
    setFamilia(novaFamilia)
    buscar({
      familia: novaFamilia || undefined,
      desfecho,
      confiancaMinima: limiar,
    })
  }

  function identificar() {
    if (!leitura) return
    procedimento.reset()
    diagnose.mutate({
      ...paraEvento(leitura),
      // O rotulo bruto vai junto para o backend normalizar e devolver o gabarito.
      // A taxonomia vive la; o frontend nao sabe que `cocked_rotor_2` e `cocked_rotor`.
      fault: leitura.raw_fault || undefined,
      confianca_minima: limiar,
      gerar_prescricao: false,
    })
  }

  function pedirProcedimento() {
    if (!leitura) return
    procedimento.mutate({
      ...paraEvento(leitura),
      confianca_minima: limiar,
      gerar_prescricao: true,
    })
  }

  const diagnostico = diagnose.data
  const coberta = diagnostico?.cobertura.coberta ?? false

  return (
    <>
      <header className="cabecalho">
        <h1>Analisar uma leitura</h1>
        <p className="t2">
          O sistema compara a leitura com o histórico da máquina, identifica a falha e
          consulta os procedimentos cadastrados para dizer o que fazer.
        </p>
      </header>

      {/* ----- 1. escolher ----- */}
      <Passo numero={1} titulo="Escolher a leitura" feito={!!leitura}
        nota="Vem do conjunto de teste: dados reais de 10 a 16 de junho que o sistema nunca usou para aprender.">
        {amostra.isError && <Erro erro={amostra.error} aoTentarNovamente={() => buscar({ familia: familia || undefined, desfecho, confiancaMinima: limiar })} />}
        {amostra.isPending && !leitura && <Girando texto="Procurando uma leitura…" />}

        {colando && (
          <ColarJson
            aoCancelar={() => setColando(false)}
            aoCarregar={(nova) => {
              diagnose.reset()
              procedimento.reset()
              setLeitura(nova)
              setColando(false)
            }}
          />
        )}

        {leitura && (
          <div className="cartao leitura">
            <div className="leitura-topo">
              <div>
                <span className="rotulo">Leitura</span>
                <p className="leitura-id dado">#{leitura.id}</p>
              </div>

              <div className="leitura-verdade">
                <label className="rotulo" htmlFor="seletor-condicao">
                  Condição anotada pelo operador
                </label>
                <div className="seletor-condicao">
                  {/* A cor identifica a familia. Fica num ponto ao lado, nao no
                      texto do select: cor aplicada no <select> vaza para todas
                      as <option> e pinta a lista inteira. */}
                  <span
                    className="seletor-cor"
                    style={{ background: corDaFamilia(familia || leitura.fault_family) }}
                    aria-hidden="true"
                  />
                  <select
                    id="seletor-condicao"
                    value={familia || leitura.fault_family}
                    onChange={(e) => trocarCondicao(e.target.value)}
                    disabled={amostra.isPending}
                  >
                    <option value="">Qualquer condição</option>
                    {(familias.data ?? [])
                      // Familias sem leitura no conjunto de teste nao tem o que
                      // demonstrar: existem no historico, mas nao no periodo
                      // reservado para avaliacao. Oferece-las levaria a um erro.
                      .filter((f) => f.eventos_holdout > 0)
                      .map((f) => (
                        <option key={f.familia} value={f.familia}>
                          {rotuloFamilia(f.familia)}
                          {f.e_problema && !f.coberta ? ' — sem procedimento' : ''}
                          {!f.e_problema ? ' — não é falha' : ''}
                        </option>
                      ))}
                  </select>
                  <button
                    type="button"
                    className="botao seletor-sortear"
                    onClick={() =>
                      buscar({ familia: familia || undefined, desfecho, confiancaMinima: limiar })
                    }
                    disabled={amostra.isPending}
                    title="Sortear outra leitura desta condição"
                    aria-label="Sortear outra leitura"
                  >
                    {amostra.isPending ? '…' : '↻'}
                  </button>
                </div>
              </div>
            </div>

            <div className="leitura-rodape">
              <dl className="medidas">
                <Medida rotulo="Rotação" valor={leitura.rpm} unidade="RPM" />
                <Medida rotulo="Temperatura" valor={leitura.temperature_c} unidade="°C" />
                <Medida rotulo="Vibração Z" valor={leitura.z_rms_velocity_mm_s} unidade="mm/s" />
                <Medida rotulo="Vibração X" valor={leitura.x_rms_velocity_mm_s} unidade="mm/s" />
              </dl>

              <div className="leitura-acoes">
                <button type="button" className="botao-texto"
                  onClick={() => setColando(!colando)} aria-expanded={colando}>
                  {colando ? 'Fechar' : 'Colar JSON'}
                </button>
                <button type="button" className="botao-texto"
                  onClick={() => setAvancado(!avancado)} aria-expanded={avancado}>
                  {avancado ? 'Ocultar opções' : 'Opções de demonstração'}
                </button>
              </div>
            </div>

            {avancado && (
              <div className="avancado">
                <label className="campo">
                  <span className="rotulo">Tipo de caso</span>
                  <select value={desfecho} onChange={(e) => setDesfecho(e.target.value as Desfecho)}>
                    <option value="prescricao">Falha com procedimento cadastrado</option>
                    <option value="sem_documento">Falha sem procedimento</option>
                    <option value="sem_diagnostico">Sinal ambíguo</option>
                    <option value="qualquer">Sorteio livre</option>
                  </select>
                </label>
                <label className="campo">
                  <span className="rotulo">Certeza mínima para diagnosticar: {porcento(limiar)}</span>
                  <input type="range" min="0.4" max="0.95" step="0.05" value={limiar}
                    onChange={(e) => setLimiar(Number(e.target.value))} />
                  <span className="t3 campo-dica">
                    Exigir mais certeza faz o sistema responder menos vezes e acertar mais.
                  </span>
                </label>
              </div>
            )}
          </div>
        )}
      </Passo>

      {/* ----- 2. identificar ----- */}
      <Passo numero={2} titulo="Identificar a falha" feito={!!diagnostico}
        nota="Busca as leituras mais parecidas no histórico e vê em que elas concordam.">
        {!diagnostico && !diagnose.isPending && (
          <button type="button" className="botao botao-primario botao-grande"
            onClick={identificar} disabled={!leitura}>
            Identificar falha
          </button>
        )}

        {diagnose.isPending && (
          <div className="cartao carregando-simples">
            <Girando texto="Comparando com 157 mil leituras do histórico…" />
          </div>
        )}

        {diagnose.isError && <Erro erro={diagnose.error} aoTentarNovamente={identificar} />}

        {diagnostico && leitura && (
          <Diagnostico resultado={diagnostico} />
        )}
      </Passo>

      {/* ----- 3. procedimento ----- */}
      {diagnostico && (
        <Passo numero={3} titulo="Procedimento recomendado" feito={!!procedimento.data?.prescricao}
          nota="Monta o passo a passo a partir dos manuais da falha identificada, citando a página de cada item.">
          {!coberta ? (
            <SemProcedimento resultado={diagnostico} />
          ) : (
            <>
              {!procedimento.data && !procedimento.isPending && (
                <button type="button" className="botao botao-primario botao-grande"
                  onClick={pedirProcedimento}>
                  Gerar procedimento
                </button>
              )}

              {procedimento.isPending && (
                <Progresso etapas={ETAPAS_PROCEDIMENTO} estimativaSegundos={45} />
              )}

              {procedimento.isError && (
                <Erro erro={procedimento.error} aoTentarNovamente={pedirProcedimento} />
              )}

              {procedimento.data?.prescricao && (
                <Prescricao prescricao={procedimento.data.prescricao} />
              )}
            </>
          )}
        </Passo>
      )}

      {/* ----- 4. chat ----- */}
      {diagnostico && coberta && leitura && (
        <Passo numero={4} titulo="Tirar dúvidas" ultimo
          nota="Pergunte o que quiser sobre esta falha. O assistente responde consultando os mesmos manuais e diz quando a documentação não cobre a pergunta.">
          <Chat evento={leitura} limiar={limiar} />
        </Passo>
      )}

      {diagnostico && <Detalhes resultado={procedimento.data ?? diagnostico} />}
    </>
  )
}

function Passo({
  numero,
  titulo,
  nota,
  feito,
  ultimo,
  children,
}: {
  numero: number
  titulo: string
  nota: string
  feito?: boolean
  ultimo?: boolean
  children: React.ReactNode
}) {
  return (
    <section className={`passo ${ultimo ? 'passo--ultimo' : ''}`}>
      <div className="passo-marca">
        <span className={`passo-numero ${feito ? 'passo-numero--feito' : ''}`}>
          {feito ? '✓' : numero}
        </span>
        {!ultimo && <span className="passo-linha" />}
      </div>
      <div className="passo-conteudo">
        <h2>{titulo}</h2>
        <p className="t2 passo-nota">{nota}</p>
        {children}
      </div>
    </section>
  )
}

function Diagnostico({ resultado }: { resultado: RespostaAnalise }) {
  const { diagnostico, cobertura } = resultado
  // O veredito vem do backend, que normalizou o rotulo bruto pela taxonomia.
  const acertou = diagnostico.acertou

  return (
    <div className="cartao diagnostico">
      <div className="diagnostico-linha">
        <h3
          className={`diagnostico-nome ${diagnostico.familia ? '' : 'diagnostico-nome--vazio'}`}
          style={
            diagnostico.familia ? { color: corDaFamilia(diagnostico.familia) } : undefined
          }
        >
          {diagnostico.familia ? rotuloFamilia(diagnostico.familia) : 'Sem conclusão'}
        </h3>
        <span
          className={`distintivo distintivo--${diagnostico.familia && acertou ? 'ok' : 'atencao'}`}
        >
          {!diagnostico.familia
            ? 'sem conclusão'
            : acertou
              ? 'confere com o rótulo real'
              : 'diverge do rótulo real'}
        </span>
      </div>

      {/* Texto corrido, nao flex: o leitor precisa da frase, nao de tres dados
          soltos. O numero em destaque carrega a informacao, o resto explica. */}
      <p className="diagnostico-meta">
        {diagnostico.familia ? (
          <>
            <b>{porcento(diagnostico.confianca)}</b> das{' '}
            <b>{resultado.vizinhos.length}</b> leituras mais parecidas do histórico
            apresentavam esta mesma falha.
          </>
        ) : (
          <>
            A hipótese mais forte é{' '}
            <b style={{ color: corDaFamilia(diagnostico.hipotese ?? '') }}>
              {diagnostico.hipotese ? rotuloFamilia(diagnostico.hipotese) : '—'}
            </b>
            , com <b>{porcento(diagnostico.confianca)}</b> das{' '}
            <b>{resultado.vizinhos.length}</b> leituras mais parecidas — abaixo do
            mínimo exigido. O sistema não conclui nem recomenda correção; confirme em
            campo antes de intervir.
          </>
        )}
      </p>

      {cobertura.coberta && (
        <p className="diagnostico-fonte">
          Procedimento cadastrado:{' '}
          {cobertura.documentos.map((documento) => (
            <span key={documento.arquivo} className="distintivo distintivo--acento">
              {documento.arquivo}
            </span>
          ))}
        </p>
      )}

      <div className="votacao">
        <div className="votacao-barra">
          {diagnostico.votos.map((voto) => (
            <span key={voto.fault_family}
              style={{ width: `${voto.peso * 100}%`, background: corDaFamilia(voto.fault_family) }}
              title={`${rotuloFamilia(voto.fault_family)}: ${porcento(voto.peso)}`} />
          ))}
        </div>
        <div className="votacao-legenda">
          {diagnostico.votos.slice(0, 3).map((voto) => (
            <span key={voto.fault_family} className="votacao-item">
              <i style={{ background: corDaFamilia(voto.fault_family) }} />
              {rotuloFamilia(voto.fault_family)} <b>{porcento(voto.peso)}</b>
            </span>
          ))}
          {diagnostico.votos.length > 3 && (
            <span className="votacao-item t3">
              +{diagnostico.votos.length - 3} outras
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

function SemProcedimento({ resultado }: { resultado: RespostaAnalise }) {
  const { recusa, cobertura } = resultado
  const semDocumento = cobertura.motivo === 'sem_documento'

  return (
    <div className="cartao sem-procedimento">
      <span className="distintivo distintivo--atencao">Nenhuma recomendação</span>
      <p className="sem-procedimento-texto">
        {recusa?.mensagem ?? 'Não há procedimento cadastrado para esta falha.'}
      </p>
      {semDocumento && (
        <a href="/documentos" className="botao botao-primario">
          Cadastrar procedimento
        </a>
      )}
      <p className="t3 sem-procedimento-nota">
        O assistente não foi consultado. A decisão de não responder é tomada antes, por
        regra — não depende do modelo se comportar bem.
      </p>
    </div>
  )
}

function Medida({ rotulo, valor, unidade }: { rotulo: string; valor: number; unidade: string }) {
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
