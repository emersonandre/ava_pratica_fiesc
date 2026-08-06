import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { enviar, enviarArquivo, obter } from './client'
import type {
  AmostraHoldout,
  DocumentoIndexado,
  EventoSensor,
  FamiliaResumo,
  PontoLinhaDoTempo,
  RespostaAnalise,
  Saude,
  VisaoGeral,
} from './types'

export const chaves = {
  saude: ['saude'] as const,
  visaoGeral: ['visao-geral'] as const,
  familias: ['familias'] as const,
  documentos: ['documentos'] as const,
  linhaDoTempo: (familia?: string) => ['linha-do-tempo', familia ?? 'todas'] as const,
}

export function useSaude() {
  return useQuery({
    queryKey: chaves.saude,
    queryFn: () => obter<Saude>('/api/health'),
    refetchInterval: 30_000,
    retry: false,
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

/** Puxa um evento real do holdout -- dado que o modelo nunca viu. */
export function useAmostra() {
  return useMutation({
    mutationFn: (familia?: string) => {
      const busca = familia ? `?familia=${encodeURIComponent(familia)}` : ''
      return obter<AmostraHoldout>(`/api/internal/events/sample${busca}`)
    },
  })
}

export function useAnalisar() {
  return useMutation({
    mutationFn: (evento: EventoSensor) =>
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
