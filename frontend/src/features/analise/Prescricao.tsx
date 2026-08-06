import type { Citacao, Passo, Prescricao as TipoPrescricao } from '../../api/types'
import { FonteCitacao } from './Citacoes'
import './Prescricao.css'

/** Procedimento recomendado, montado a partir dos manuais.
 *
 * Cada passo carrega a citacao que o sustenta -- nao ha uma nota de rodape
 * generica no fim. Uma citacao global nao prova que *aquele* passo veio do
 * manual.
 */
export function Prescricao({ prescricao }: { prescricao: TipoPrescricao }) {
  const porRotulo = new Map(prescricao.citacoes.map((c) => [rotulo(c), c]))
  const temOcr = prescricao.citacoes.some((c) => c.metodo === 'ocr')

  return (
    <div className="cartao procedimento">
      <div className="procedimento-topo">
        <p className="procedimento-diagnostico">{prescricao.diagnostico}</p>
        {prescricao.embasamento && (
          <span
            className="distintivo distintivo--ok"
            title="Fração dos passos cuja origem foi confirmada nos trechos citados"
          >
            {Math.round(prescricao.embasamento.score * 100)}% verificado
          </span>
        )}
      </div>

      <Secao titulo="Antes de intervir" passos={prescricao.inspecao} citacoes={porRotulo} />
      <Secao titulo="Corrigir" passos={prescricao.correcao} citacoes={porRotulo} />
      <Secao titulo="Confirmar que resolveu" passos={prescricao.validacao} citacoes={porRotulo} />

      {prescricao.avisos.length > 0 && (
        <div className="procedimento-avisos">
          <p className="rotulo">O que a documentação não cobre</p>
          <ul>
            {prescricao.avisos.map((aviso) => (
              <li key={aviso}>{aviso}</li>
            ))}
          </ul>
        </div>
      )}

      {prescricao.embasamento && prescricao.embasamento.removidas.length > 0 && (
        <div className="procedimento-removidos">
          <p className="rotulo">Removido por não ter fonte</p>
          <ul>
            {prescricao.embasamento.removidas.map((texto) => (
              <li key={texto}>{texto}</li>
            ))}
          </ul>
        </div>
      )}

      <footer className="procedimento-fontes">
        <span className="rotulo">Baseado em</span>
        {prescricao.citacoes.map((citacao) => (
          <FonteCitacao key={rotulo(citacao)} citacao={citacao} />
        ))}
        {temOcr && (
          <p className="t3 procedimento-nota">
            Trechos marcados como OCR vieram de páginas em imagem, transcritas
            automaticamente. Confira valores críticos no documento original.
          </p>
        )}
      </footer>
    </div>
  )
}

function Secao({
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
    <div className="secao">
      <h3 className="secao-titulo">{titulo}</h3>
      <ol className="passos">
        {passos.map((passo, indice) => (
          <li key={indice} className="passo-item">
            <span className="passo-marca">{indice + 1}</span>
            <div>
              <p>{passo.texto}</p>
              <p className="passo-fontes">
                {passo.citacoes.map((marca) => {
                  const citacao = citacoes.get(marca)
                  // Rotulo sem citacao correspondente nao deveria chegar aqui --
                  // a verificacao remove os inventados --, mas se chegar vai
                  // como texto, e nao some da tela.
                  return citacao ? (
                    <FonteCitacao key={marca} citacao={citacao} chaves />
                  ) : (
                    <span key={marca} className="fonte">
                      {marca}
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

/** Chave de busca, identica byte a byte ao rotulo que o backend emite.
 *
 * Nao usa o travessao de `rotuloCitacao`: o backend escreve `p. 4-5` com hifen
 * comum, e um travessao aqui faria toda citacao de mais de uma pagina falhar em
 * achar o objeto no mapa -- o passo perdia a fonte em silencio.
 */
function rotulo(citacao: Citacao): string {
  const paginas =
    citacao.pagina_inicial === citacao.pagina_final
      ? `p. ${citacao.pagina_inicial}`
      : `p. ${citacao.pagina_inicial}-${citacao.pagina_final}`
  return `[${citacao.documento}, ${paginas}]`
}
