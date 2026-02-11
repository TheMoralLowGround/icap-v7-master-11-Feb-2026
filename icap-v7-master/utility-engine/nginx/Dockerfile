FROM registry.access.redhat.com/ubi8/nginx-118:1-67

USER 0

RUN yum install -y gettext

USER 1001

WORKDIR /app

COPY ./nginx.conf /etc/nginx/nginx.conf

COPY ./app.conf.template /opt/app-root/etc/nginx.d/app.conf.template

USER 0

RUN chgrp -R 0 /opt/app-root/etc/nginx.d && \
    chmod -R g=u /opt/app-root/etc/nginx.d

COPY entrypoint.sh /usr/share/nginx/

RUN chmod +x /usr/share/nginx/entrypoint.sh

USER 1001

ENTRYPOINT ["/usr/share/nginx/entrypoint.sh"]

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]