const config = {
  _id: "rs1",
  members: [
    { _id: 0, host: "host.docker.internal:27117" },
    { _id: 1, host: "host.docker.internal:27118" },
    { _id: 2, host: "host.docker.internal:27119", arbiterOnly: true }
  ]
};

if (!db.hello().setName) {
  print("Initializing rs1 with two data-bearing members and one arbiter...");
  const result = rs.initiate(config);
  print(`rs.initiate returned ok=${result.ok}`);
} else {
  print("Replica set rs1 is already initialized.");
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
print("\nAn arbiter votes but stores no replica set data.");
