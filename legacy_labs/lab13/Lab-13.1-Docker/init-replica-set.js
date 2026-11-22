const admin = db.getSiblingDB("admin");
let initialized = false;

try {
  const status = admin.runCommand({ replSetGetStatus: 1 });
  if (status.ok === 1) {
    initialized = true;
  } else if (status.code !== 94 && status.codeName !== "NotYetInitialized") {
    throw new Error(`Unable to inspect replica set: ${JSON.stringify(status)}`);
  }
} catch (error) {
  if (error.code !== 94 && error.codeName !== "NotYetInitialized") {
    throw error;
  }
}

if (initialized) {
  print("Replica set is already initialized.");
} else {
  const result = rs.initiate({
    _id: "rs0",
    members: [
      { _id: 0, host: "mongo1:27017" },
      { _id: 1, host: "mongo2:27017" },
      { _id: 2, host: "mongo3:27017" }
    ]
  });
  if (result.ok !== 1) {
    throw new Error(`Replica set initialization failed: ${JSON.stringify(result)}`);
  }
  print("Replica set rs0 initialized.");
}
