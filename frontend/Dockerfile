FROM node:20-alpine

WORKDIR /app

# Copia arquivos do package
COPY package*.json ./

# Instala dependências
RUN npm install

# Copia o restante do código da interface
COPY . .

# Expõe a porta de desenvolvimento
EXPOSE 3000

# Executa o servidor de desenvolvimento http-server
CMD ["npm", "run", "dev"]
