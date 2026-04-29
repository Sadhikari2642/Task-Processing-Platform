FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --production
COPY . .

FROM node:20-alpine
USER node
WORKDIR /home/node/app
COPY --from=builder /app .
EXPOSE 4000
CMD ["node","src/server.js"]
