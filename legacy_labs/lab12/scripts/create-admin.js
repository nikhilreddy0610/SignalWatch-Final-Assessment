const adminDb = db.getSiblingDB("admin");
adminDb.createUser({
  user: process.env.MONGO_ADMIN_USER,
  pwd: process.env.MONGO_ADMIN_PASSWORD,
  roles: [{ role: "root", db: "admin" }]
});
print("[OK] Created the lab administrator.");
