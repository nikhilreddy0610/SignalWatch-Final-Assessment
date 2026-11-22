const config = rs.conf();
const priorities = new Map([
  ["host.docker.internal:27217", 2],
  ["host.docker.internal:27218", 3],
  ["host.docker.internal:27219", 1]
]);

config.members.forEach((member) => {
  const priority = priorities.get(member.host);
  if (priority === undefined) {
    throw new Error(`Unexpected replica set member: ${member.host}`);
  }
  member.priority = priority;
});

print("Applying election priorities (mongo1=2, mongo2=3, mongo3=1)...");
printjson(rs.reconfig(config));
print("\nExpected order when all members are healthy and caught up:");
print("  mongo2 (priority 3), then mongo1 (priority 2), then mongo3 (priority 1)");
print("After mongo2 is PRIMARY, predict mongo1 as its step-down successor.");
