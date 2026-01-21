FROM node:18
WORKDIR /usr/src/app
COPY package.json package-lock.json* /usr/src/app/
# Limpiar cache y reinstalar dependencias (soluciona problema de Rollup)
RUN rm -rf node_modules package-lock.json && npm cache clean --force && npm install
COPY . /usr/src/app
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
