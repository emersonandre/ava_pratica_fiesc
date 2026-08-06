import type { MotivoCobertura } from '../api/types'
import './Selo.css'

/** Selo de estado da cobertura documental.
 *
 * Vocabulario emprestado das etiquetas de inspecao e calibracao afixadas em
 * equipamento: quem trabalha em manutencao le esse formato sem instrucao.
 *
 * A recusa NAO usa o tratamento de erro da aplicacao. Recusar por falta de
 * documentacao e o comportamento correto do sistema, nao uma falha -- se
 * parecesse erro, seria lido como defeito.
 */

const ESTADOS: Record<
  MotivoCobertura,
  { titulo: string; tom: 'ok' | 'ausente' | 'neutro' | 'indefinido' }
> = {
  coberto: { titulo: 'Documentado', tom: 'ok' },
  sem_documento: { titulo: 'Sem documento', tom: 'ausente' },
  estado_operacional: { titulo: 'Estado operacional', tom: 'neutro' },
  sem_diagnostico: { titulo: 'Sem diagnóstico', tom: 'indefinido' },
}

export function Selo({ motivo }: { motivo: MotivoCobertura }) {
  const estado = ESTADOS[motivo]
  return (
    <span className={`selo selo--${estado.tom}`}>
      <span className="selo-marca" aria-hidden="true" />
      {estado.titulo}
    </span>
  )
}

export function Etiqueta({
  children,
  tom = 'neutro',
}: {
  children: React.ReactNode
  tom?: 'ok' | 'ausente' | 'neutro' | 'atencao'
}) {
  return <span className={`etiqueta etiqueta--${tom}`}>{children}</span>
}
