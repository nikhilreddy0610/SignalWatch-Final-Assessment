from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "FINAL_ASSESSMENT_REPORT.pdf"

NAVY = colors.HexColor("#15324b")
BLUE = colors.HexColor("#1c668c")
CYAN = colors.HexColor("#24a4c7")
PALE = colors.HexColor("#eaf3f8")
INK = colors.HexColor("#273746")
MUTED = colors.HexColor("#60758a")
GRID = colors.HexColor("#c5d2dc")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=24, leading=29, textColor=NAVY, alignment=TA_CENTER, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="CoverSubtitle", parent=styles["Normal"], fontName="Helvetica",
    fontSize=12, leading=17, textColor=BLUE, alignment=TA_CENTER, spaceAfter=7,
))
styles.add(ParagraphStyle(
    name="CoverInstitution", parent=styles["Normal"], fontName="Helvetica-Bold",
    fontSize=12, leading=17, textColor=NAVY, alignment=TA_CENTER,
))
styles.add(ParagraphStyle(
    name="Section", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=15, leading=19, textColor=NAVY, spaceBefore=5, spaceAfter=9,
))
styles.add(ParagraphStyle(
    name="Subsection", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=11, leading=14, textColor=BLUE, spaceBefore=9, spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="BodySW", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=9.2, leading=13.2, textColor=INK, alignment=TA_LEFT, spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="SmallSW", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=7.6, leading=10.2, textColor=INK, spaceAfter=2,
))
styles.add(ParagraphStyle(
    name="CaptionSW", parent=styles["BodyText"], fontName="Helvetica-Oblique",
    fontSize=8, leading=10.5, textColor=MUTED, alignment=TA_CENTER, spaceBefore=4, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="CalloutSW", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=9, leading=13, textColor=NAVY, backColor=PALE, borderColor=CYAN,
    borderWidth=0.7, borderPadding=8, spaceBefore=5, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="CoverMeta", parent=styles["Normal"], fontName="Helvetica",
    fontSize=10.2, leading=16, textColor=INK, alignment=TA_CENTER,
))


def para(text, style="BodySW"):
    return Paragraph(escape(text), styles[style])


def rich(text, style="BodySW"):
    return Paragraph(text, styles[style])


def bullet_list(items):
    return ListFlowable(
        [ListItem(para(item), leftIndent=9) for item in items],
        bulletType="bullet", start="circle", leftIndent=17, bulletFontSize=6,
        bulletColor=CYAN, spaceAfter=5,
    )


def make_table(headers, rows, widths, font_size=7.6):
    cell_style = ParagraphStyle(
        f"TableCell{font_size}", parent=styles["SmallSW"],
        fontSize=font_size, leading=font_size + 2.4,
    )
    header_style = ParagraphStyle(
        f"TableHeader{font_size}", parent=cell_style,
        fontName="Helvetica-Bold", textColor=colors.white,
    )
    data = [[Paragraph(escape(str(value)), header_style) for value in headers]]
    data += [[Paragraph(escape(str(value)), cell_style) for value in row] for row in rows]
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.35, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f8fa")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


