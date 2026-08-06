import { Link } from 'react-router-dom'

import { useLinhaDoTempo, useVisaoGeral } from '../../api/queries'
import { Carregando, Erro } from '../../components/Estado'
import { corDaFamilia, dataCurta, numero, rotuloFamilia } from '../../lib/formato'
import { LinhaDoTempo } from './LinhaDoTempo'
import { Recorrencia } from './Recorrencia'
import { Separabilidade } from './Separabilidade'
import './Painel.css'

export function Painel() {
  const geral = useVisaoGeral()
  const serie = useLinhaDoTempo()

  if (geral.isLoading) return <Carregando altura="26rem" />
  if (geral.isError) return <Erro erro={geral.error} aoTentarNovamente={geral.refetch} />
  if (!geral.data) return null

  const dados = geral.data
  const descobertas = dados.familias_descobertas
  const cobertas = dados.familias_cobertas

  return (
    <>
      <header className="cabecalho">
        <h1>Como este sistema funciona</h1>
        <p className="t2">
          Sensores de vibração leem a máquina o tempo todo. Quando aparece um sinal
          estranho, o sistema procura no histórico leituras parecidas, descobre que
          falha era aquela e consulta o procedimento técnico para dizer o que fazer.
        </p>
      </header>

      {/* A tese: o sistema so responde o que consegue citar. */}
      <section className="cartao regra">
        <div className="regra-texto">
          <span className="distintivo distintivo--acento">A regra do sistema</span>
          <h2>Só recomenda o que consegue citar</h2>
          <p className="t2">
            Se a falha identificada não tem procedimento cadastrado, o sistema informa
            isso e pede o documento — em vez de inventar uma resposta. Hoje{' '}
            <b>{cobertas} de {dados.familias_problema}</b> tipos de falha têm
            procedimento.
          </p>

          <div className="regra-barra">
            {Array.from({ length: dados.familias_problema }, (_, i) => (
              <span
                key={i}
                className={`regra-marca ${i < cobertas ? 'regra-marca--ok' : ''}`}
              />
            ))}
          </div>

          {descobertas.length > 0 && (
            <p className="regra-lacuna">
              <span className="t3">Ainda sem procedimento: </span>
              {descobertas.map((familia) => (
                <span key={familia} className="distintivo distintivo--atencao">
                  {rotuloFamilia(familia)}
                </span>
              ))}
              <Link to="/documentos" className="regra-link">
                cadastrar →
              </Link>
            </p>
          )}
        </div>
      </section>

      {/* Os tres passos, em linguagem de operacao. */}
      <section className="etapas">
        <Etapa
          numero="1"
          titulo="Compara com o histórico"
          texto={`${numero(dados.total_eventos)} leituras registradas entre ${
            dados.periodo_inicio ? dataCurta(dados.periodo_inicio) : ''
          } e ${dados.periodo_fim ? dataCurta(dados.periodo_fim) : ''}.`}
        />
        <Etapa
          numero="2"
          titulo="Identifica a falha"
          texto={`${dados.familias_problema} tipos de falha distintos, aprendidos das anotações dos operadores.`}
        />
        <Etapa
          numero="3"
          titulo="Consulta o procedimento"
          texto={`${dados.documentos_indexados} documentos técnicos indexados, em ${numero(
            dados.trechos_indexados,
          )} trechos pesquisáveis.`}
        />
      </section>

      <section className="cartao">
        <div className="cartao-topo">
          <div>
            <h2>Quando as falhas aconteceram</h2>
            <p className="t3">Leituras por dia, separadas por tipo de falha</p>
          </div>
        </div>
        <div className="cartao-corpo">
          {serie.isLoading && <Carregando altura="16rem" />}
          {serie.isError && <Erro erro={serie.error} aoTentarNovamente={serie.refetch} />}
          {serie.data && <LinhaDoTempo pontos={serie.data} />}
        </div>
      </section>

      <Recorrencia />

      <section className="cartao">
        <div className="cartao-topo">
          <div>
            <h2>Tipos de falha</h2>
            <p className="t3">Clique para analisar uma leitura desse tipo</p>
          </div>
        </div>
        <div className="cartao-corpo cartao-corpo--tabela">
          <table>
            <thead>
              <tr>
                <th>Falha</th>
                <th>O que é</th>
                <th className="num">Leituras</th>
                <th>Procedimento</th>
              </tr>
            </thead>
            <tbody>
              {dados.ranking
                .filter((familia) => familia.e_problema)
                .map((familia) => (
                  <tr key={familia.familia}>
                    <td>
                      <Link
                        to={`/analise?familia=${familia.familia}`}
                        className="falha-nome"
                      >
                        <i style={{ background: corDaFamilia(familia.familia) }} />
                        {rotuloFamilia(familia.familia)}
                      </Link>
                    </td>
                    <td className="t2">{familia.descricao}</td>
                    <td className="num">{numero(familia.eventos)}</td>
                    <td>
                      {familia.coberta ? (
                        <span className="distintivo distintivo--ok">
                          {familia.documentos.join(', ')}
                        </span>
                      ) : (
                        <span className="distintivo distintivo--atencao">
                          não cadastrado
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </section>

      <Separabilidade />
    </>
  )
}

function Etapa({
  numero,
  titulo,
  texto,
}: {
  numero: string
  titulo: string
  texto: string
}) {
  return (
    <div className="cartao etapa">
      <span className="etapa-numero">{numero}</span>
      <h3>{titulo}</h3>
      <p className="t2">{texto}</p>
    </div>
  )
}
