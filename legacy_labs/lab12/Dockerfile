FROM mongo:8.0

COPY scripts/mongo-entrypoint.sh /usr/local/bin/mongo-entrypoint
COPY scripts/create-admin.js /opt/lab/create-admin.js
COPY scripts/init-users.js /opt/lab/init-users.js
COPY scripts/seed.js /opt/lab/seed.js
COPY scripts/verify-rbac.sh /opt/lab/verify-rbac.sh

RUN chmod 0755 /usr/local/bin/mongo-entrypoint /opt/lab/verify-rbac.sh

EXPOSE 27017
ENTRYPOINT ["/usr/local/bin/mongo-entrypoint"]
