import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { PontoLinhaDoTempo } from '../../api/types'
import { corDaFamilia, dataCurta, numero, rotuloFamilia } from '../../lib/formato'

/** Corte entre historico e conjunto de teste.
 *
 * Marcado no grafico de proposito: o rigor metodologico fica visivel em vez de
 * precisar ser explicado. Tudo a direita desta linha o modelo nunca viu. */
const INICIO_HOLDOUT = '2026-06-10'

interface Linha {
  dia: string
  [familia: string]: string | number
}

function agrupar(pontos: PontoLinhaDoTempo[]): {
  linhas: Linha[]
  familias: string[]
} {
  const porDia = new Map<string, Linha>()
  const familias = new Set<string>()

  for (const ponto of pontos) {
    familias.add(ponto.familia)
    const linha = porDia.get(ponto.dia) ?? { dia: ponto.dia }
    linha[ponto.familia] = ((linha[ponto.familia] as number) ?? 0) + ponto.total
    porDia.set(ponto.dia, linha)
  }

  return {
    linhas: [...porDia.values()].sort((a, b) => a.dia.localeCompare(b.dia)),
    familias: [...familias].sort(),
  }
}

export function LinhaDoTempo({ pontos }: { pontos: PontoLinhaDoTempo[] }) {
  const { linhas, familias } = agrupar(pontos)

  if (linhas.length === 0) {
    return <p className="fraco">Sem ocorrências no período.</p>
  }

  return (
    <>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={linhas} margin={{ top: 8, right: 8, bottom: 0, left: -8 }}>
          <CartesianGrid stroke="#23304d" vertical={false} />
          <XAxis
            dataKey="dia"
            tickFormatter={dataCurta}
            stroke="#6f7f9f"
            tick={{ fontSize: 11, fontFamily: 'var(--fonte-dado)' }}
            tickLine={false}
          />
          <YAxis
            stroke="#6f7f9f"
            tick={{ fontSize: 11, fontFamily: 'var(--fonte-dado)' }}
            tickLine={false}
            axisLine={false}
            label={{
              value: 'leituras',
              angle: -90,
              position: 'insideLeft',
              style: { fill: '#6f7f9f', fontSize: 11 },
            }}
          />
          {/* O Recharts escreve os estilos do tooltip inline, num contexto que
              nao herda as variaveis CSS da aplicacao. Por isso os valores aqui
              sao literais: usar `var(--…)` deixava o texto invisivel e o
              destaque da coluna preto. */}
          <Tooltip
            cursor={{ fill: 'rgba(77, 159, 255, 0.10)' }}
            contentStyle={{
              background: '#17223a',
              border: '1px solid #2f3f63',
              borderRadius: 10,
              boxShadow: '0 8px 24px -12px rgba(0,0,0,.6)',
              fontSize: 13,
              padding: '8px 12px',
            }}
            labelStyle={{ color: '#eaf0fa', fontWeight: 600, marginBottom: 6 }}
            itemStyle={{ color: '#a3b1cc', padding: '2px 0' }}
            labelFormatter={(dia) => (typeof dia === 'string' ? dataCurta(dia) : String(dia ?? ''))}
            formatter={(valor, nome) => [numero(Number(valor ?? 0)), rotuloFamilia(String(nome ?? ''))]}
          />
          <ReferenceLine
            x={INICIO_HOLDOUT}
            stroke="#a3b1cc"
            strokeDasharray="4 4"
            label={{
              value: 'conjunto de teste →',
              position: 'insideTopRight',
              fill: '#a3b1cc',
              fontSize: 11,
            }}
          />
          {familias.map((familia) => (
            <Bar
              key={familia}
              dataKey={familia}
              stackId="ocorrencias"
              fill={corDaFamilia(familia)}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>

      <p className="fraco grafico-nota">
        A linha tracejada marca 10/06/2026. Tudo à direita foi separado como conjunto
        de teste e nunca entra na busca por similaridade — evita comparar um evento
        com ele mesmo.
      </p>
    </>
  )
}
