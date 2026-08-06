import { useState } from 'react'

import type { AmostraHoldout, ColunaSensor } from '../../api/types'
import { COLUNAS_SENSOR } from '../../api/types'
import './ColarJson.css'

/** Entrada manual de uma leitura em JSON.
 *
 * A Figura 01 do enunciado mostra o JSON de sensor como entrada do sistema. Este
 * campo aceita o payload do §2 exatamente como está no documento, incluindo os
 * campos que o vetor não usa (`id`, `created_at`, `fault` e as colunas em
 * unidade imperial) -- eles são ignorados, não rejeitados.
 *
 * A validação acontece aqui, antes de chamar a API: um campo faltando é apontado
 * pelo nome, e não vira um 422 genérico.
 */

// Exemplo literal da seção 2 do enunciado.
const EXEMPLO_DO_ENUNCIADO = `{"id":114387,"created_at":"2026-06-01 21:32:53.911176+00:00","z_rms_velocity_in_s":0.0597,"z_rms_velocity_mm_s":1.517,"temperature_f":76.44,"temperature_c":24.69,"x_rms_velocity_in_s":0.0787,"x_rms_velocity_mm_s":2.0,"z_peak_acceleration_g":0.484,"x_peak_acceleration_g":0.631,"z_peak_vel_comp_freq_hz":61.0,"x_peak_vel_comp_freq_hz":61.0,"z_rms_acceleration_g":0.09,"x_rms_acceleration_g":0.114,"z_kurtosis":2.392,"x_kurtosis":2.77,"z_crest_factor":3.747,"x_crest_factor":4.269,"z_peak_velocity_in_s":0.0844,"z_peak_velocity_mm_s":2.146,"x_peak_velocity_in_s":0.1113,"x_peak_velocity_mm_s":2.829,"z_high_freq_rms_accel_g":0.129,"x_high_freq_rms_accel_g":0.147,"fault":"cocked_rotor_2","rpm":1000.0}`

interface Analise {
  valida: boolean
  erro?: string
  leitura?: AmostraHoldout
}

/** Remove os artefatos de copiar e colar de PDF, Word e Swagger.
 *
 * O JSON do enunciado vem de um documento, e o texto chega quebrado em varias
 * linhas. `JSON.parse` rejeita caractere de controle cru dentro de string --
 * "Bad control character in string literal" --, e a quebra dentro do
 * `created_at` derruba o payload inteiro. Word tambem troca aspas retas por
 * tipograficas e espaco comum por espaco fixo.
 *
 * Tudo aqui e ilegal em JSON valido, entao a limpeza nao altera nenhum
 * documento que ja estivesse correto.
 */
function limpar(texto: string): string {
  return texto
    .replace(/[\u201c\u201d\u201e\u201f]/g, '"')
    .replace(/[\u2018\u2019\u201a\u201b]/g, "'")
    .replace(/[\u00a0\u2000-\u200a\u202f\u205f\u3000]/g, ' ')
    .replace(/[\u200b-\u200d\ufeff]/g, '')
    .replace(/[\u0000-\u001f]/g, ' ')
    .trim()
}

function validar(texto: string): Analise {
  if (!texto.trim()) return { valida: false, erro: 'Cole um JSON de leitura.' }

  let bruto: unknown
  try {
    bruto = JSON.parse(limpar(texto))
  } catch (erro) {
    return {
      valida: false,
      erro: `JSON inválido: ${(erro as Error).message}. Confira se o texto foi copiado inteiro, do primeiro { ao último }.`,
    }
  }

  if (typeof bruto !== 'object' || bruto === null || Array.isArray(bruto)) {
    return { valida: false, erro: 'O JSON precisa ser um objeto com os campos da leitura.' }
  }

  // A quebra de linha do documento cai em qualquer ponto -- inclusive no meio do
  // nome de um campo, que entao chega como `z_peak_vel_comp_freq_hz ` e nao
  // corresponde a coluna nenhuma. Aparar chave e valor resolve, e nao muda nada
  // num JSON que ja viesse limpo.
  const dados: Record<string, unknown> = {}
  for (const [chave, valor] of Object.entries(bruto as Record<string, unknown>)) {
    dados[chave.trim()] = typeof valor === 'string' ? valor.trim() : valor
  }
  const faltando: string[] = []
  const naoNumericos: string[] = []
  const leitura = {} as Record<string, unknown>

  for (const coluna of COLUNAS_SENSOR) {
    const valor = dados[coluna]
    if (valor === undefined || valor === null) {
      faltando.push(coluna)
      continue
    }
    const numero = typeof valor === 'string' ? Number(valor) : valor
    if (typeof numero !== 'number' || Number.isNaN(numero)) {
      naoNumericos.push(coluna)
      continue
    }
    leitura[coluna] = numero
  }

  if (faltando.length) {
    return {
      valida: false,
      erro: `Faltam ${faltando.length} campo(s): ${faltando.join(', ')}`,
    }
  }
  if (naoNumericos.length) {
    return {
      valida: false,
      erro: `Campo(s) não numérico(s): ${naoNumericos.join(', ')}`,
    }
  }

  // `fault` é a condição anotada pelo operador. Se vier, serve de gabarito para
  // comparar com o diagnóstico -- é o que o enunciado chama de rótulo real.
  const rotulo = typeof dados.fault === 'string' ? dados.fault : ''

  return {
    valida: true,
    leitura: {
      ...(leitura as Record<ColunaSensor, number>),
      id: typeof dados.id === 'number' ? dados.id : 0,
      created_at: typeof dados.created_at === 'string' ? dados.created_at : '',
      raw_fault: rotulo,
      fault_family: rotulo,
      split: 'colado',
    } as AmostraHoldout,
  }
}

export function ColarJson({
  aoCarregar,
  aoCancelar,
}: {
  aoCarregar: (leitura: AmostraHoldout) => void
  aoCancelar: () => void
}) {
  const [texto, setTexto] = useState('')
  const [erro, setErro] = useState<string | null>(null)

  function usar() {
    const resultado = validar(texto)
    if (!resultado.valida || !resultado.leitura) {
      setErro(resultado.erro ?? 'JSON inválido.')
      return
    }
    setErro(null)
    aoCarregar(resultado.leitura)
  }

  return (
    <div className="cartao colar">
      <div className="colar-topo">
        <div>
          <h3>Colar leitura em JSON</h3>
          <p className="t3">
            Aceita o formato de saída do coletor. Campos que o modelo não usa —{' '}
            <code>id</code>, <code>created_at</code>, <code>fault</code> e as colunas
            em polegada — são ignorados.
          </p>
        </div>
        <button type="button" className="botao-texto" onClick={aoCancelar}>
          Fechar
        </button>
      </div>

      <textarea
        value={texto}
        onChange={(e) => {
          setTexto(e.target.value)
          setErro(null)
        }}
        placeholder='{"id": 114387, "z_rms_velocity_mm_s": 1.517, ...}'
        rows={6}
        spellCheck={false}
        aria-label="JSON da leitura"
      />

      {erro && (
        <p className="colar-erro" role="alert">
          {erro}
        </p>
      )}

      <div className="colar-acoes">
        <button type="button" className="botao botao-primario" onClick={usar}>
          Usar esta leitura
        </button>
        <button
          type="button"
          className="botao"
          onClick={() => {
            setTexto(EXEMPLO_DO_ENUNCIADO)
            setErro(null)
          }}
        >
          Preencher com o exemplo do enunciado
        </button>
      </div>
    </div>
  )
}