class ArchitectureDiagram(Flowable):
    def __init__(self):
        super().__init__()
        self.width = 178 * mm
        self.height = 54 * mm

    def draw(self):
        c = self.canv
        scale = mm

        def box(x, y, w, h, title, detail):
            c.setFillColor(PALE)
            c.setStrokeColor(BLUE)
            c.roundRect(x * scale, y * scale, w * scale, h * scale, 2 * mm, fill=1, stroke=1)
            c.setFillColor(NAVY)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString((x + w / 2) * scale, (y + h - 7) * scale, title)
            c.setFillColor(INK)
            c.setFont("Helvetica", 6.8)
            c.setFont("Helvetica", 6.5)
            c.drawCentredString((x + w / 2) * scale, (y + 5) * scale, detail)

        def arrow(x1, y1, x2, y2):
            c.setStrokeColor(CYAN)
            c.setFillColor(CYAN)
            c.setLineWidth(1.2)
            c.line(x1 * scale, y1 * scale, x2 * scale, y2 * scale)
            if abs(x2 - x1) >= abs(y2 - y1):
                sign = 1 if x2 >= x1 else -1
                points = [(x2, y2), (x2 - 2.1 * sign, y2 + 1.3), (x2 - 2.1 * sign, y2 - 1.3)]
            else:
                sign = 1 if y2 >= y1 else -1
                points = [(x2, y2), (x2 + 1.3, y2 - 2.1 * sign), (x2 - 1.3, y2 - 2.1 * sign)]
            path = c.beginPath()
            path.moveTo(points[0][0] * scale, points[0][1] * scale)
            path.lineTo(points[1][0] * scale, points[1][1] * scale)
            path.lineTo(points[2][0] * scale, points[2][1] * scale)
            path.close()
            c.drawPath(path, fill=1, stroke=0)

        box(2, 31, 39, 18, "Browser UI", "chat and filters")
        box(67, 31, 45, 18, "FastAPI service", "RAG and APIs")
        box(135, 31, 40, 18, "MongoDB", "records and vectors")
        box(67, 3, 45, 18, "Ollama", "LLM and embeddings")
        box(135, 3, 40, 18, "External sources", "RSS and OSV")
        box(2, 3, 39, 18, "Host scanner", "read-only packages")
        arrow(41, 40, 67, 40)
        arrow(112, 40, 135, 40)
        arrow(89, 31, 89, 21)
        arrow(112, 12, 135, 12)
        arrow(41, 12, 67, 35)


def page_chrome(canvas, doc):
    canvas.saveState()
    page_width, page_height = A4
    if doc.page > 1:
        canvas.setStrokeColor(GRID)
        canvas.setLineWidth(0.5)
        canvas.line(17 * mm, page_height - 13 * mm, page_width - 17 * mm, page_height - 13 * mm)
        canvas.setFont("Helvetica-Bold", 7.5)
        canvas.setFillColor(BLUE)
        canvas.drawString(17 * mm, page_height - 10 * mm, "SIGNALWATCH  |  MINI PROJECT REPORT")
    canvas.setStrokeColor(GRID)
    canvas.line(17 * mm, 13 * mm, page_width - 17 * mm, 13 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(17 * mm, 8.5 * mm, "K J NIKHIL REDDY  |  24BTRCL091")
    canvas.drawRightString(page_width - 17 * mm, 8.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


story = []
story.extend([
    Spacer(1, 12 * mm),
    para("FACULTY OF ENGINEERING AND TECHNOLOGY", "CoverInstitution"),
    para("JAIN (Deemed-to-be University), Bengaluru", "CoverInstitution"),
    Spacer(1, 9 * mm),
    para("23CSE528", "CoverSubtitle"),
    para("NoSQL Databases using MongoDB", "CoverSubtitle"),
    Spacer(1, 9 * mm),
    para("MINI PROJECT REPORT", "CoverSubtitle"),
    Spacer(1, 3 * mm),
    para("Threat Intelligence Chat: SignalWatch", "CoverTitle"),
    para("Building and Deploying an LLM/SLM-backed Chat Application on MongoDB", "CoverSubtitle"),
    Spacer(1, 7 * mm),
    para("SUBMITTED BY", "CoverSubtitle"),
    para("Name: K J NIKHIL REDDY", "CoverMeta"),
    para("USN: 24BTRCL091", "CoverMeta"),
    para("Programme: B.Tech", "CoverMeta"),
    para("Section / Semester: AIML-B / 5th", "CoverMeta"),
    Spacer(1, 9 * mm),
    para("SUBMITTED TO", "CoverSubtitle"),
    para("Sujeet S Jagtap", "CoverMeta"),
    para("Faculty, NoSQL Databases using MongoDB", "CoverMeta"),
    Spacer(1, 12 * mm),
    para("Report prepared: 22 November 2026", "CoverMeta"),
    Spacer(1, 11 * mm),
    Table(
        [[para("____________________________", "CoverMeta"), para("____________________________", "CoverMeta")],
         [para("Signature of Student", "SmallSW"), para("Signature of Faculty", "SmallSW")]],
        colWidths=[86 * mm, 86 * mm],
        style=TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]),
    ),
    PageBreak(),
])

