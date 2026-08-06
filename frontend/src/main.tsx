import '@fontsource-variable/ibm-plex-sans'
import '@fontsource/ibm-plex-sans-condensed/400.css'
import '@fontsource/ibm-plex-sans-condensed/600.css'
import '@fontsource/ibm-plex-mono/400.css'
import '@fontsource/ibm-plex-mono/500.css'
import './styles/tokens.css'
import './styles/base.css'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { Layout } from './components/Layout'
import { Analise } from './features/analise/Analise'
import { Documentos } from './features/documentos/Documentos'
import { Painel } from './features/painel/Painel'

const cliente = new QueryClient({
  defaultOptions: {
    queries: {
      // Os dados de sensor sao historicos e nao mudam sozinhos; refazer a
      // consulta a cada foco de janela so gastaria banco.
      refetchOnWindowFocus: false,
      staleTime: 60_000,
      retry: 1,
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={cliente}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Painel />} />
            <Route path="analise" element={<Analise />} />
            <Route path="documentos" element={<Documentos />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
