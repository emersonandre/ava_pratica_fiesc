import { Link } from 'react-router-dom'

import { useLinhaDoTempo, useVisaoGeral } from '../../api/queries'
import { Carregando, Erro } from '../../components/Estado'
import { Etiqueta } from '../../components/Selo'
import { corDaFamilia, dataCurta, numero, rotuloFamilia } from '../../lib/formato'
import { LinhaDoTempo } from './LinhaDoTempo'
import './Painel.css'

export function Painel() {
  const geral = useVisaoGeral()
  const serie = useLinhaDoTempo()

  if (geral.isLoading) return <Carregando altura="24rem" />
  if (geral.isError) return <Erro erro={geral.error} aoTentarNovamente={geral.refetch} />
  if (!geral.data) return null

  const dados = geral.data
  const cobertura = dados.familias_cobertas / dados.familias_problema
  const descobertas = dados.familias_descobertas

  return (
    <>
      <header className="pagina-cabecalho">
        <h1>Painel</h1>
        <p>
          {numero(dados.total_eventos)} leituras de sensor entre{' '}
          {dados.periodo_inicio && dataCurta(dados.periodo_inicio)} e{' '}
          {dados.periodo_fim && dataCurta(dados.periodo_fim)}, classificadas em{' '}
          {dados.familias_problema} famílias de falha.
        </p>
      </header>

      {/* Tese da pagina: o que o sistema PODE prescrever. E o unico indicador
          que decide se ha resposta ou recusa, entao abre o painel. */}
      <section className="painel cobertura" aria-labelledby="titulo-cobertura">
        <div className="cobertura-numero">
          <p className="rotulo">Cobertura documental</p>
          <p className="cobertura-fracao">
            <b>{dados.familias_cobertas}</b>
            <span className="fraco">/{dados.familias_problema}</span>
          </p>
          <p className="cobertura-legenda">famílias com procedimento indexado</p>
        </div>

        <div className="cobertura-detalhe">
          <h2 id="titulo-cobertura">
            O sistema só prescreve o que está documentado
          </h2>
          <div
            className="cobertura-trilha"
            role="img"
            aria-label={`${dados.familias_cobertas} de ${dados.familias_problema} famílias cobertas`}
          >
            <span
              className="cobertura-preenchida"
              style={{ width: `${cobertura * 100}%` }}
            />
          </div>

          {descobertas.length > 0 ? (
            <p className="cobertura-texto">
              Sem procedimento cadastrado:{' '}
              {descobertas.map((familia, indice) => (
                <span key={familia}>
                  <Etiqueta tom="ausente">{rotuloFamilia(familia)}</Etiqueta>
                  {indice < descobertas.length - 1 ? ' ' : ''}
                </span>
              ))}
              . Eventos dessas famílias recebem a análise estatística, mas nenhuma
              recomendação de correção. <Link to="/documentos">Registrar documento</Link>.
            </p>
          ) : (
            <p className="cobertura-texto">
              Todas as famílias de falha têm procedimento indexado.
            </p>
          )}
        </div>
      </section>

      <section className="indicadores">
        <Indicador
          rotulo="Leituras"
          valor={numero(dados.total_eventos)}
          nota={`${numero(dados.eventos_holdout)} reservadas para teste`}
        />
        <Indicador
          rotulo="Classificadas como falha"
          valor={numero(dados.eventos_problema)}
          nota={`${Math.round((dados.eventos_problema / dados.total_eventos) * 100)}% do total`}
        />
        <Indicador
          rotulo="Documentos indexados"
          valor={String(dados.documentos_indexados)}
          nota={`${numero(dados.trechos_indexados)} trechos pesquisáveis`}
        />
        <Indicador
          rotulo="Famílias de falha"
          valor={String(dados.familias_problema)}
          nota={`${dados.familias - dados.familias_problema} estados operacionais`}
        />
      </section>

      <section className="painel">
        <div className="painel-cabecalho">
          <h2>Ocorrências ao longo do tempo</h2>
          <span className="fraco">por dia, empilhado por família</span>
        </div>
        <div className="painel-corpo">
          {serie.isLoading && <Carregando altura="18rem" />}
          {serie.isError && <Erro erro={serie.error} aoTentarNovamente={serie.refetch} />}
          {serie.data && <LinhaDoTempo pontos={serie.data} />}
        </div>
      </section>

      <section className="painel">
        <div className="painel-cabecalho">
          <h2>Famílias por volume de ocorrências</h2>
          <span className="fraco">clique para analisar um evento da família</span>
        </div>
        <div className="painel-corpo painel-corpo--tabela">
          <table>
            <thead>
              <tr>
                <th>Família</th>
                <th>Descrição</th>
                <th className="num">Leituras</th>
                <th>Documentação</th>
              </tr>
            </thead>
            <tbody>
              {dados.ranking.map((familia) => (
                <tr key={familia.familia}>
                  <td>
                    <Link
                      to={`/analise?familia=${familia.familia}`}
                      className="familia-nome"
                    >
                      <span
                        className="familia-marca"
                        style={{ background: corDaFamilia(familia.familia) }}
                      />
                      {rotuloFamilia(familia.familia)}
                    </Link>
                  </td>
                  <td className="medio">{familia.descricao}</td>
                  <td className="num">{numero(familia.eventos)}</td>
                  <td>
                    {!familia.e_problema ? (
                      <Etiqueta>não é falha</Etiqueta>
                    ) : familia.coberta ? (
                      <Etiqueta tom="ok">{familia.documentos.join(', ')}</Etiqueta>
                    ) : (
                      <Etiqueta tom="ausente">sem documento</Etiqueta>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}

function Indicador({
  rotulo,
  valor,
  nota,
}: {
  rotulo: string
  valor: string
  nota: string
}) {
  return (
    <div className="painel indicador">
      <p className="rotulo">{rotulo}</p>
      <p className="indicador-valor dado">{valor}</p>
      <p className="indicador-nota">{nota}</p>
    </div>
  )
}