story.extend([
    para("Abstract", "Section"),
    para(
        "SignalWatch is a local-first threat-intelligence chat application that combines a FastAPI service, "
        "MongoDB operational storage, Ollama language and embedding models, a browser dashboard, and a "
        "read-only host inventory agent. It consolidates the supplied MongoDB Labs 7-18 source material into "
        "a retrieval-augmented generation (RAG) knowledge base and stores conversation messages for follow-up "
        "questions. Threat records use Anticipated, Active, Evolving, and Resolved lifecycle states. The "
        "dashboard also supports reviewed threat-record management, external RSS leads, and searchable scan "
        "findings. At the verified snapshot for this report, MongoDB held 303 knowledge documents: 14 curated "
        "course references and 289 chunks from preserved lab files. A read-only macOS inventory contained "
        "28 packages and submitted 93 OSV advisory matches for review. These matches are leads, not proof of "
        "exploitation. The application was verified with MongoDB and Ollama connected; chat citations, "
        "conversation persistence, threat CRUD, and finding filters were exercised. The report distinguishes "
        "this tested local setup from the Docker deployment configuration, which was not rebuilt as part of "
        "this verification.",
        "BodySW",
    ),
    rich("<b>Keywords:</b> MongoDB, threat intelligence, Ollama, RAG, embeddings, conversation memory, FastAPI, OSV", "BodySW"),
    para("1. Introduction", "Section"),
    para(
        "Security information is difficult to use when advisories, package inventories, course knowledge, and "
        "operational notes are separated. A chat interface can make this information easier to query, but a "
        "language model must not be treated as an authoritative threat feed: it may confuse examples with "
        "evidence or invent affected versions. SignalWatch addresses this problem by retrieving local project "
        "material and stored records before generating answers, presenting source references, and explicitly "
        "marking synthetic records and unreviewed external leads.",
    ),
    para(
        "The application is intended as a defensive coursework demonstration. It provides explanations and "
        "review guidance; it does not execute remediation commands or claim that a host has been repaired. "
        "The user must validate advisories and approve any action outside the chat.",
    ),
    para("2. Problem Statement and Objectives", "Section"),
    para(
        "The project goal is to demonstrate how MongoDB can serve as the operational store, local knowledge "
        "store, and conversation-memory store for a small-model chat application. The implementation objectives are:",
    ),
    bullet_list([
        "Integrate MongoDB Labs 7-18 concepts into one browser-accessible threat-intelligence application.",
        "Store threat records, scanner submissions, advisory findings, RSS leads, knowledge chunks, and chat messages in MongoDB.",
        "Retrieve relevant lab passages with embeddings and lexical matching, then return friendly answers with source identifiers.",
        "Support four lifecycle states and provide user-facing create, edit, delete, search, and filtering workflows.",
        "Keep host inventory collection explicit and read-only; label advisory matches as requiring human review.",
        "Expose health and metrics endpoints and document configuration and deployment limitations accurately.",
    ]),
    PageBreak(),
])

story.extend([
    para("3. Background and Lab Integration", "Section"),
    para(
        "The application uses document-oriented records and indexes from the course, replica-set and consistency "
        "principles, security guidance, Docker deployment patterns, monitoring, and the RAG workflow. Original "
        "source folders for Labs 7-18 are preserved under legacy_labs/ for traceability. The project is a "
        "consolidated implementation and does not claim that every lab's separate cluster, benchmark, or "
        "Cassandra/Neo4j service is started by the final application.",
    ),
    make_table(
        ["Lab", "Concept applied or represented"],
        [
            ("7", "CTI source/report/IOC modelling, references, indexes, working-set and WiredTiger monitoring concepts."),
            ("8", "Replica-set topology, majority operations, elections, and failover concepts."),
            ("9", "Write concern and durability, availability, and latency trade-offs."),
            ("10", "Transaction-ready replica-set deployment principles and atomicity concepts."),
            ("11", "Shard-key distribution, query targeting, and hotspot considerations."),
            ("12", "Environment-based secrets, least privilege, TLS, and RBAC guidance."),
            ("13", "Docker Compose, health checks, persistent volumes, and replica-set deployment."),
            ("14", "Health/metrics endpoints and backup/restore operational guidance."),
            ("15", "Session isolation concepts, optional API-token protection, and rate limiting; full JWT tenancy is future work."),
            ("16", "MongoDB, Cassandra, and Neo4j workload comparison; reference implementations remain in legacy sources."),
            ("17", "Knowledge ingestion, embeddings, RAG retrieval, conversation memory, and vector-search comparison."),
            ("18", "Threat lifecycle, heuristic false-positive review, synthetic examples, and comparative data concepts."),
        ],
        [15 * mm, 157 * mm],
        font_size=7.3,
    ),
    Spacer(1, 5 * mm),
    rich(
        "<b>Scope note.</b> This report covers the delivered SignalWatch application and preserved Labs 7-18 "
        "materials. It does not claim that Labs 1-6 or each original lab's independent infrastructure is "
        "implemented in the final runtime.",
        "CalloutSW",
    ),
    para("4. System Architecture", "Section"),
    para(
        "The browser communicates with the FastAPI application over HTTP. The API reads and writes threat, "
        "finding, scan, feed, knowledge, and message documents in MongoDB. For chat requests it selects an "
        "installed Ollama model, retrieves relevant knowledge, adds bounded session history, and returns an "
        "answer with source metadata. The host scanner runs separately on the user's computer and submits its "
        "read-only inventory to the scan endpoint.",
    ),
    ArchitectureDiagram(),
    para("Figure 1. SignalWatch runtime components and the principal data paths.", "CaptionSW"),
    PageBreak(),
])

