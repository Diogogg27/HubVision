FROM node:20-slim

WORKDIR /app

COPY server/package*.json ./server/
RUN npm --prefix server install

COPY . .

EXPOSE 8787

CMD ["node", "server/server.js"]
