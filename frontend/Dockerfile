# Build em dois estagios: o node so existe para compilar. A imagem final e um
# nginx servindo arquivos estaticos -- alguns megabytes, sem toolchain.

FROM node:22-alpine AS build

WORKDIR /app

# As dependencias mudam menos que o codigo: copiadas antes para aproveitar o
# cache de camada entre builds.
COPY package.json package-lock.json* ./
RUN npm ci

COPY tsconfig.json vite.config.ts index.html ./
COPY src ./src
RUN npm run build

# -----------------------------------------------------------------------------

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# A imagem do nginx substitui as variaveis dos templates na inicializacao. E o
# que permite injetar a chave interna sem grava-la na imagem.
ENV API_UPSTREAM=http://prescritiva-api:8000
ENV NGINX_ENVSUBST_TEMPLATE_SUFFIX=.template

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD wget -q --spider http://localhost/ || exit 1
