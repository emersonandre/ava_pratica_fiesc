import { NavLink, Outlet } from 'react-router-dom'

import { useSaude } from '../api/queries'
import type { ComponenteSaude } from '../api/types'
import './Layout.css'

const PAGINAS = [
  { para: '/', rotulo: 'Painel', fim: true },
  { para: '/analise', rotulo: 'Análise' },
  { para: '/documentos', rotulo: 'Documentos' },
]

function EstadoDoSistema() {
  const { data, isLoading, isError } = useSaude()

  if (isLoading) return <span className="saude saude--carregando">verificando</span>
  if (isError || !data) {
    return (
      <span className="saude saude--fora" title="Sem resposta da API">
        API fora do ar
      </span>
    )
  }

  const problemas = data.componentes.filter((c: ComponenteSaude) => c.estado !== 'ok')
  const titulo = problemas.length
    ? problemas.map((c) => `${c.nome}: ${c.detalhe ?? c.estado}`).join('\n')
    : 'Banco, dados, documentos, modelo e credenciais respondendo'

  return (
    <span className={`saude saude--${data.estado}`} title={titulo}>
      {data.estado === 'ok'
        ? 'Sistema operante'
        : `${problemas.length} ${problemas.length === 1 ? 'aviso' : 'avisos'}`}
    </span>
  )
}

export function Layout() {
  return (
    <div className="aplicacao">
      <aside className="rail">
        {/* Placa de identificacao, no formato das que ficam presas ao
            equipamento: identifica a maquina e o ativo monitorado. */}
        <div className="placa">
          <p className="placa-linha">
            <span className="rotulo">Ativo</span>
            <span className="dado">MÁQ-ROT-01</span>
          </p>
          <h1 className="placa-titulo">
            Manutenção
            <br />
            Prescritiva
          </h1>
          <p className="placa-sub">Máquina rotativa · sensores de vibração</p>
        </div>

        <nav className="menu" aria-label="Seções">
          {PAGINAS.map((pagina) => (
            <NavLink
              key={pagina.para}
              to={pagina.para}
              end={pagina.fim}
              className={({ isActive }) => `menu-item ${isActive ? 'menu-item--ativo' : ''}`}
            >
              {pagina.rotulo}
            </NavLink>
          ))}
        </nav>

        <div className="rail-rodape">
          <EstadoDoSistema />
          <p className="rail-nota">
            SENAI SC · Processo seletivo 02198/2026
          </p>
        </div>
      </aside>

      <main className="conteudo">
        <Outlet />
      </main>
    </div>
  )
}
