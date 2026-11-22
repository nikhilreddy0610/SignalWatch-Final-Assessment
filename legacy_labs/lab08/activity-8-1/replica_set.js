const config = {
  _id: "rs0",
  members: [
    { _id: 0, host: "host.docker.internal:27217" },
    { _id: 1, host: "host.docker.internal:27218" },
    { _id: 2, host: "host.docker.internal:27219" }
  ]
};

if (!db.hello().setName) {
  print("Initializing three-data-member replica set rs0...");
  const result = rs.initiate(config);
  print(`rs.initiate returned ok=${result.ok}`);
} else {
  print("Replica set rs0 is already initialized.");
}

let status;
for (let attempt = 0; attempt < 60; attempt += 1) {
  status = rs.status();
  if (status.members.some((member) => member.stateStr === "PRIMARY")) {
    break;
  }
  sleep(1000);
}

print("\nReplica set member status:");
status.members.forEach((member) => {
  print(`${member.name}  ${member.stateStr}  health=${member.health}`);
});