story.extend([
    para("4.1 Runtime Configuration", "Subsection"),
    make_table(
        ["Component", "Verified implementation"],
        [
            ("Web/API", "Python FastAPI service on localhost:8000, with static HTML, CSS, and JavaScript."),
            ("Operational database", "Local MongoDB Community service, database signalwatch; collections persist outside the app process."),
            ("Chat model", "Ollama model llama3.2:3b (3B class), selected from the installed model list."),
            ("Embedding model", "Ollama nomic-embed-text:latest; the indexed vectors observed in MongoDB have 768 dimensions."),
            ("Knowledge base", "303 documents: 14 curated references and 289 source-file chunks from Labs 7-18."),
            ("External feeds", "CISA, BleepingComputer, and The Hacker News RSS; items are stored as unreviewed leads."),
            ("Deployment artifacts", "Dockerfile and docker-compose.yml are provided; this report's runtime verification used the local MongoDB and Ollama services."),
        ],
        [41 * mm, 131 * mm],
    ),
    Spacer(1, 4 * mm),
    rich(
        "<b>Deployment verification boundary.</b> The local application, MongoDB connection, and Ollama inference "
        "were verified. A fresh Docker image build and Compose deployment were not part of this report's test "
        "run; they are not represented as passed.",
        "CalloutSW",
    ),
    para("4.2 MongoDB Data Model", "Subsection"),
    make_table(
        ["Collection", "Purpose and representative fields"],
        [
            ("threats", "Platform, title, status, severity, CVE/advisory, summary, mitigation, evidence URL, and update time."),
            ("scans", "Host/platform metadata, scan timestamp, package inventory, and submitted findings."),
            ("findings", "Advisory match, package/version, CVE or OSV identifier, severity, source, review status, host, and scan ID."),
            ("knowledge", "Title, source path, chunk index, text, platform tags, embedding vector, and created time."),
            ("feed_reports", "Feed fingerprint, title, summary, URL, source, publication time, and unreviewed classification."),
            ("messages", "Session ID, role, content, and timestamp for persisted multi-turn conversations."),
        ],
        [35 * mm, 137 * mm],
    ),
    para(
        "Indexes support common list and lookup paths, including platform/status/update ordering for threats, "
        "CVE lookup, host and timestamp scans, session and timestamp messages, knowledge titles, and unique "
        "feed fingerprints. A single local MongoDB instance is used for the verified run; replica-set mode is "
        "configured in Docker Compose for transaction-oriented demonstrations.",
    ),
    para("5. Threat Records, Feeds, and Host Inventory", "Section"),
    para("5.1 Threat Lifecycle and Review", "Subsection"),
    para(
        "The four supported states are Anticipated, Active, Evolving, and Resolved. An active classification "
        "requires evidence of current activity; a resolved classification should follow verified containment "
        "or remediation rather than merely the availability of a patch. Four seed records are labelled "
        "DEMO ONLY and synthetic. The dashboard can add, edit, delete, search, and filter records, and retains "
        "the evidence URL and mitigation notes provided by the analyst.",
    ),
    para("5.2 External Intelligence Leads", "Subsection"),
    para(
        "The refresh workflow retrieves RSS entries from CISA, BleepingComputer, and The Hacker News and "
        "deduplicates them by URL fingerprint. The verified database snapshot contained 55 feed leads. "
        "Feed content is untrusted and remains unreviewed; ingestion does not automatically create an active "
        "threat or confirm exploitation.",
    ),
    PageBreak(),
])

