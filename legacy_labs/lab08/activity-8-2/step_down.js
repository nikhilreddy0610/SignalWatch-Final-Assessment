print("Current replica set members:");
rs.status().members.forEach((member) => {
  print(`${member.name}  ${member.stateStr}  health=${member.health}`);
});

if (!db.hello().isWritablePrimary) {
  throw new Error("Run this script on the current PRIMARY member.");
}

print("\nStepping down this primary for 60 seconds...");
printjson(db.adminCommand({ replSetStepDown: 60 }));
