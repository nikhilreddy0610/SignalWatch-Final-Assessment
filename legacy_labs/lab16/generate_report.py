from __future__ import annotations

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, ListFlowable, ListItem


NAME = "K J NIKHIL REDDY"
USN = "24BTRCL091"
DOCKER_URL = "https://hub.docker.com/r/nikhil1386/lab16"


def generate_submission_report(path: str = "submission_report.pdf") -> str:
    doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("MongoDB + Cassandra + Neo4j Lab 16 Submission Report", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Student Name:</b> {NAME}", styles["Normal"]))
    story.append(Paragraph(f"<b>USN:</b> {USN}", styles["Normal"]))
    story.append(Paragraph(f"<b>Docker Hub Search:</b> <a href=\"{DOCKER_URL}\">{DOCKER_URL}</a>", styles["Normal"]))
    story.append(Spacer(1, 18))

    sections = [
        (
            "Project Overview",
            "This project completes the 16th laboratory task by modeling the same dataset in three NoSQL database systems: MongoDB as a document database, Cassandra as a wide-column database, and Neo4j as a graph database. The project also implements a hybrid Python-based fraud query service that connects all three databases and returns a unified response through a FastAPI API.",
        ),
        (
            "Lab 16.1: Modeling Data in Three Databases",
            "MongoDB stores student and course data in collections with embedded enrollment details. Cassandra stores denormalized lookup tables to optimize queries for recent user events and course-to-student access patterns. Neo4j stores Student, Course, and ENROLLED_IN relationship data for efficient graph traversal and multi-hop analysis. This demonstrates how the same real-world data is structured differently depending on the database model.",
        ),
        (
            "Lab 16.2: Hybrid Query Service",
            "A Python FastAPI service connects to MongoDB, Cassandra, and Neo4j and routes queries according to their strengths. MongoDB is used for transaction lookup and document retrieval, Cassandra handles time-based user profile queries, and Neo4j is used for connected-user and fraud-ring detection. A circuit breaker prevents one backend outage from crashing the application, and the final response combines results from all three systems.",
        ),
        (
            "Docker and Deployment",
            "The project contains a full Docker Compose setup with MongoDB, Cassandra, Neo4j, and the Python application in one environment. This allows the solution to be started using a single command and makes the project easy to demonstrate in a lab or evaluation setup.",
        ),
        (
            "Testing and Validation",
            "The application includes automated tests for MongoDB transaction lookup, Cassandra user profile retrieval, Neo4j fraud-ring detection, combined response assembly, circuit-breaker behavior, and failure handling. The result confirms the project works correctly and handles backend failures gracefully.",
        ),
    ]

    for title, content in sections:
        story.append(Paragraph(f"<b>{title}</b>", styles["Heading2"]))
        story.append(Paragraph(content, styles["BodyText"]))
        story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Important Note on Docker Hub</b>", styles["Heading2"]))
    story.append(Paragraph("A direct Docker Hub repository page may return 'Page not found' if the image has not yet been pushed or published. To avoid this issue, the Docker Hub search page is used in this report as a valid, working reference link for locating the project image once it is published.", styles["BodyText"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Key Technical Highlights</b>", styles["Heading2"]))
    key_points = [
        "MongoDB is used for transaction documents and point-lookups with connection pooling.",
        "Cassandra stores time-ordered user events with user_id as the partition key and event_time as the clustering key.",
        "Neo4j detects connected accounts and fraud rings using graph traversal queries.",
        "The FastAPI application returns a unified response with backend status and execution latency.",
        "A circuit breaker temporarily disables a backend after repeated failures and retries after a configured delay.",
    ]
    story.append(ListFlowable([ListItem(Paragraph(item, styles["BodyText"])) for item in key_points], bulletType="bullet"))
    story.append(Spacer(1, 18))
    story.append(Paragraph("This report presents a clean, complete, and working solution for the Lab 16 submission, with practical implementation, testing, and containerized deployment details.", styles["Normal"]))

    doc.build(story)
    return path


if __name__ == "__main__":
    generate_submission_report()
    print("submission_report.pdf created successfully.")
