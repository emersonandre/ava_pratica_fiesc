import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { enviar, enviarArquivo, obter } from './client'
import type {
  AmostraHoldout,
  Distribuicao,
  DocumentoIndexado,
  EventoSensor,
  FrequenciaDaFamilia,
  FamiliaResumo,
  PontoLinhaDoTempo,
  MensagemChat,
  RespostaAnalise,
  RespostaChat,
  Saude,
  VisaoGeral,
} from './types'

export const chaves = {
  saude: ['saude'] as const,
  visaoGeral: ['visao-geral'] as const,
  familias: ['familias'] as const,
  documentos: ['documentos'] as const,
  linhaDoTempo: (familia?: string) => ['linha-do-tempo', familia ?? 'todas'] as const,
  distribuicao: (metrica: string) => ['distribuicao', metrica] as const,
  frequencia: ['frequencia'] as const,
}

export function useSaude() {
  return useQuery({
    queryKey: chaves.saude,
    queryFn: () => obter<Saude>('/api/health'),
    refetchInterval: 30_000,
    retry: false,
  })
}

/** Faixa de valores de uma metrica em cada familia.
 *
 * `staleTime` alto de proposito: sao percentis sobre a base inteira, que so
 * mudam quando chega leitura nova. Trocar de metrica no seletor nao deve
 * refazer a consulta da metrica anterior.
 */
export function useDistribuicao(metrica: string) {
  return useQuery({
    queryKey: chaves.distribuicao(metrica),
    queryFn: () =>
      obter<Distribuicao>(
        `/api/internal/stats/distribution?metrica=${encodeURIComponent(metrica)}`,
      ),
    staleTime: 5 * 60_000,
  })
}

export function useFrequencia() {
  return useQuery({
    queryKey: chaves.frequencia,
    queryFn: () => obter<FrequenciaDaFamilia[]>('/api/internal/stats/frequency'),
    staleTime: 5 * 60_000,
  })
}

export function useVisaoGeral() {
  return useQuery({
    queryKey: chaves.visaoGeral,
    queryFn: () => obter<VisaoGeral>('/api/internal/stats/overview'),
  })
}

export function useFamilias() {
  return useQuery({
    queryKey: chaves.familias,
    queryFn: () => obter<FamiliaResumo[]>('/api/internal/faults'),
  })
}

export function useDocumentos() {
  return useQuery({
    queryKey: chaves.documentos,
    queryFn: () => obter<DocumentoIndexado[]>('/api/internal/documents'),
  })
}

export function useLinhaDoTempo(familia?: string) {
  return useQuery({
    queryKey: chaves.linhaDoTempo(familia),
    queryFn: () => {
      const busca = familia ? `?familia=${encodeURIComponent(familia)}` : ''
      return obter<PontoLinhaDoTempo[]>(`/api/internal/stats/timeline${busca}`)
    },
  })
}

export type Desfecho = 'qualquer' | 'prescricao' | 'sem_documento' | 'sem_diagnostico'

export interface PedidoAmostra {
  familia?: string
  desfecho?: Desfecho
  confiancaMinima?: number
}

/** Puxa um evento real do holdout -- dado que o modelo nunca viu.
 *
 * `desfecho` procura um evento que produza determinado resultado. O evento
 * continua real e nunca visto; muda apenas qual dos casos reais e mostrado.
 */
export function useAmostra() {
  return useMutation({
    mutationFn: ({ familia, desfecho, confiancaMinima }: PedidoAmostra) => {
      const busca = new URLSearchParams()
      if (familia) busca.set('familia', familia)
      if (desfecho && desfecho !== 'qualquer') busca.set('desfecho', desfecho)
      if (confiancaMinima !== undefined) {
        busca.set('confianca_minima', String(confiancaMinima))
      }
      const consulta = busca.toString()
      return obter<AmostraHoldout>(
        `/api/internal/events/sample${consulta ? `?${consulta}` : ''}`,
      )
    },
  })
}

export function useAnalisar() {
  return useMutation({
    mutationFn: (
      evento: EventoSensor & {
        fault?: string
        confianca_minima?: number
        gerar_prescricao?: boolean
      },
    ) =>
      enviar<RespostaAnalise>('/api/internal/events/analyze', evento),
  })
}

export interface RespostaUpload {
  document_id: number
  status: string
  arquivo: string
  titulo: string
  familia: string
  paginas: number
  trechos: number
  metodo: string
  ja_existia: boolean
  cobertura_atualizada: boolean
}

export function useRegistrarDocumento() {
  const cliente = useQueryClient()

  return useMutation({
    mutationFn: (dados: { arquivo: File; familia: string; titulo: string }) => {
      const formulario = new FormData()
      formulario.append('file', dados.arquivo)
      formulario.append('fault_family', dados.familia)
      formulario.append('title', dados.titulo)
      return enviarArquivo<RespostaUpload>('/api/internal/documents', formulario)
    },
    onSuccess: () => {
      // A cobertura muda: painel, familias e lista de documentos ficam obsoletos.
      void cliente.invalidateQueries({ queryKey: chaves.documentos })
      void cliente.invalidateQueries({ queryKey: chaves.familias })
      void cliente.invalidateQueries({ queryKey: chaves.visaoGeral })
    },
  })
}

export interface PedidoChat {
  evento: EventoSensor
  mensagens: MensagemChat[]
  pergunta: string
  confianca_minima?: number
}

/** Conversa ancorada em uma leitura. Cada pergunta recupera trechos de novo. */
export function useChat() {
  return useMutation({
    mutationFn: (pedido: PedidoChat) =>
      enviar<RespostaChat>('/api/internal/chat', pedido),
  })
}