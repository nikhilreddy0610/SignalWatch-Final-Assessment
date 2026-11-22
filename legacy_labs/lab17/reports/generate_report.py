"""Generate the submission PDF from genuine benchmark outputs."""

import csv
from html import escape
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "reports" / "comparison.csv"
GRAPH_PATH = ROOT / "reports" / "latency_recall.png"
PDF_PATH = ROOT / "reports" / "Lab17_Report.pdf"
PUBLISHED_IMAGE_URL = "https://hub.docker.com/r/nikhil1386/mongo-lab17-rag"


def build_pdf() -> None:
    load_dotenv(ROOT / ".env")
    if not CSV_PATH.exists() or not GRAPH_PATH.exists():
        raise FileNotFoundError("Run `python -m benchmark.run_benchmark` before generating the report.")
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"No measured results found in {CSV_PATH}")

    image_url = os.getenv("DOCKERHUB_IMAGE_URL", PUBLISHED_IMAGE_URL).strip()
    docker_status = (
        f'Published repository: <link href="{escape(image_url, quote=True)}" '
        f'color="#1565c0">{escape(image_url)}</link><br/>'
        "Pull command: docker pull nikhil1386/mongo-lab17-rag:latest"
        if image_url
        else "Docker Hub publication was not verified when this report was generated. "
        "No repository URL is asserted."
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontSize=24, leading=30, textColor=colors.HexColor("#15345b"), alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle(name="StudentDetails", parent=styles["BodyText"], fontSize=13, leading=19, alignment=TA_CENTER, textColor=colors.HexColor("#26364a")))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], textColor=colors.HexColor("#15345b"), spaceBefore=10, spaceAfter=5))
    styles.add(ParagraphStyle(name="BodySmall", parent=styles["BodyText"], fontSize=9, leading=13, spaceAfter=6))
    styles.add(ParagraphStyle(name="TableSmall", parent=styles["BodyText"], fontSize=7.5, leading=9))

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="MongoDB Lab 17 — RAG Pipeline and Vector Search Index Comparison",
        author="Lab 17 Submission",
    )
    story = [
        Spacer(1, 25 * mm),
        Paragraph("MONGODB LAB 17", styles["CoverTitle"]),
        Paragraph("RAG PIPELINE AND VECTOR SEARCH INDEX COMPARISON", styles["Heading2"]),
        Spacer(1, 8 * mm),
        Paragraph("<b>K J NIKHIL REDDY</b><br/>USN: 24BTRCL091", styles["StudentDetails"]),
        Spacer(1, 5 * mm),
        Paragraph(f"Submission report · {date.today().isoformat()}", styles["BodyText"]),
        Spacer(1, 15 * mm),
        Paragraph("<b>Objective</b>", styles["Section"]),
        Paragraph(
            "Build a threat-intelligence retrieval-augmented generation (RAG) application using MongoDB Atlas Vector Search and conversation memory, then measure local HNSW and IVF search against exact nearest-neighbor results.",
            styles["BodyText"],
        ),
        PageBreak(),
        Paragraph("1. Software and Technologies", styles["Section"]),
        Paragraph(
            "Python 3.12+, MongoDB Atlas and PyMongo, Voyage AI embeddings, OpenAI-compatible chat completions, FAISS, NumPy, Matplotlib, ReportLab, and Docker.",
            styles["BodyText"],
        ),
        Paragraph("2. Lab 17.1 — RAG Implementation", styles["Section"]),
        Paragraph(
            "Five concise threat-intelligence sources cover ransomware response, phishing and account compromise, command and control, vulnerability management, and indicators of compromise. Text is split into windows of up to 100 words with a 20-word overlap. Voyage AI voyage-3-lite creates 512-dimensional embeddings. MongoDB stores each chunk with text, source, and embedding fields.",
            styles["BodyText"],
        ),
        Paragraph("RAG architecture", styles["Section"]),
        Paragraph(
            "Question → Voyage query embedding → Atlas $vectorSearch (top 3) → retrieved sources + last five conversation messages → chat completion → saved user/assistant messages.",
            styles["BodyText"],
        ),
        Paragraph(
            "The Atlas index is declared as a vectorSearch index using cosine similarity, the embedding field, 512 dimensions, and a source filter. Atlas manages its approximate vector index implementation; Atlas does not expose a user-selected IVF index type in this configuration. `numCandidates` controls the candidate pool for approximate search. The IVF experiment in this submission uses FAISS locally and is not an Atlas index.",
            styles["BodyText"],
        ),
        Paragraph("Conversation memory", styles["Section"]),
        Paragraph(
            "A MongoDB conversations collection records user_id, UTC timestamp, role, and content. The CLI retrieves up to five recent messages for the next prompt and saves each user question and assistant answer.",
            styles["BodyText"],
        ),
        Paragraph("3. Lab 17.2 — Benchmark Methodology", styles["Section"]),
        Paragraph(
            "The benchmark uses a deterministic synthetic topic-structured corpus of 5,000 records, each with a normalized 384-dimensional vector, and runs 100 noisy in-corpus queries. Exact brute-force cosine search supplies the Top-20 reference. Recall is the overlap between approximate and exact Top-20 sets divided by 20, averaged across queries. Build time covers index construction/training and vector addition; latency is the mean of 100 single-query measurements. FAISS runs single-threaded for repeatable host-local measurements.",
            styles["BodyText"],
        ),
        Paragraph("HNSW uses M=32, efConstruction=80, efSearch=64. IVF uses nlist=100 and nprobe=10 with flat inner-product lists. These values are local FAISS parameters, not Atlas configuration options.",
            styles["BodyText"]),
        Paragraph("Measured results", styles["Section"]),
    ]

    columns = [
        "Index Type",
        "Parameters",
        "Build Time (seconds)",
        "Average Query Latency (ms)",
        "Recall (%)",
    ]
    table_data = [[Paragraph(f"<b>{name}</b>", styles["TableSmall"]) for name in columns]]
    for row in rows:
        table_data.append([Paragraph(row.get(column, ""), styles["TableSmall"]) for column in columns])
    table = Table(table_data, colWidths=[25 * mm, 53 * mm, 28 * mm, 30 * mm, 22 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#15345b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b7c5d5")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([
        table,
        Spacer(1, 5 * mm),
        Paragraph("Latency versus recall", styles["Section"]),
        Image(str(GRAPH_PATH), width=155 * mm, height=99 * mm),
        Paragraph(
            "Results are genuine measurements from this machine and installed FAISS build. Hardware, software versions, and index settings affect the results; rerun the benchmark to reproduce them on another host.",
            styles["BodySmall"],
        ),
        PageBreak(),
        Paragraph("4. Docker and Demonstration", styles["Section"]),
        Paragraph(
            "The Dockerfile uses Python 3.12 slim, installs the project requirements, copies only application and benchmark code, and starts the interactive RAG CLI. Use `docker compose up --build` after configuring a local .env file. The benchmark can be run separately with `docker run --rm --env-file .env --entrypoint python mongo-lab17-rag:latest -m benchmark.run_benchmark`.",
            styles["BodyText"],
        ),
        Paragraph("Docker Hub", styles["Section"]),
        Paragraph(docker_status, styles["BodyText"]),
        Paragraph("5. Conclusion", styles["Section"]),
        Paragraph(
            "The project demonstrates embedding-based retrieval, grounded generation, and persistent conversational context. The separate FAISS experiment produces measured HNSW and IVF latency/recall values against exact search while clearly distinguishing these local index implementations from MongoDB Atlas Vector Search.",
            styles["BodyText"],
        ),
        Spacer(1, 5 * mm),
        Paragraph(
            "Documentation reference: MongoDB Vector Search index types and definitions — "
            "https://www.mongodb.com/docs/vector-search/indexes/vector-search-type/",
            styles["BodySmall"],
        ),
    ])

    def page_footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#d4dce6"))
        canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#526174"))
        canvas.drawString(18 * mm, 9 * mm, "MongoDB Lab 17")
        canvas.drawRightString(A4[0] - 18 * mm, 9 * mm, f"Page {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    print(f"Generated {PDF_PATH}")


if __name__ == "__main__":
    build_pdf()
