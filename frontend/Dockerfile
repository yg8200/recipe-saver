# Multi-stage build: the first stage compiles the React app, the second serves only the result.
# Node, node_modules and the source code never end up in the final image.

# ---- Stage 1: build ----
FROM node:22-alpine AS build
WORKDIR /app

# Install dependencies in their own layer so they are cached until package*.json changes.
# `npm ci` installs exactly what package-lock.json says (reproducible), unlike `npm install`.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---- Stage 2: serve ----
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
