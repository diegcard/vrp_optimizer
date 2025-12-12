# ===========================================
# VRP Optimizer Frontend - Production Dockerfile
# Multi-stage build with Nginx for serving
# ===========================================

# Stage 1: Build the React application
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar archivos de configuración de dependencias
COPY package*.json ./

# Instalar dependencias (usa npm ci si hay package-lock.json, sino npm install)
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copiar código fuente
COPY . .

# Build de producción
RUN npm run build

# ===========================================
# Stage 2: Serve with Nginx
# ===========================================
FROM nginx:alpine AS production

# Copiar configuración de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar archivos build desde stage anterior
COPY --from=builder /app/dist /usr/share/nginx/html

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

# Exponer puerto 80
EXPOSE 80

# Nginx en foreground
CMD ["nginx", "-g", "daemon off;"]
