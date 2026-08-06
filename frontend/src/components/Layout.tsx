import { NavLink, Outlet } from 'react-router-dom'

import { useSaude } from '../api/queries'
import './Layout.css'

const PAGINAS = [
  { para: '/', rotulo: 'Início', fim: true },
  { para: '/analise', rotulo: 'Analisar leitura' },
  { para: '/documentos', rotulo: 'Procedimentos' },
]

function EstadoDoSistema() {
  const { data, isLoading, isError } = useSaude()

  if (isLoading) return <span className="saude saude--carregando">verificando</span>
  if (isError || !data) {
    return (
      <span className="saude saude--fora" title="Sem resposta da API">
        sistema fora do ar
      </span>
    )
  }

  const problemas = data.componentes.filter((componente) => componente.estado !== 'ok')
  const titulo = problemas.length
    ? problemas.map((c) => `${c.nome}: ${c.detalhe ?? c.estado}`).join('\n')
    : 'Banco, dados, documentos e assistente respondendo'

  return (
    <span className={`saude saude--${data.estado}`} title={titulo}>
      {data.estado === 'ok' ? 'tudo operando' : `${problemas.length} aviso(s)`}
    </span>
  )
}

export function Layout() {
  return (
    <div className="aplicacao">
      <aside className="rail">
        <div className="marca">
          <span className="marca-icone" aria-hidden="true">
            MP
          </span>
          <div>
            <p className="marca-nome">Manutenção Prescritiva</p>
            <p className="marca-sub">Máquina rotativa MAQ-01</p>
          </div>
        </div>

        <nav className="menu" aria-label="Seções">
          {PAGINAS.map((pagina) => (
            <NavLink
              key={pagina.para}
              to={pagina.para}
              end={pagina.fim}
              className={({ isActive }) =>
                `menu-item ${isActive ? 'menu-item--ativo' : ''}`
              }
            >
              {pagina.rotulo}
            </NavLink>
          ))}
        </nav>

        <div className="rail-rodape">
          <EstadoDoSistema />
          <p className="rail-nota">SENAI SC · Processo seletivo 02198/2026</p>
        </div>
      </aside>

      <main className="conteudo">
        <Outlet />
      </main>
    </div>
  )
}
