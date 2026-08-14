# syntax=docker/dockerfile:1

# ---- Builder: npm run build ----
FROM node:20-slim AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
# Regenerate lock file so all transitive deps are resolved, then do clean install
RUN npm install --package-lock-only --ignore-scripts && npm ci

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