story.extend([
    para("5.3 Read-only Host Inventory", "Subsection"),
    para(
        "The explicitly invoked host_agent/scan_host.py inventories supported package managers and Python "
        "packages, then queries OSV for exact package/version matches where an ecosystem is available. The "
        "scanner submits packages and advisory results to /api/scan and does not install, remove, update, or "
        "otherwise modify software. The verified macOS scan observed 28 packages and submitted 93 advisory "
        "matches. The dashboard marks findings as needing review and presents a reminder that an advisory "
        "match is not proof of exploitability.",
    ),
    rich(
        "<b>Platform boundary.</b> A host scan only covers inventory accessible to the scanner on the machine "
        "where it runs. The platform selector filters stored records; it does not remotely scan Windows, "
        "Android, or iOS devices.",
        "CalloutSW",
    ),
    para("6. Knowledge Ingestion and Retrieval-Augmented Generation", "Section"),
    para("6.1 Ingestion", "Subsection"),
    para(
        "At startup, the service seeds curated Lab 7-18 concepts and indexes eligible preserved source files. "
        "Supported file types include Markdown, Python, text, JavaScript, YAML, and shell scripts. Large files "
        "and cache/secret directories are skipped. The implementation applies simple pattern-based redaction "
        "for common inline secret assignments before indexing. Source passages are up to 2,200 characters "
        "with an approximate 300-character overlap, and a per-file chunk cap bounds the corpus.",
    ),
    para(
        "When nomic-embed-text is installed, passage embeddings are generated through Ollama and stored with "
        "the MongoDB document. The observed vectors are 768-dimensional. If the embedding service is missing "
        "or fails, the code retains lexical retrieval as a fallback.",
    ),
    para("6.2 Retrieval and Source References", "Subsection"),
    para(
        "For a chat question, the service embeds the query when possible and ranks up to 1,500 knowledge "
        "documents. It compares cosine similarity with a title-weighted lexical score and returns the best six "
        "passages. The lexical score gives additional weight to title matches and removes common stop words. "
        "For short or elliptical follow-ups, the latest prior user question is included in the retrieval query; "
        "longer new questions are retrieved independently.",
    ),
    para(
        "Retrieved passages receive S1, S2, and similar references. Relevant stored findings, threat records, "
        "and feed leads can receive V, T, and F references. The prompt asks the model to cite only supplied "
        "references, distinguish confirmed evidence from synthetic or unreviewed data, and state uncertainty. "
        "The API also returns a source list for the browser to display; if the model omits citations while "
        "sources were supplied, the response receives a deterministic Sources line.",
    ),
    para("6.3 Conversation Memory", "Subsection"),
    para(
        "Each browser chat has a random session identifier stored in localStorage. Messages are persisted in "
        "MongoDB and the recent eight messages are included in subsequent model prompts. Users can restore "
        "the current session after reload, start a separate chat, or clear that session's history. Session "
        "history is a convenience boundary, not a complete multi-user authentication or tenant-isolation system.",
    ),
    PageBreak(),
])

