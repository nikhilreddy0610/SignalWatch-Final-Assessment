const labDb = db.getSiblingDB("nosql_labs");

labDb.public_data.updateOne(
  { _id: "sample-report" },
  { $set: { title: "Quarterly analytics", status: "ready" } },
  { upsert: true }
);
labDb.orders.updateOne(
  { _id: "sample-order" },
  { $set: { item: "Notebook", quantity: 2 } },
  { upsert: true }
);

const employees = [
  {
    _id: "employee-1",
    username: "arjun",
    email: "arjun@example.test",
    role: "admin",
    ssn: "111-22-3333",
    salary: 150000
  },
  {
    _id: "employee-2",
    username: "sneha",
    email: "sneha@example.test",
    role: "developer",
    ssn: "444-55-6666",
    salary: 120000
  }
];
for (const employee of employees) {
  labDb.employees.replaceOne({ _id: employee._id }, employee, { upsert: true });
}

if (labDb.getCollectionInfos({ name: "employees_safe" }).length > 0) {
  labDb.getCollection("employees_safe").drop();
}
labDb.createView("employees_safe", "employees", [
  {
    $project: {
      _id: 0,
      username: 1,
      email: 1,
      role: 1,
      ssn: {
        $concat: ["***-**-", { $substrBytes: ["$ssn", 7, 4] }]
      },
      salary: "$$REMOVE"
    }
  }
]);

print("[OK] Seeded sample collections and created the redacted employees_safe view.");
