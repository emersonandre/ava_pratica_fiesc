import { Link } from 'react-router-dom'

import type { Citacao, Passo, RespostaAnalise } from '../../api/types'
import { Etiqueta } from '../../components/Selo'
import { porcento } from '../../lib/formato'
import './Prescricao.css'

/** Procedimento prescrito, ou a recusa.
 *
 * A recusa nao usa tratamento de erro. Recusar por falta de documentacao e o
 * comportamento correto do sistema -- desenhar como erro faria o avaliador ler
 * como defeito.
 */
export function Prescricao({ resposta }: { resposta: RespostaAnalise }) {
  if (resposta.recusa) {
    const { recusa } = resposta
    return (
      <section className="painel recusa">
        <div className="painel-corpo">
          <p className="rotulo">Nenhuma recomendação emitida</p>
          <p className="recusa-mensagem">{recusa.mensagem}</p>

          {recusa.sugestao && (
            <p className="recusa-acao">
              <Link to="/documentos" className="botao botao-primario">
                Registrar documento
              </Link>
              <span className="fraco">
                Depois do registro, a mesma leitura passa a receber procedimento citado.
              </span>
            </p>
          )}

          <p className="recusa-nota">
            O modelo de linguagem <b>não foi chamado</b>. A decisão de não responder é
            tomada antes, por regra, e não depende do modelo se comportar bem.
          </p>
        </div>
      </section>
    )
  }

  const { prescricao } = resposta
  if (!prescricao) return null

  const citacoes = new Map(prescricao.citacoes.map((c) => [rotuloDaCitacao(c), c]))
  const temOcr = prescricao.citacoes.some((c) => c.metodo === 'ocr')

  return (
    <section className="painel prescricao">
      <div className="painel-cabecalho">
        <h2>Procedimento recomendado</h2>
        {prescricao.embasamento && (
          <span className="embasamento" title="Passos com respaldo verificado na documentação">
            <b className="dado">{porcento(prescricao.embasamento.score)}</b> com respaldo
            verificado
            <span className="fraco">
              {' '}
              ({prescricao.embasamento.embasadas}/{prescricao.embasamento.afirmacoes})
            </span>
          </span>
        )}
      </div>

      <div className="painel-corpo">
        <p className="prescricao-diagnostico">{prescricao.diagnostico}</p>

        <Bloco titulo="Antes de intervir" passos={prescricao.inspecao} citacoes={citacoes} />
        <Bloco titulo="Correção" passos={prescricao.correcao} citacoes={citacoes} />
        <Bloco titulo="Validação" passos={prescricao.validacao} citacoes={citacoes} />

        {prescricao.embasamento && prescricao.embasamento.removidas.length > 0 && (
          <div className="removidos">
            <p className="rotulo">Removido por falta de respaldo</p>
            <ul>
              {prescricao.embasamento.removidas.map((texto) => (
                <li key={texto}>{texto}</li>
              ))}
            </ul>
            <p className="fraco">
              Passos sem origem verificável na documentação são retirados da resposta,
              não sinalizados. Instrução de manutenção sem fonte é risco físico.
            </p>
          </div>
        )}

        {prescricao.avisos.length > 0 && (
          <div className="avisos">
            <p className="rotulo">O que a documentação não cobre</p>
            <ul>
              {prescricao.avisos.map((aviso) => (
                <li key={aviso}>{aviso}</li>
              ))}
            </ul>
          </div>
        )}

        <footer className="fontes">
          <span className="rotulo">Fontes</span>
          {prescricao.citacoes.map((citacao) => (
            <Etiqueta key={rotuloDaCitacao(citacao)} tom={citacao.metodo === 'ocr' ? 'atencao' : 'ok'}>
              {rotuloDaCitacao(citacao)}
              {citacao.metodo === 'ocr' ? ' · OCR' : ''}
            </Etiqueta>
          ))}
          {temOcr && (
            <span className="fraco fontes-nota">
              Trechos marcados como OCR vieram de páginas em imagem, transcritas
              automaticamente. Confira valores críticos no documento original.
            </span>
          )}
        </footer>
      </div>
    </section>
  )
}

function Bloco({
  titulo,
  passos,
  citacoes,
}: {
  titulo: string
  passos: Passo[]
  citacoes: Map<string, Citacao>
}) {
  if (passos.length === 0) return null

  return (
    <div className="bloco">
      <h3 className="bloco-titulo">{titulo}</h3>
      <ol className="passos">
        {passos.map((passo, indice) => (
          <li key={`${titulo}-${indice}`} className="passo">
            <span className="passo-ordem dado">{String(indice + 1).padStart(2, '0')}</span>
            <div className="passo-conteudo">
              <p>{passo.texto}</p>
              <p className="passo-citacoes">
                {passo.citacoes.map((rotulo) => {
                  const citacao = citacoes.get(rotulo)
                  return (
                    <span
                      key={rotulo}
                      className="citacao"
                      title={citacao?.secao ?? undefined}
                    >
                      {rotulo}
                    </span>
                  )
                })}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  )
}

function rotuloDaCitacao(citacao: Citacao): string {
  const paginas =
    citacao.pagina_inicial === citacao.pagina_final
      ? `p. ${citacao.pagina_inicial}`
      : `p. ${citacao.pagina_inicial}-${citacao.pagina_final}`
  return `[${citacao.documento}, ${paginas}]`
}
