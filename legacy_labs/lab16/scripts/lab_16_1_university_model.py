"""Lab 16.1 demo: university enrollment data modeled in MongoDB, Cassandra and Neo4j."""

from __future__ import annotations


def print_mongodb_demo() -> None:
    print("=== MongoDB: students collection ===")
    print({
        "student_id": "S-101",
        "name": "Alice Johnson",
        "email": "alice@university.edu",
        "enrollments": [
            {"course_id": "CS101", "semester": "Fall 2026", "grade": "A"},
            {"course_id": "MATH201", "semester": "Fall 2026", "grade": "A+"},
        ],
    })
    print("Query: db.students.find({ student_id: 'S-101' })")
    print("Query: db.students.aggregate([{ $unwind: '$enrollments' }, { $match: { 'enrollments.course_id': 'CS101' } }])")


def print_cassandra_demo() -> None:
    print("\n=== Cassandra: student_courses and course_students tables ===")
    print("CREATE TABLE student_courses (student_id TEXT, course_id TEXT, semester TEXT, PRIMARY KEY ((student_id), course_id));")
    print("CREATE TABLE course_students (course_id TEXT, student_id TEXT, semester TEXT, PRIMARY KEY ((course_id), student_id));")
    print("Query: SELECT course_id FROM student_courses WHERE student_id = 'S-101';")
    print("Query: SELECT student_id FROM course_students WHERE course_id = 'CS101';")


def print_neo4j_demo() -> None:
    print("\n=== Neo4j: Student nodes, Course nodes, ENROLLED_IN relationships ===")
    print("CREATE (alice:Student {id: 'S-101', name: 'Alice Johnson'})")
    print("CREATE (cs101:Course {id: 'CS101', title: 'Database Systems'})")
    print("CREATE (alice)-[:ENROLLED_IN {semester: 'Fall 2026'}]->(cs101)")
    print("Query: MATCH (s:Student)-[:ENROLLED_IN]->(c:Course) WHERE s.id = 'S-101' RETURN c.id")
    print("Query: MATCH (s:Student)-[:ENROLLED_IN]->(c:Course) WHERE c.id = 'CS101' RETURN s.id")


if __name__ == "__main__":
    print_mongodb_demo()
    print_cassandra_demo()
    print_neo4j_demo()
    print("\nNotes: MongoDB stores nested enrollment documents, Cassandra stores denormalized lookup tables, and Neo4j represents relationships as edges.")
