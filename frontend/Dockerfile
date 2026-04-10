# frontend/Dockerfile

FROM node:18-slim

WORKDIR /app

# Copy package files first for layer caching
COPY package.json package-lock.json ./

RUN npm install

# Copy rest of frontend source
COPY . .

# Build the production React app
RUN npm run build

# Serve the built app using a lightweight static server
RUN npm install -g serve

EXPOSE 5173

CMD ["serve", "-s", "dist", "-l", "5173"]