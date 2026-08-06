/** Tipos do contrato da API. Espelham os schemas Pydantic do backend.
 *
 * Nenhum `any`: alterar um campo no backend precisa quebrar a compilacao aqui,
 * senao a divergencia so aparece em producao.
 */

export type MotivoDiagnostico =
  | 'diagnosticado'
  | 'vizinhanca_dividida'
  | 'familia_sem_historico'
  | 'estado_operacional'

export type MotivoCobertura =
  | 'coberto'
  | 'sem_documento'
  | 'estado_operacional'
  | 'sem_diagnostico'

export type MetodoExtracao = 'text' | 'ocr'

export interface Vizinho {
  id: number
  created_at: string
  canonical_fault: string
  fault_family: string
  similarity: number
  rpm: number
  temperature_c: number
}

export interface VotoFamilia {
  fault_family: string
  vizinhos: number
  peso: number
}

export interface PontoTemporal {
  dia: string
  total: number
}

export interface ContextoOperacional {
  rpm_min: number
  rpm_max: number
  rpm_medio: number
  temp_min: number
  temp_max: number
  temp_media: number
}

export interface Evidencia {
  vizinhos_da_familia: number
  eventos_da_familia: number
  primeiro_registro: string | null
  ultimo_registro: string | null
  frequencia_por_dia: number
  intervalo_medio_horas: number | null
  linha_do_tempo: PontoTemporal[]
  contexto_operacional: ContextoOperacional | null
}

export interface Citacao {
  documento: string
  pagina_inicial: number
  pagina_final: number
  secao: string | null
  metodo: MetodoExtracao
}

export interface Passo {
  texto: string
  citacoes: string[]
}

export interface RelatorioEmbasamento {
  afirmacoes: number
  embasadas: number
  removidas: string[]
  score: number
  verificado: boolean
}

export interface Prescricao {
  tipo: 'prescricao'
  diagnostico: string
  inspecao: Passo[]
  correcao: Passo[]
  validacao: Passo[]
  citacoes: Citacao[]
  avisos: string[]
  embasamento: RelatorioEmbasamento | null
}

export interface Recusa {
  tipo: 'recusa'
  motivo: 'sem_documento' | 'estado_operacional' | 'sem_diagnostico' | 'fora_de_dominio'
  mensagem: string
  familia: string | null
  sugestao: string | null
}

export interface DocumentoConsultado {
  arquivo: string
  titulo: string
  metodo: MetodoExtracao
  paginas: number
}

export interface Tempos {
  similaridade_ms: number
  cobertura_ms: number
  recuperacao_ms: number
  geracao_ms: number
  verificacao_ms: number
  total_ms: number
}

export interface RespostaAnalise {
  diagnostico: {
    familia: string | null
    confianca: number
    motivo: MotivoDiagnostico
    e_problema: boolean
    votos: VotoFamilia[]
    aviso: string | null
  }
  evidencia: Evidencia | null
  cobertura: {
    familia: string | null
    coberta: boolean
    motivo: MotivoCobertura
    documentos: DocumentoConsultado[]
  }
  prescricao: Prescricao | null
  recusa: Recusa | null
  vizinhos: Vizinho[]
  tempos: Tempos
  chamou_llm: boolean
}

/** Colunas que compoem o vetor de features. Ordem igual a do backend. */
export const COLUNAS_SENSOR = [
  'z_rms_velocity_mm_s',
  'x_rms_velocity_mm_s',
  'z_peak_acceleration_g',
  'x_peak_acceleration_g',
  'z_rms_acceleration_g',
  'x_rms_acceleration_g',
  'z_high_freq_rms_accel_g',
  'x_high_freq_rms_accel_g',
  'z_kurtosis',
  'x_kurtosis',
  'z_crest_factor',
  'x_crest_factor',
  'z_peak_vel_comp_freq_hz',
  'x_peak_vel_comp_freq_hz',
  'temperature_c',
  'rpm',
] as const

export type ColunaSensor = (typeof COLUNAS_SENSOR)[number]

export type EventoSensor = Record<ColunaSensor, number> & {
  id?: number
  created_at?: string
  pergunta?: string
}

export interface AmostraHoldout extends Record<ColunaSensor, number> {
  id: number
  created_at: string
  raw_fault: string
  fault_family: string
  split: string
}

export interface FamiliaResumo {
  familia: string
  descricao: string
  e_problema: boolean
  eventos: number
  coberta: boolean
  documentos: string[]
}

export interface VisaoGeral {
  total_eventos: number
  eventos_problema: number
  familias: number
  familias_problema: number
  familias_cobertas: number
  familias_descobertas: string[]
  documentos_indexados: number
  trechos_indexados: number
  periodo_inicio: string | null
  periodo_fim: string | null
  eventos_holdout: number
  ranking: FamiliaResumo[]
}

export interface PontoLinhaDoTempo {
  dia: string
  familia: string
  total: number
}

export interface DocumentoIndexado {
  id: number
  arquivo: string
  titulo: string
  familia: string | null
  paginas: number
  trechos: number
  metodo: MetodoExtracao
  confianca_ocr: number | null
  status: string
  erro: string | null
  criado_em: string
}

export interface ComponenteSaude {
  nome: string
  estado: 'ok' | 'degradado' | 'fora'
  detalhe: string | null
}

export interface Saude {
  estado: 'ok' | 'degradado' | 'fora'
  componentes: ComponenteSaude[]
}
