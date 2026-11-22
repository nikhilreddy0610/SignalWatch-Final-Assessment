from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


OUTPUT = "Lab_12_MongoDB_Security_Submission.pdf"
DOCKER_URL = "https://hub.docker.com/r/nikhil1386/mongodb-security-labs"


def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=A4,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="MongoDB Security Labs 12.1 and 12.2",
        author="K J Nikhil Reddy",
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleCenter",
            parent=styles["Title"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1F4E78"),
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading1"],
            textColor=colors.HexColor("#1F4E78"),
            spaceBefore=8,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["BodyText"],
            fontSize=8.5,
            leading=11,
        )
    )

    story = []
    story.append(Paragraph("MongoDB Security Labs", styles["TitleCenter"]))
    story.append(
        Paragraph(
            "Lab 12.1: Authentication and RBAC &nbsp;&nbsp; | &nbsp;&nbsp; "
            "Lab 12.2: TLS Encryption-in-Transit",
            styles["Heading2"],
        )
    )
    story.append(Spacer(1, 10))

    identity = [
        [Paragraph("<b>Name</b>", styles["Small"]), "K J NIKHIL REDDY"],
        [Paragraph("<b>USN</b>", styles["Small"]), "24BTRCL091"],
        [Paragraph("<b>Submission</b>", styles["Small"]), "Docker-based demonstration"],
    ]
    identity_table = Table(identity, colWidths=[1.25 * inch, 5.25 * inch])
    identity_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#1F4E78")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#A6A6A6")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#D9EAF7")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(identity_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Docker Hub Submission", styles["Section"]))
    story.append(
        Paragraph(
            f'<link href="{DOCKER_URL}" color="#0563C1"><u>{DOCKER_URL}</u></link>',
            styles["BodyText"],
        )
    )
    story.append(Spacer(1, 8))

    story.append(Paragraph("Lab 12.1: Authentication and RBAC", styles["Section"]))
    story.append(
        Paragraph(
            "The container starts MongoDB with authentication enabled and "
            "<b>--tlsMode requireTLS</b>. A lab administrator owns setup, while "
            "three least-privilege application identities are created:",
            styles["BodyText"],
        )
    )

    rbac_rows = [
        [Paragraph("<b>User</b>", styles["Small"]), Paragraph("<b>Permission</b>", styles["Small"])],
        ["app_user_read", "Find public_data and the employees_safe view"],
        ["app_user_write", "Find, insert, update, and delete on orders only"],
        ["hr_user", "Find on the underlying employees collection"],
        ["lab_admin", "Administration and lab setup"],
    ]
    rbac_table = Table(rbac_rows, colWidths=[1.8 * inch, 4.7 * inch], repeatRows=1)
    rbac_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#A6A6A6")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F6FA")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(rbac_table)
    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "<b>Field-level redaction:</b> the <font name='Courier'>employees_safe</font> "
            "view preserves username, email, and role. It masks SSNs as "
            "<font name='Courier'>***-**-NNNN</font> and removes salary. The read-only "
            "application user cannot query the underlying employees collection; the "
            "HR user can.",
            styles["BodyText"],
        )
    )

    story.append(Paragraph("Lab 12.2: TLS Encryption-in-Transit", styles["Section"]))
    story.append(
        Paragraph(
            "The entrypoint creates a lab certificate authority, a server certificate "
            "for MongoDB, and a client certificate for mongosh and PyMongo. MongoDB "
            "uses a combined server key/certificate PEM and a CA certificate. The "
            "server certificate contains DNS names for localhost and mongo plus "
            "127.0.0.1 as an IP subject alternative name.",
            styles["BodyText"],
        )
    )

    story.append(Paragraph("Certificate Chain", styles["Section"]))
    story.append(
        Paragraph(
            "<b>MongoDB-Lab-CA</b> (ca.crt)<br/>"
            "&nbsp;&nbsp;├── Server certificate (server.crt + server.key = mongodb.pem)<br/>"
            "&nbsp;&nbsp;└── Client certificate (client.crt + client.key = client.pem)",
            styles["BodyText"],
        )
    )

    story.append(PageBreak())
    story.append(Paragraph("Build and Demonstration Steps", styles["Section"]))
    story.append(
        Paragraph(
            "<b>1. Start the demonstration:</b><br/>"
            "<font name='Courier'>docker compose up --build -d</font>",
            styles["BodyText"],
        )
    )
    story.append(
        Paragraph(
            "<b>2. Verify RBAC and redaction:</b><br/>"
            "<font name='Courier'>docker compose exec mongo /opt/lab/verify-rbac.sh</font>",
            styles["BodyText"],
        )
    )
    story.append(
        Paragraph(
            "<b>3. Verify TLS and reject plaintext:</b><br/>"
            "<font name='Courier'>docker compose --profile verify run --rm tls-check</font>",
            styles["BodyText"],
        )
    )
    story.append(
        Paragraph(
            "<b>4. Stop the demonstration:</b><br/>"
            "<font name='Courier'>docker compose down</font>",
            styles["BodyText"],
        )
    )

    story.append(Paragraph("Verified Results", styles["Section"]))
    verification = [
        ["Check", "Observed result"],
        ["Reader read permissions", "PASS - public data and redacted view accessible"],
        ["Reader denial checks", "PASS - orders and writes denied"],
        ["Writer scope", "PASS - orders permitted; outside collections denied"],
        ["HR access", "PASS - underlying employees collection exposes salary"],
        ["PyMongo over TLS", "PASS - authenticated read succeeded"],
        ["Plaintext connection", "PASS - connection was rejected"],
        ["Docker health", "PASS - MongoDB container reported healthy"],
    ]
    verification_table = Table(
        [[Paragraph(f"<b>{c}</b>", styles["Small"]) if r == 0 else c for c in row]
         for r, row in enumerate(verification)],
        colWidths=[2.15 * inch, 4.35 * inch],
        repeatRows=1,
    )
    verification_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#A6A6A6")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F6FA")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(verification_table)

    story.append(Spacer(1, 12))
    story.append(Paragraph("Security Notes", styles["Section"]))
    story.append(
        Paragraph(
            "The classroom certificates are self-signed and stored only in a Docker "
            "volume. Private keys are not copied into the application image and must "
            "not be committed to source control. Production deployments should use "
            "certificates issued by a trusted internal or public certificate authority.",
            styles["BodyText"],
        )
    )

    doc.build(story)


if __name__ == "__main__":
    build_pdf()
