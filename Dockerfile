FROM nginx:alpine
COPY painel.html /usr/share/nginx/html/index.html
EXPOSE 80
