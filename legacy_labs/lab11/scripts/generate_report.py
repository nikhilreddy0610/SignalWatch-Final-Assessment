"""Generate the coursework PDF report using ReportLab."""

from __future__ import annotations

from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUTPUT = Path(__file__).resolve().parents[1] / "submission-report.pdf"
NAVY = colors.HexColor("#17233c")
BLUE = colors.HexColor("#2672bd")
PALE_BLUE = colors.HexColor("#edf3fa")
TEXT = colors.HexColor("#172033")


def para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def page_number(canvas, document) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#c5ccda"))
    canvas.line(0.65 * inch, 0.52 * inch, 7.85 * inch, 0.52 * inch)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#526078"))
    canvas.drawString(0.65 * inch, 0.34 * inch, "MongoDB Sharding Labs 11.1 and 11.2")
    canvas.drawRightString(7.85 * inch, 0.34 * inch, f"Page {document.page}")
    canvas.restoreState()


def build_report() -> None:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=23,
            leading=27,
            alignment=TA_CENTER,
            textColor=NAVY,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Subtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#526078"),
            spaceAfter=16,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=7,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Subsection",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=NAVY,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["BodyText"],
            fontSize=8.7,
            leading=12,
            textColor=TEXT,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableCell",
            parent=styles["BodyText"],
            fontSize=7,
            leading=9,
            textColor=TEXT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHead",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=colors.white,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Callout",
            parent=styles["BodyText"],
            fontSize=8.7,
            leading=12,
            textColor=TEXT,
            spaceAfter=0,
        )
    )

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.58 * inch,
        bottomMargin=0.72 * inch,
        title="MongoDB Sharding Labs 11.1 and 11.2",
        author="K J NIKHIL REDDY",
    )
    body = styles["BodySmall"]
    cell = styles["TableCell"]
    story = [
        para("MongoDB Sharding Labs", styles["ReportTitle"]),
        para(
            "Lab 11.1: Evaluate Shard Key Choices | "
            "Lab 11.2: Shard Key Hotspot Detection",
            styles["Subtitle"],
        ),
        para(
            "<b>Student:</b> K J NIKHIL REDDY &nbsp;&nbsp; "
            "<b>USN:</b> 24BTRCL091",
            styles["Subtitle"],
        ),
    ]

    environment = Table(
        [[para(
            "<b>Environment:</b> MongoDB 7.0, Docker Compose, two shard replica "
            "sets, a config-server replica set, and mongos. Single-node replica "
            "sets are used for coursework only; this is not a production topology.",
            styles["Callout"],
        )]],
        colWidths=[7.2 * inch],
    )
    environment.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE),
                ("LINEBEFORE", (0, 0), (0, -1), 4, BLUE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.extend([environment, Spacer(1, 8), para("Lab 11.1 - Shard-key decision matrix", styles["Section"])])

    headers = ("Candidate", "Cardinality", "Distribution", "Query targeting", "Hotspot risk", "Verdict")
    rows = (
        (
            "order_id",
            "Very high, usually unique.",
            "Even for random IDs; potentially skewed for sequential values.",
            "Targets order lookup; customer and date queries scatter.",
            "Depends on generation; increasing IDs can hotspot.",
            "Good if order-ID lookup dominates.",
        ),
        (
            "customer_id",
            "High with many customers.",
            "May skew when a few customers generate many orders.",
            "Targets one customer's order history.",
            "One very active customer remains on one shard.",
            "Good for customer locality; may skew.",
        ),
        (
            "order_date",
            "High over time, but clustered.",
            "New values concentrate in the highest range chunk.",
            "Efficient date ranges; customer queries scatter.",
            "High for inserts on an ascending range key.",
            "Avoid as the sole key for write-heavy orders.",
        ),
        (
            'customer_id: "hashed"',
            "High, inherited from customer IDs.",
            "Generally even across distinct customer values.",
            "Customer equality lookup targets one shard; date ranges scatter.",
            "Low across customers; cannot split one hot customer.",
            "Recommended for customer-centric reads.",
        ),
    )
    table_data = [
        [para(escape(value), styles["TableHead"]) for value in headers],
        *[
            [para(escape(value), cell) for value in row]
            for row in rows
        ],
    ]
    matrix = Table(
        table_data,
        colWidths=[0.78 * inch, 1.02 * inch, 1.25 * inch, 1.35 * inch, 1.15 * inch, 1.15 * inch],
        repeatRows=1,
        hAlign="LEFT",
    )
    matrix.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#c5ccda")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f5f9")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(matrix)
    story.append(Spacer(1, 8))
    story.append(
        para(
            '<b>Recommendation:</b> Among the four candidates, use '
            '<font name="Courier">{customer_id: "hashed"}</font> when customer '
            "order history is the dominant access pattern. It balances distinct "
            "customers while allowing equality lookups to target a shard. Validate "
            "with real workload measurements: hashing does not distribute one "
            "customer's orders, and it sacrifices range locality.",
            body,
        )
    )
    story.append(para("MongoDB 5.0+ resharding overview", styles["Subsection"]))
    story.append(
        para(
            "1. Check version compatibility, cluster health, unique-index rules, globally "
            "unique _id values, collection features, active index builds, and resources.<br/>"
            "2. Disable the balancer and run "
            '<font name="Courier">db.adminCommand({reshardCollection: "shop.orders", '
            'key: {customer_id: "hashed"}})</font> through mongos.<br/>'
            "3. Monitor with $currentOp. Verify data, placement, and application query "
            "plans, then re-enable the balancer.",
            body,
        )
    )
    story.append(
        para(
            "Resharding copies data and catches up concurrent writes. Plan for high "
            "I/O/CPU, temporary storage, increased latency, and a brief write-blocking "
            "critical section. Unique indexes must satisfy shard-key requirements; "
            "duplicate _id values can cause failure, and queryable-encryption "
            "collections are unsupported. Only one collection resharding/move/"
            "unshard/rewrite operation runs at a time. See the "
            '<link href="https://www.mongodb.com/docs/manual/core/sharding-reshard-a-collection/" '
            'color="#155da5">MongoDB Manual: Reshard a Collection</link>.',
            body,
        )
    )

    story.extend(
        [
            PageBreak(),
            para("Lab 11.2 - Hotspot demonstration", styles["Section"]),
            para(
                "The Compose lab inserted 10,000 documents into each collection "
                "on a two-shard MongoDB 7.0 cluster.",
                body,
            ),
        ]
    )
    stats_rows = [
        ("Collection", "Shard key", "Observed per-shard count", "Date-range query plan"),
        ("hotspot_data", "{ts: 1}", "shard2RS: 10,000", "Targets shard2RS (SINGLE_SHARD)."),
        (
            "even_data",
            '{user_id: "hashed"}',
            "shard1RS: 4,970; shard2RS: 5,030",
            "Same date range scatters to both shards (SHARD_MERGE).",
        ),
    ]
    stats = Table(
        [
            [para(escape(value), styles["TableHead"]) for value in stats_rows[0]],
            *[[para(escape(value), cell) for value in row] for row in stats_rows[1:]],
        ],
        colWidths=[1.05 * inch, 1.25 * inch, 2.15 * inch, 2.25 * inch],
        repeatRows=1,
        hAlign="LEFT",
    )
    stats.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#c5ccda")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f5f9")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([stats, Spacer(1, 8)])
    story.append(
        para(
            "An equality query on the hashed user_id targeted one shard. A range "
            "query on that hashed field scattered to both shards. These plans were "
            "verified with explain(); per-shard counts came from collStats.",
            body,
        )
    )
    story.append(
        para(
            "Increasing timestamp values continually target the highest range chunk, "
            "creating a write hotspot even if the collection can later be balanced. "
            "Hashed values distribute distinct keys across chunks, but lose ordered "
            "range locality. A ranged key remains appropriate when range queries are "
            "central and insertion rate or key design avoids a single active "
            "upper-bound chunk.",
            body,
        )
    )
    story.append(para("Docker demonstration and submission", styles["Section"]))
    story.append(
        para(
            "The source builds a local lab-runner image. Start the services, initialize "
            "the cluster, then run both labs with:",
            body,
        )
    )
    story.append(
        para(
            '<font name="Courier">docker compose up -d config shard1 shard2 mongos<br/>'
            "docker compose run --rm initialize<br/>"
            "docker compose --profile tools run --rm lab all</font>",
            body,
        )
    )
    story.append(
        para(
            '<b>Target Docker Hub repository:</b> '
            '<link href="https://hub.docker.com/r/nikhil1386/mongodb-sharding-lab11" '
            'color="#155da5">https://hub.docker.com/r/nikhil1386/mongodb-sharding-lab11</link>',
            body,
        )
    )
    published = Table(
        [[
            para(
                "<b>Publishing status:</b> The image push succeeded. The Docker "
                "Hub tag is <font name=\"Courier\">"
                "nikhil1386/mongodb-sharding-lab11:1.0</font> "
                "(digest <font name=\"Courier\">"
                "sha256:f1ea080d2ddce6c9aa7ea500bddd8b7172dab72e4cee1d3"
                "dae28d4a182dc22ff</font>). The Compose lab service is configured "
                "to use this image.",
                styles["Callout"],
            )
        ]],
        colWidths=[7.2 * inch],
    )
    published.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE),
                ("LINEBEFORE", (0, 0), (0, -1), 4, BLUE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.extend([published, Spacer(1, 8)])
    story.append(
        para(
            "<b>Validation:</b> Python syntax, Docker Compose configuration, image build, "
            "cluster initialization, insertion of 20,000 total documents, per-shard "
            "statistics, and query routing plans all succeeded.",
            body,
        )
    )
    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)


if __name__ == "__main__":
    build_report()
