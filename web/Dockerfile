# Next.js frontend for ShipTrack AI (standalone output).
FROM node:22-slim AS builder
WORKDIR /app
ARG BACKEND_URL=http://backend:5000
ENV BACKEND_URL=$BACKEND_URL
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
# Backend service URL used by Next's /api proxy (next.config rewrites).
ENV BACKEND_URL=http://backend:5000
ENV PORT=3000
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
