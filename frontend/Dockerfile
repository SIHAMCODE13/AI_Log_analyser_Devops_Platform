# =====================================================
# AI Log Analyzer — Frontend Dockerfile
# Multi-stage build: Node (build) → Nginx (serve)
# =====================================================

# Stage 1: Build (minimal here as we use plain HTML/CSS/JS)
FROM node:20-alpine AS builder
WORKDIR /app
# Copy all frontend assets
COPY templates/ ./templates/
COPY static/    ./static/

# Stage 2: Nginx production server
FROM nginx:1.25-alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our config
COPY nginx/nginx.conf /etc/nginx/conf.d/

# Copy app files
COPY --from=builder /app/templates/index.html /usr/share/nginx/html/index.html
COPY --from=builder /app/static/              /usr/share/nginx/html/static/

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD wget -qO- http://localhost:80/ | head -c 50 || exit 1

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