story.extend([
    para("7. Application Interface and API", "Section"),
    para(
        "The responsive browser interface combines service status, lifecycle counts, threat-record workflows, "
        "external leads, the assistant, and scan findings. Each panel reports request failures rather than "
        "silently treating them as successful data. Findings expand to show package, version, advisory, "
        "recommendation, and source link. External items are labelled unreviewed.",
    ),
    make_table(
        ["Endpoint", "Function"],
        [
            ("GET /health", "Reports MongoDB connectivity, available Ollama models, and current time."),
            ("GET /api/threats", "Lists records with platform, lifecycle, and search filters."),
            ("POST /api/threats", "Creates a validated lifecycle record."),
            ("PATCH /api/threats/{id}", "Updates a record's permitted evidence and lifecycle fields."),
            ("DELETE /api/threats/{id}", "Deletes the selected threat record."),
            ("POST /api/chat", "Retrieves evidence, generates a response, and stores the conversation turn."),
            ("GET/DELETE /api/chat/{session_id}", "Restores or clears a session's saved message history."),
            ("POST /api/scan and GET /api/findings", "Accepts host inventory and lists filterable findings."),
            ("POST /api/feeds/refresh and GET /api/feeds", "Ingests RSS leads and displays stored entries."),
            ("GET /metrics", "Exposes request, error, latency, and model token counters."),
        ],
        [55 * mm, 117 * mm],
        font_size=7.2,
    ),
    para("8. Safety, Privacy, and Access Controls", "Section"),
    bullet_list([
        "The host scanner is opt-in and read-only. SignalWatch does not execute commands returned by the language model.",
        "Threat examples are synthetic; RSS items and OSV results are advisory leads that require analyst verification.",
        "The assistant is instructed not to fabricate CVEs, affected versions, exploitation status, or completed remediation.",
        "API_TOKEN is optional and is checked by middleware when configured. The browser stores a supplied key in sessionStorage for the current tab.",
        "At the verified local run the API token was not configured, so local API access was open. Do not expose this service publicly in that configuration.",
        "The in-memory chat rate limiter is process-local and is not a substitute for a production gateway or distributed rate limit.",
        "Pattern-based secret redaction reduces some accidental exposure but is not a complete secret scanner. Keep .env files and credentials out of source control.",
    ]),
    rich(
        "<b>Production hardening.</b> Configure a strong API token or user authentication, TLS, MongoDB "
        "authentication/authorization, per-user session authorization, request limits at a reverse proxy, "
        "secret management, and tested backup/restore before external deployment.",
        "CalloutSW",
    ),
    para("9. Verification and Results", "Section"),
    para(
        "Verification combined live endpoint checks, targeted API exercises, browser rendering, and repository "
        "static checks. The values below are a snapshot of the local demonstration environment and are not "
        "benchmark results.",
    ),
    make_table(
        ["Check", "Observed result"],
        [
            ("Service health", "MongoDB reported connected; Ollama reported llama3.2:3b and nomic-embed-text:latest."),
            ("Knowledge ingestion", "303 documents total: 14 curated entries and 289 preserved-source chunks; 768-dimensional embeddings observed."),
            ("Threat dashboard", "4 seed records, each explicitly marked as a synthetic demo."),
            ("External feeds", "55 feed reports stored from the configured RSS sources."),
            ("Latest host inventory", "macOS; 28 packages; 93 OSV matches submitted with needs_review status."),
            ("Threat CRUD and search", "Create, search/filter, edit, and delete integration exercise passed."),
            ("Chat grounding", "Multi-turn test returned answers with source references and retained both messages in the session."),
            ("Session control", "History endpoint returned the saved messages; clear-history endpoint deleted the test session messages."),
            ("Findings filter", "macOS + needs_review + starlette query returned matching findings."),
            ("Code checks", "Python compilation, JavaScript syntax check, and offline structural checks passed."),
        ],
        [43 * mm, 129 * mm],
        font_size=7.3,
    ),
    PageBreak(),
])

