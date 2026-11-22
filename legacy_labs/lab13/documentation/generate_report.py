from datetime import date
from pathlib import Path
import textwrap

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "MongoDB_Lab_13_Final_Report.pdf"
NAVY = colors.HexColor("#15324B")
BLUE = colors.HexColor("#246B8E")
PALE = colors.HexColor("#EAF2F6")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=26, leading=32, textColor=NAVY, alignment=TA_CENTER, spaceAfter=12,
))
styles.add(ParagraphStyle(
    name="CoverSubtitle", parent=styles["Normal"], fontSize=14, leading=21,
    textColor=BLUE, alignment=TA_CENTER, spaceAfter=14,
))
styles.add(ParagraphStyle(
    name="Section", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=17, leading=22, textColor=NAVY, spaceBefore=8, spaceAfter=9,
))
styles.add(ParagraphStyle(
    name="Subsection", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=12, leading=16, textColor=BLUE, spaceBefore=8, spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="BodySmall", parent=styles["BodyText"], fontSize=9.5, leading=14,
    spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="CodeBlock", fontName="Courier", fontSize=7.2, leading=9.2,
    textColor=colors.HexColor("#18212A"), backColor=PALE, borderPadding=7,
    leftIndent=6, rightIndent=6, spaceBefore=4, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="TableCell", parent=styles["BodyText"], fontSize=8.5, leading=11,
))
styles.add(ParagraphStyle(
    name="TableHeader", parent=styles["TableCell"], fontName="Helvetica-Bold",
    textColor=colors.white,
))


def paragraph(text, style="BodySmall"):
    return Paragraph(text, styles[style])


def code(text, width=100):
    lines = text.strip().splitlines() or ["(No output captured.)"]
    wrapped = "\n".join(
        segment
        for line in lines
        for segment in (
            textwrap.wrap(line, width=width, subsequent_indent="    ",
                          break_long_words=True, break_on_hyphens=False) or [""]
        )
    )
    return Preformatted(wrapped, styles["CodeBlock"])


def read_output(name, contains=None, limit=24):
    path = ROOT / "documentation" / name
    if not path.exists():
        return "(Output not captured.)"
    lines = path.read_text(errors="replace").splitlines()
    if name == "dockerhub-push.txt":
        starts = [i for i, line in enumerate(lines) if line.startswith("The push refers to repository")]
        if starts:
            lines = lines[starts[-1]:]
    if contains:
        lines = [line for line in lines if any(token in line for token in contains)]
    return "\n".join(lines[:limit]) or "(No matching output lines.)"


def dockerhub_result():
    path = ROOT / "documentation" / "dockerhub-push.txt"
    if not path.exists():
        return "Push not confirmed; no successful registry result was captured."
    lines = path.read_text(errors="replace").splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith("The push refers to repository")]
    if starts:
        lines = lines[starts[-1]:]
    for line in reversed(lines):
        if "digest:" in line:
            return line
        if "failed commit on ref" in line or "net/http: timeout" in line:
            return "Push failed: Docker Hub timed out while committing an image layer."
    return "Push not yet confirmed; the latest registry attempt had not completed when this report was generated."


def bullet(text):
    return paragraph(f'<font color="{BLUE}">&#8226;</font> {text}')


def table(rows, widths, header=True):
    data = [
        [paragraph(str(cell), "TableHeader" if header and row_index == 0 else "TableCell") for cell in row]
        for row_index, row in enumerate(rows)
    ]
    obj = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C8D5DE")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    if header:
        commands += [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ]
    obj.setStyle(TableStyle(commands))
    return obj


