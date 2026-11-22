import os

from pymongo import MongoClient
from pymongo.errors import PyMongoError


host = os.environ.get("MONGO_HOST", "localhost")
username = os.environ["APP_READ_USER"]
password = os.environ["APP_READ_PASSWORD"]
tls_uri = (
    f"mongodb://{host}:27017/"
    "?tls=true&tlsCAFile=/certs/ca.crt"
    "&tlsCertificateKeyFile=/certs/client.pem"
    "&serverSelectionTimeoutMS=5000"
)

with MongoClient(tls_uri, username=username, password=password, authSource="admin") as client:
    client.admin.command("ping")
    sample = client["nosql_labs"]["public_data"].find_one()
    if not sample:
        raise RuntimeError("The TLS connection succeeded, but the sample read returned no data.")
    print("[PASS] PyMongo authenticated over verified TLS and read sample data.")

plain_uri = f"mongodb://{host}:27017/?serverSelectionTimeoutMS=5000"
try:
    with MongoClient(plain_uri) as client:
        client.admin.command("ping")
except PyMongoError as error:
    print(f"[PASS] Plaintext connection was rejected: {type(error).__name__}.")
else:
    raise RuntimeError("Plaintext connection unexpectedly succeeded; TLS is not being enforced.")
