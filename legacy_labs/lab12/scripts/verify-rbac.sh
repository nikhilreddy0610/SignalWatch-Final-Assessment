#!/usr/bin/env bash
set -Eeuo pipefail

MONGO_URI='mongodb://127.0.0.1:27017/?tls=true&tlsCAFile=/data/tls/ca.crt&tlsCertificateKeyFile=/data/tls/client.pem&serverSelectionTimeoutMS=30000'
TLS_ARGS=(--quiet "$MONGO_URI" --authenticationDatabase admin)

expect_unauthorized() {
  local user=$1 password=$2 eval_script=$3 label=$4
  mongosh "${TLS_ARGS[@]}" --username "$user" --password "$password" \
    --eval "$eval_script"
  echo "[PASS] $label"
}

echo "=== Reader permissions ==="
mongosh "${TLS_ARGS[@]}" --username "$APP_READ_USER" --password "$APP_READ_PASSWORD" \
  --eval '
    const lab = db.getSiblingDB("nosql_labs");
    if (!lab.public_data.findOne()) quit(1);
    if (lab.public_data.aggregate([{ $count: "records" }]).toArray()[0].records < 1) quit(1);
    const safeEmployee = lab.employees_safe.findOne();
    if (!safeEmployee || "salary" in safeEmployee || !safeEmployee.ssn.startsWith("***-**-")) quit(1);
    print("[PASS] Reader can find/aggregate public data and sees redacted employee fields.");
  '
expect_unauthorized "$APP_READ_USER" "$APP_READ_PASSWORD" '
  try {
    db.getSiblingDB("nosql_labs").orders.find().toArray();
    print("[FAIL] Reader unexpectedly read orders.");
    quit(1);
  } catch (e) {
    if (e.code !== 13) throw e;
  }
' "Reader is denied access to the orders collection."
expect_unauthorized "$APP_READ_USER" "$APP_READ_PASSWORD" '
  try {
    db.getSiblingDB("nosql_labs").public_data.insertOne({ unauthorized: true });
    print("[FAIL] Reader unexpectedly wrote data.");
    quit(1);
  } catch (e) {
    if (e.code !== 13) throw e;
  }
' "Reader is denied write access."

echo "=== Writer permissions ==="
mongosh "${TLS_ARGS[@]}" --username "$APP_WRITE_USER" --password "$APP_WRITE_PASSWORD" \
  --eval '
    const result = db.getSiblingDB("nosql_labs").orders.insertOne({ item: "RBAC check" });
    if (!result.acknowledged) quit(1);
    print("[PASS] Writer can insert into the orders collection.");
  '
expect_unauthorized "$APP_WRITE_USER" "$APP_WRITE_PASSWORD" '
  try {
    db.getSiblingDB("nosql_labs").public_data.find().toArray();
    print("[FAIL] Writer unexpectedly read public_data.");
    quit(1);
  } catch (e) {
    if (e.code !== 13) throw e;
  }
' "Writer is denied access to collections outside orders."

echo "=== HR permissions ==="
mongosh "${TLS_ARGS[@]}" --username "$HR_USER" --password "$HR_PASSWORD" \
  --eval '
    const employee = db.getSiblingDB("nosql_labs").employees.findOne();
    if (!employee || !("salary" in employee)) quit(1);
    print("[PASS] HR can read the underlying collection, including salary.");
  '

echo "[PASS] All RBAC and field-redaction checks completed."
