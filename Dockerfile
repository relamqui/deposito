FROM nginx:alpine
COPY painel.html /usr/share/nginx/html/index.html
RUN sed -i 's/listen  *80;/listen 8010;/g' /etc/nginx/conf.d/default.conf
EXPOSE 8010