story.extend([
    para("10. Limitations and Future Work", "Section"),
    bullet_list([
        "The locally verified database is a single MongoDB instance. Replica-set transaction behavior is configured for the Compose deployment but was not used in the local test run.",
        "Local MongoDB Community does not provide Atlas $vectorSearch. This application retrieves stored vectors by client-side cosine ranking with lexical fallback.",
        "The chat uses a small local model. Answers may still be incomplete or incorrect; citations and human review reduce, but do not eliminate, that risk.",
        "The scanner is package-oriented and is not a full malware, filesystem, kernel, driver, mobile-device, or remote endpoint scanner.",
        "A finding may reflect an OSV ecosystem mapping or version-range match that needs independent validation. The 93 submitted matches must not be interpreted as 93 confirmed exploitable vulnerabilities.",
        "The application currently has a shared optional API token, not individual accounts, roles, or complete tenant isolation. The UI session identifier is not user authentication.",
        "RSS ingestion is on-demand, source-dependent, and limited to recent entries. Feed metadata and summaries may be incomplete.",
        "The current chat endpoint waits for the full Ollama response; token streaming and cancellation are not implemented.",
        "The local runtime was tested; Docker image build, Docker Compose startup, public hosting, and a fresh restore-from-backup exercise remain to be verified.",
    ]),
    para("10.1 Future Enhancements", "Subsection"),
    bullet_list([
        "Add per-user authentication, authorized session ownership, and an analyst review queue for feed and scanner records.",
        "Configure and test MongoDB Atlas Vector Search with a matching index; retain lexical fallback for local development.",
        "Add tests for source ranking and access-control behavior, and run a clean Docker build and Compose deployment in CI.",
        "Add streaming responses, cancel/retry controls, and structured evaluation of answer correctness and citation faithfulness.",
        "Persist scanner provenance and advisory affected-version ranges, deduplicate findings across scans, and define an explicit analyst workflow for false positives.",
        "Implement scheduled backups and document a verified restore procedure before relying on the database for important records.",
    ]),
    para("11. Conclusion", "Section"),
    para(
        "SignalWatch demonstrates a practical MongoDB-backed RAG assistant that brings together course knowledge, "
        "threat records, external leads, host inventory, and persistent chat memory. The implementation is "
        "explicit about the difference between synthetic examples, retrieved course material, unreviewed "
        "advisories, and verified evidence. The local demonstration confirmed end-to-end MongoDB and Ollama "
        "connectivity, source-backed multi-turn chat, threat-record workflows, and filtered scanner findings. "
        "The scanner does not alter the host, and the model is not authorized to perform remediation. "
        "Additional production controls and a separate Docker deployment validation remain necessary.",
    ),
    PageBreak(),
    para("References", "Section"),
])

references = [
    "[1] JAIN (Deemed-to-be University), 23CSE528, Instructions: LLM-based Chat Application on MongoDB, assessment handout supplied with the project.",
    "[2] MongoDB, Inc., MongoDB Manual: CRUD Operations, Indexes, Transactions, Replication, and Security. https://www.mongodb.com/docs/manual/",
    "[3] MongoDB, Inc., Atlas Vector Search documentation. https://www.mongodb.com/docs/atlas/atlas-vector-search/",
    "[4] Ollama, API documentation: chat, model listing, and embeddings. https://github.com/ollama/ollama/blob/main/docs/api.md",
    "[5] Open Source Vulnerability (OSV) project, OSV API documentation. https://google.github.io/osv.dev/api/",
    "[6] FastAPI, official documentation. https://fastapi.tiangolo.com/",
    "[7] P. Lewis et al., Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks, NeurIPS, 2020.",
    "[8] N. Reimers and I. Gurevych, Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks, EMNLP-IJCNLP, 2019.",
    "[9] MITRE, ATT&CK knowledge base. https://attack.mitre.org/",
    "[10] The SignalWatch project source: README.md, app/main.py, app/static/, host_agent/scan_host.py, Dockerfile, and docker-compose.yml; inspected 22 November 2026.",
]
story.append(bullet_list(references))
story.extend([
    Spacer(1, 7 * mm),
    para("Appendix A. Local Demonstration", "Subsection"),
    make_table(
        ["Step", "Demonstration action"],
        [
            ("1", "Start MongoDB and Ollama; confirm the configured chat and embedding models are installed."),
            ("2", "Set MONGO_URI, OLLAMA_BASE_URL, OLLAMA_MODEL, and OLLAMA_EMBED_MODEL for the chosen runtime."),
            ("3", "Start the API and open http://localhost:8000; verify /health and /docs."),
            ("4", "Ask a question about a lab topic, then ask a short follow-up and inspect the returned source references."),
            ("5", "Create, edit, search, and delete a synthetic test threat record."),
            ("6", "Run host_agent/scan_host.py explicitly and review the findings as advisory matches, not proof."),
        ],
        [15 * mm, 157 * mm],
    ),
    Spacer(1, 5 * mm),
    rich(
        "<b>Submission note.</b> The existing project does not provide a GitHub repository URL. Add the actual "
        "private repository link separately if required by the submission portal; this report does not invent one.",
        "CalloutSW",
    ),
])

doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    rightMargin=19 * mm,
    leftMargin=19 * mm,
    topMargin=18 * mm,
    bottomMargin=18 * mm,
    title="SignalWatch Mini Project Report - K J Nikhil Reddy",
    author="K J Nikhil Reddy",
    subject="23CSE528 NoSQL Databases using MongoDB",
)
doc.build(story, onFirstPage=page_chrome, onLaterPages=page_chrome)
print(f"Generated {OUTPUT}")
