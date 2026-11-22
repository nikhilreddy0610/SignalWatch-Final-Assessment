# MongoDB Security Labs 12.1 and 12.2

This Docker demonstration implements authentication, least-privilege RBAC,
field-level redaction through a MongoDB view, and TLS-enforced connections.
The startup script generates a lab CA plus server and client certificates,
starts MongoDB with `--auth` and `--tlsMode requireTLS`, creates the users and
roles, and seeds sample data.

The lab objectives follow the referenced
[Chapter 12 sample](https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-12);
the Docker startup and verification workflow here is independently adapted
for this submission.

The certificates and database are kept in Docker volumes. The CA private key
and generated private keys are never copied into the image. The default
credentials below are for a local classroom demonstration only; change them
before exposing the service to another network.

## Run the labs

Requirements: Docker Desktop / Docker Engine with Compose.

```sh
docker compose up --build -d
docker compose ps
docker compose exec mongo /opt/lab/verify-rbac.sh
docker compose --profile verify run --rm tls-check
```

The MongoDB service is reachable only from the Docker host at
`localhost:27020` by default (override with `MONGO_PORT` if needed). The TLS
verifier checks that a CA-verified PyMongo connection can authenticate and
read sample data, then verifies a plaintext connection is rejected.

The sample identities are:

| User | Granted access |
|---|---|
| `app_user_read` | Find and standard aggregation pipelines on `public_data` and the `employees_safe` view |
| `app_user_write` | Find/insert/update/delete on `orders` only |
| `hr_user` | Find on the underlying `employees` collection |
| `lab_admin` | Lab administrator for setup and demonstration |

Default lab passwords are `ReadOnly-ChangeMe-2026`,
`Writer-ChangeMe-2026`, `HR-ChangeMe-2026`, and
`LabAdmin-ChangeMe-2026`, respectively. Supply replacements through environment
variables or a local `.env` file before starting the container. Do not use
these classroom defaults outside an isolated lab.

The `employees_safe` view masks SSNs as `***-**-NNNN` and omits `salary`.
The reader can query that view but cannot read `employees`; the HR user can
read the underlying collection. MongoDB authorizes standard aggregation
pipelines with the `find` action; `aggregate` is a command, not a grantable
privilege action.

## Demonstrate the TLS configuration

The server certificate is signed by the generated lab CA and has `localhost`,
`mongo`, and `127.0.0.1` subject alternative names. The client certificate is
also signed by that CA and is presented by mongosh and PyMongo. MongoDB only
accepts TLS connections.

To try a TLS mongosh connection from the container:

```sh
docker compose exec mongo mongosh \
  --host localhost --port 27017 --tls \
  --tlsCAFile /data/tls/ca.crt \
  --tlsCertificateKeyFile /data/tls/client.pem \
  --username app_user_read \
  --password 'ReadOnly-ChangeMe-2026' \
  --authenticationDatabase admin \
  --eval 'db.getSiblingDB("nosql_labs").public_data.findOne()'
```

The certificate chain is:

```text
MongoDB-Lab-CA (ca.crt)
  ├── mongo server certificate (server.crt, bundled with server.key as mongodb.pem)
  └── lab client certificate (client.crt, bundled with client.key as client.pem)
```

Certificates are generated inside the `mongo-tls` volume the first time the
container starts and expire after one year. This self-signed chain is for the
lab only, not production use.

## Build and publish to Docker Hub

Log in to Docker Hub locally, then build and push the MongoDB image. Replace
`YOUR_DOCKERHUB_USERNAME` with your account name:

```sh
docker login
docker build -t YOUR_DOCKERHUB_USERNAME/mongodb-security-labs:12 .
docker push YOUR_DOCKERHUB_USERNAME/mongodb-security-labs:12
```

The image requires the environment variables listed in `compose.yaml`. For a
local run, Compose supplies the classroom defaults; for a published
demonstration, use environment values you control and mount persistent data
volumes. Do not publish `.env` files, generated certificates, or private keys.

The PDF submission URL should point to:

```text
https://hub.docker.com/r/YOUR_DOCKERHUB_USERNAME/mongodb-security-labs
```

Replace the placeholder with the pushed repository URL before submitting the
PDF. Publishing requires the student's Docker Hub login and is not performed
by the build files.

## Stop the lab

```sh
docker compose down
```

To reset the demo data and regenerate the certificates as well:

```sh
docker compose down --volumes
```
