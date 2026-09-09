# syntax=docker/dockerfile:1

# ---- Builder: npm run build ----
# Vite 8 and the current dependency tree require a modern Node runtime.
FROM node:22.18-bookworm-slim AS builder

WORKDIR /app

COPY package.json package-lock.json ./

# The committed package-lock.json is currently incomplete and causes npm's
# Arborist to crash with "Cannot read properties of null (reading edgesOut)".
# Install from package.json until a complete lockfile is generated and committed.
RUN npm ci --no-audit --no-fund

COPY . .

# Vite вшивает VITE_*-переменные в bundle во время build, поэтому они должны
# быть доступны как build args (docker-compose.yml передаёт их из .env).
ARG VITE_API_MODE=http
ARG VITE_API_BASE_URL=/api
ENV VITE_API_MODE=${VITE_API_MODE} \
    VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

# ---- Runtime: nginx отдаёт dist/ + reverse-proxy на backend ----
FROM nginx:1.27-alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/templates/default.conf.template

ENV BACKEND_UPSTREAM=backend:5000

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
