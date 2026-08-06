/** Formatacao. Publico tecnico: unidade sempre explicita, numero sempre tabular. */

const NUMERO = new Intl.NumberFormat('pt-BR')
const DATA = new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit' })
const DATA_HORA = new Intl.DateTimeFormat('pt-BR', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

export const numero = (valor: number) => NUMERO.format(valor)

export const porcento = (valor: number, casas = 0) =>
  `${(valor * 100).toFixed(casas)}%`

export const dataCurta = (iso: string) => DATA.format(new Date(iso))
export const dataHora = (iso: string) => DATA_HORA.format(new Date(iso))

export const duracao = (ms: number) =>
  ms >= 1000 ? `${(ms / 1000).toFixed(1)} s` : `${Math.round(ms)} ms`

/** `rolamento_inner` -> `Rolamento inner`. Mantem o slug reconhecivel. */
export function rotuloFamilia(familia: string): string {
  const texto = familia.replaceAll('_', ' ')
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

export function corDaFamilia(familia: string): string {
  return `var(--f-${familia}, var(--texto-3))`
}