def page_chrome(canvas, doc):
    canvas.saveState()
    width, height = A4
    if doc.page > 1:
        canvas.setStrokeColor(colors.HexColor("#D5E0E7"))
        canvas.line(18 * mm, height - 14 * mm, width - 18 * mm, height - 14 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(NAVY)
        canvas.drawString(18 * mm, height - 11 * mm, "MONGODB LAB 13")
        canvas.setFillColor(colors.HexColor("#637381"))
        canvas.drawRightString(width - 18 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_story():
    story = [
        Spacer(1, 30 * mm),
        paragraph("MONGODB LAB 13", "CoverTitle"),
        HRFlowable(width="45%", thickness=2, color=BLUE, hAlign="CENTER", spaceAfter=12),
        paragraph(
            "DEPLOYMENT OF REPLICA SET USING DOCKER COMPOSE<br/>"
            "AND KUBERNETES STATEFULSET",
            "CoverSubtitle",
        ),
        Spacer(1, 16 * mm),
        table([
            ["Submission details", "Student entry"],
            ["Student name", "K J NIKHIL REDDY"],
            ["USN", "24BTRCL091"],
            ["Subject name", "________________________________"],
            ["Submission date", date.today().strftime("%d %B %Y")],
        ], [55 * mm, 85 * mm]),
        Spacer(1, 18 * mm),
        paragraph("Practical deployment, authentication, persistence, client testing, and failover.", "CoverSubtitle"),
        PageBreak(),

        paragraph("1. Lab Objectives", "Section"),
        bullet("Deploy a three-member MongoDB replica set named <b>rs0</b> with internal keyfile authentication."),
        bullet("Use Docker Compose services, persistent storage, health checks, and automated initialization."),
        bullet("Verify reads and writes with PyMongo and test election of a replacement primary."),
        bullet("Prepare a Kubernetes headless Service, StatefulSet, PVC templates, secure keyfile distribution, and initialization Job."),
        bullet("Build and publish a small Docker image for the PyMongo demonstration client."),
        paragraph("2. Software Prerequisites", "Section"),
        table([
            ["Component", "Used / required"],
            ["Docker Engine and Compose", "Docker 29.8.2; Docker Compose 5.6.0"],
            ["MongoDB", "Official mongo:7.0 image"],
            ["PyMongo demo image", "python:3.12-alpine with PyMongo 4.x"],
            ["Kubernetes", "A cluster, kubectl context, and default StorageClass are required for Lab 13.2 execution."],
            ["YAML validation", "Ruby YAML parser; all three manifest files parsed successfully."],
        ], [48 * mm, 112 * mm]),
        paragraph("3. Lab 13.1 - Docker Compose", "Section"),
        paragraph(
            "Three MongoDB 7.0 containers are attached to a private bridge network. "
            "Each uses an independent named data volume and the same keyfile from a shared "
            "Docker-managed volume. A one-shot initializer waits for MongoDB health checks, "
            "then initiates rs0 with stable member names. Ports are bound to loopback at "
            "27117-27119 to avoid the default ports already occupied on this computer."
        ),
        paragraph("Architecture", "Subsection"),
        table([
            ["Component", "Purpose"],
            ["mongo1 / mongo2 / mongo3", "Replica set members with individual persistent data volumes"],
            ["mongo-keyfile volume", "Shared key material; created once and mounted read-only in each database container"],
            ["keyfile-init", "Creates keyfile in volume and sets mongodb ownership and mode 0400"],
            ["init-replica-set", "Idempotent initialization after all three health checks pass"],
            ["pymongo-test", "Optional test-profile service for insertion/readback and stepdown verification"],
        ], [45 * mm, 115 * mm]),
        paragraph("Keyfile authentication and credentials", "Subsection"),
        paragraph(
            "The local generator creates a random administrator password in a private, ignored "
            ".env file and a separate random keyfile for Kubernetes. Compose generates its "
            "own keyfile inside a named volume, changes its owner to mongodb (UID/GID 999), "
            "and restricts permissions to 0400. Neither file is included in the Docker image "
            "or source-control deliverables. Application credentials are supplied through "
            "environment variables, not hardcoded in scripts."
        ),
        paragraph("Deployment commands", "Subsection"),
        code(
            "./generate-keyfile.sh\n"
            "docker compose up -d\n"
            "docker compose ps\n"
            "docker compose --profile test run --rm pymongo-test\n"
            "docker compose --profile test run --rm pymongo-test python failover-test.py"
        ),
        paragraph("Replica set verification", "Subsection"),
        paragraph(
            "All three Compose containers became healthy and the initializer exited with code 0. "
            "The shared keyfile was confirmed as mongodb:mongodb, mode 400. The initial state "
            "had one PRIMARY and two SECONDARY members. After the deliberate stepdown, the new "
            "primary was mongo2."
        ),
        code(read_output("docker-verification.txt", contains=["mongo", "PRIMARY", "SECONDARY", "mode=400"], limit=20)),
        paragraph("PyMongo connectivity test", "Subsection"),
        paragraph("The test inserted a UUID-keyed document in lab13.verification, read it back, and compared the stored document with the original."),
        code(read_output("pymongo-verification.txt", contains=["PASS:"], limit=5)),
        paragraph("Failover test", "Subsection"),
        paragraph("The test recorded the original primary, issued replSetStepDown with force enabled, and waited for hello to identify a different writable primary. The test only reports success after observing that change."),
        code(read_output("failover-verification.txt", contains=["Current primary:", "PASS:"], limit=5)),
        PageBreak(),

        paragraph("4. Lab 13.2 - Kubernetes StatefulSet", "Section"),
        paragraph(
            "The Kubernetes deliverable contains a headless Service, a three-replica "
            "StatefulSet with stable pod DNS identities, and a ConfigMap/Job pair to initialize "
            "rs0. Each pod receives its own 5 GiB ReadWriteOnce PVC through volumeClaimTemplates. "
            "A root init container copies the Kubernetes Secret keyfile into a memory-backed "
            "emptyDir, changes ownership to UID/GID 999, and sets mode 0400 before mongod starts "
            "as a non-root user. Readiness and liveness probes authenticate with the Kubernetes "
            "mongo-auth Secret."
        ),
        paragraph("Kubernetes files", "Subsection"),
        table([
            ["File", "Purpose"],
            ["mongo-headless-svc.yaml", "Headless Service publishes stable StatefulSet member identities."],
            ["mongo-statefulset.yaml", "Three MongoDB replicas, probes, security context, keyfile init container, and PVC template."],
            ["mongo-init.yaml", "ConfigMap with replica-set initialization logic and a retrying initialization Job."],
        ], [55 * mm, 105 * mm]),
        paragraph("Execution status", "Subsection"),
        paragraph(
            "<b>Manifest syntax validated.</b> Docker Desktop reports Kubernetes disabled and "
            "stopped; kubectl has no current cluster context. Therefore no StatefulSet or pods "
            "were applied, and pod readiness/deletion recovery were not tested. To execute, "
            "enable a cluster, create the mongo-keyfile and mongo-auth Secrets as documented in "
            "Lab-13.2-Kubernetes/README.md, apply the manifests, wait for the Job, then delete "
            "mongo-1 and confirm it returns Ready and SECONDARY. These are explicit remaining "
            "manual checks, not reported as successes."
        ),
        code(
            "kubectl -n mongo-lab rollout status statefulset/mongo --timeout=10m\n"
            "kubectl -n mongo-lab wait --for=condition=complete job/mongo-init-rs --timeout=5m\n"
            "kubectl -n mongo-lab get pods,pvc\n"
            "kubectl -n mongo-lab delete pod mongo-1\n"
            "kubectl -n mongo-lab wait --for=condition=Ready pod/mongo-1 --timeout=5m"
        ),
        paragraph("5. Docker and Kubernetes Comparison", "Section"),
        table([
            ["Topic", "Docker Compose", "Kubernetes StatefulSet"],
            ["Identity", "Service names on one Compose network", "Stable pod names and headless DNS"],
            ["Storage", "Named volumes per member", "PVC per ordinal pod"],
            ["Scheduling", "Single Docker host", "Cluster scheduler and controller reconciliation"],
            ["Recovery", "Compose restart behavior", "StatefulSet recreates pods and reattaches claims"],
            ["This lab result", "Executed and verified, including actual failover", "Manifests validated; cluster unavailable for runtime verification"],
        ], [32 * mm, 63 * mm, 65 * mm]),
        paragraph("6. Docker Hub Image", "Section"),
        paragraph(
            "The public image packages the PyMongo verification/failover client, its dependencies, "
            "and the project documentation, Compose configuration, Kubernetes manifests, and report "
            "under /lab/project. It does not contain MongoDB credentials, the generated .env, or "
            "private key material."
        ),
        paragraph("Image build and runtime check", "Subsection"),
        code(read_output("image-build-verification.txt", limit=5)),
        paragraph(
            f'Docker Hub repository: <link href="https://hub.docker.com/r/nikhil1386/mongodb-lab13-demo" '
            f'color="#246B8E">https://hub.docker.com/r/nikhil1386/mongodb-lab13-demo</link>'
        ),
        paragraph("Publication result", "Subsection"),
        code(dockerhub_result()),
        paragraph("7. Results and Conclusion", "Section"),
        paragraph(
            "The Docker Compose lab ran successfully with authenticated, persistent MongoDB "
            "members. The replica set produced one primary and two secondaries; a real PyMongo "
            "write/read test passed; and a forced primary stepdown elected a different primary. "
            "The Kubernetes design and manifests are prepared and syntax-validated, but runtime "
            "verification awaits an enabled Kubernetes cluster. The demonstration image build "
            "and Docker Hub result are recorded above. Terminal evidence is saved under "
            "documentation/. No screenshots were fabricated; no application screenshots were "
            "available from this terminal-only execution."
        ),
        paragraph("Reference Materials", "Subsection"),
        paragraph(
            '<link href="https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/blob/main/chapter-13/docker-compose-production.yml" color="#246B8E">Professor Docker Compose production configuration</link><br/>'
            '<link href="https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/blob/main/chapter-13/main.tf" color="#246B8E">Professor Terraform Atlas configuration</link><br/>'
            '<link href="https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-13" color="#246B8E">Complete Chapter 13 materials</link>'
        ),
    ]
    return story


doc = SimpleDocTemplate(
    str(OUTPUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
    topMargin=20 * mm, bottomMargin=18 * mm,
    title="MongoDB Lab 13 - Replica Set Deployment",
    author="Student",
    subject="Docker Compose and Kubernetes StatefulSet",
)
doc.build(build_story(), onFirstPage=page_chrome, onLaterPages=page_chrome)
print(f"Created {OUTPUT}")
