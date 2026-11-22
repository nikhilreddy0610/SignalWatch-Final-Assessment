const labDb = db.getSiblingDB("nosql_labs");

function ensureRole(name, privileges) {
  const existing = labDb.getRole(name);
  if (existing) {
    labDb.updateRole(name, { privileges, roles: [] });
  } else {
    labDb.createRole({ role: name, privileges, roles: [] });
  }
}

function ensureUser(name, password, roles) {
  const adminDb = db.getSiblingDB("admin");
  if (adminDb.getUser(name)) {
    adminDb.updateUser(name, { pwd: password, roles });
  } else {
    adminDb.createUser({ user: name, pwd: password, roles });
  }
}

ensureRole("appReader", [
  {
    resource: { db: "nosql_labs", collection: "public_data" },
    actions: ["find"]
  },
  {
    resource: { db: "nosql_labs", collection: "employees_safe" },
    actions: ["find"]
  }
]);

ensureRole("appWriter", [
  {
    resource: { db: "nosql_labs", collection: "orders" },
    actions: ["find", "insert", "update", "remove"]
  }
]);

ensureRole("hrReader", [
  {
    resource: { db: "nosql_labs", collection: "employees" },
    actions: ["find"]
  }
]);

ensureUser(process.env.APP_READ_USER, process.env.APP_READ_PASSWORD, [
  { role: "appReader", db: "nosql_labs" }
]);
ensureUser(process.env.APP_WRITE_USER, process.env.APP_WRITE_PASSWORD, [
  { role: "appWriter", db: "nosql_labs" }
]);
ensureUser(process.env.HR_USER, process.env.HR_PASSWORD, [
  { role: "hrReader", db: "nosql_labs" }
]);

print("[OK] Created or updated the least-privilege application and HR users.");
