# DashWise frontend image — build the Vite app, serve it with nginx.
# Build context is ./frontend (see docker-compose.yml).

# --- build stage -----------------------------------------------------------
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

# --- serve stage -----------------------------------------------------------
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
# On startup (before nginx), overlay the freshest analysis from the shared
# volume, if the pipeline has published one. Falls back to the baked-in sample.
COPY docker-entrypoint.d/40-analysis.sh /docker-entrypoint.d/40-analysis.sh
RUN chmod +x /docker-entrypoint.d/40-analysis.sh
EXPOSE 80
