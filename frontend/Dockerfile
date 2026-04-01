# Build stage
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production stage — serve via nginx
FROM nginx:alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html

# Proxy /api/* → backend:8000
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
