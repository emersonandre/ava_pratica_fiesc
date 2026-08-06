import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
    server: {
      port: Number(env.WEB_PORT ?? 5173),
      // Em desenvolvimento o Vite faz o papel do nginx: encaminha /api para a
      // API injetando a chave interna. Assim a chave nunca entra no bundle nem
      // aparece no painel de rede do navegador -- mesmo comportamento de producao.
      proxy: {
        '/api': {
          target: env.API_UPSTREAM_DEV ?? 'http://127.0.0.1:8001',
          changeOrigin: true,
          headers: env.INTERNAL_API_KEY
            ? { 'X-Internal-Key': env.INTERNAL_API_KEY }
            : undefined,
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
    },
  }
})
