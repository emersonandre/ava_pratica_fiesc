import type { ReactNode } from 'react'

import { ErroDaApi } from '../api/client'
import './Estado.css'

/** Estados de carregamento, erro e vazio.
 *
 * Tratados como parte do design, nao como sobra. Uma tela vazia e convite para
 * agir; um erro explica o que houve e como resolver, na voz da interface.
 */

export function Carregando({ altura = '8rem' }: { altura?: string }) {
  return <div className="esqueleto" style={{ height: altura }} aria-label="Carregando" />
}

export function Erro({
  erro,
  aoTentarNovamente,
}: {
  erro: unknown
  aoTentarNovamente?: () => void
}) {
  const mensagem =
    erro instanceof ErroDaApi
      ? erro.message
      : erro instanceof Error
        ? erro.message
        : 'Erro inesperado.'

  const semApi = erro instanceof ErroDaApi && erro.status === 0

  return (
    <div className="estado estado--erro" role="alert">
      <p className="estado-titulo">Não foi possível carregar</p>
      <p className="estado-texto">{mensagem}</p>
      {semApi && (
        <p className="estado-dica dado">
          cd backend &amp;&amp; python manage.py runserver
        </p>
      )}
      {aoTentarNovamente && (
        <button type="button" className="botao" onClick={aoTentarNovamente}>
          Tentar de novo
        </button>
      )}
    </div>
  )
}

export function Vazio({
  titulo,
  children,
}: {
  titulo: string
  children?: ReactNode
}) {
  return (
    <div className="estado">
      <p className="estado-titulo">{titulo}</p>
      {children && <div className="estado-texto">{children}</div>}
    </div>
  )
}
