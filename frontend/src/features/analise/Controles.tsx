import type { Desfecho } from '../../api/queries'
import type { FamiliaResumo } from '../../api/types'
import { porcento, rotuloFamilia } from '../../lib/formato'
import './Controles.css'

/** Controles da demonstracao.
 *
 * O limiar de concordancia fica exposto de proposito. Ele e uma escolha de
 * projeto, nao uma constante da natureza: baixar aumenta a fracao de eventos
 * diagnosticados e reduz o acerto. Com o controle a vista, quem avalia mexe e
 * ve o efeito, em vez de aceitar o numero na palavra de quem escreveu.
 *
 * A tabela ao lado traz a medicao real sobre 3.000 eventos do conjunto de teste.
 */

const MEDICAO: { limiar: number; cobertura: string; precisao: string }[] = [
  { limiar: 0.5, cobertura: '74%', precisao: '47%' },
  { limiar: 0.6, cobertura: '59%', precisao: '53%' },
  { limiar: 0.7, cobertura: '47%', precisao: '59%' },
  { limiar: 0.8, cobertura: '35%', precisao: '64%' },
  { limiar: 0.9, cobertura: '25%', precisao: '70%' },
]

const DESFECHOS: { valor: Desfecho; rotulo: string; nota: string }[] = [
  { valor: 'qualquer', rotulo: 'Qualquer caso', nota: 'sorteio livre no conjunto de teste' },
  { valor: 'prescricao', rotulo: 'Que gere procedimento', nota: 'falha reconhecida e documentada' },
  { valor: 'sem_documento', rotulo: 'Sem documentação', nota: 'falha reconhecida, sem procedimento' },
  { valor: 'sem_diagnostico', rotulo: 'Sem diagnóstico', nota: 'vizinhança dividida' },
]

export function Controles({
  familias,
  familia,
  aoMudarFamilia,
  desfecho,
  aoMudarDesfecho,
  limiar,
  aoMudarLimiar,
}: {
  familias: FamiliaResumo[]
  familia: string
  aoMudarFamilia: (valor: string) => void
  desfecho: Desfecho
  aoMudarDesfecho: (valor: Desfecho) => void
  limiar: number
  aoMudarLimiar: (valor: number) => void
}) {
  const linhaAtual = MEDICAO.reduce((mais, atual) =>
    Math.abs(atual.limiar - limiar) < Math.abs(mais.limiar - limiar) ? atual : mais,
  )

  return (
    <div className="controles">
      <div className="controle">
        <label htmlFor="ctl-desfecho" className="rotulo">
          Qual caso mostrar
        </label>
        <select
          id="ctl-desfecho"
          value={desfecho}
          onChange={(e) => aoMudarDesfecho(e.target.value as Desfecho)}
        >
          {DESFECHOS.map((opcao) => (
            <option key={opcao.valor} value={opcao.valor}>
              {opcao.rotulo}
            </option>
          ))}
        </select>
        <p className="controle-dica">
          {DESFECHOS.find((o) => o.valor === desfecho)?.nota}. A leitura continua real
          e nunca vista — muda só qual dos casos aparece.
        </p>
      </div>

      <div className="controle">
        <label htmlFor="ctl-familia" className="rotulo">
          Família
        </label>
        <select
          id="ctl-familia"
          value={familia}
          onChange={(e) => aoMudarFamilia(e.target.value)}
        >
          <option value="">Todas</option>
          {familias
            .filter((f) => f.e_problema)
            .map((f) => (
              <option key={f.familia} value={f.familia}>
                {rotuloFamilia(f.familia)}
                {f.coberta ? '' : ' — sem documento'}
              </option>
            ))}
        </select>
        <p className="controle-dica">
          Famílias marcadas não têm procedimento cadastrado e sempre caem em recusa.
        </p>
      </div>

      <div className="controle controle--limiar">
        <label htmlFor="ctl-limiar" className="rotulo">
          Concordância mínima para diagnosticar
        </label>
        <div className="limiar-linha">
          <input
            id="ctl-limiar"
            type="range"
            min="0.4"
            max="0.95"
            step="0.05"
            value={limiar}
            onChange={(e) => aoMudarLimiar(Number(e.target.value))}
          />
          <b className="dado limiar-valor">{porcento(limiar)}</b>
        </div>
        <p className="controle-dica">
          Medido em 3.000 leituras do conjunto de teste: neste patamar o sistema
          diagnostica <b>{linhaAtual.cobertura}</b> dos casos e acerta{' '}
          <b>{linhaAtual.precisao}</b> deles. Baixar o limiar responde mais e erra mais.
        </p>
      </div>
    </div>
  )
}
