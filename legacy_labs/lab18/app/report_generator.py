from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def generate_pdf_report(results, output_path, chart_path=None, docker_hub_url='https://hub.docker.com/r/nikhil1386/threat-intelligence-lab18'):
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(output), pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph('Lab 18 Threat Intelligence Comparative System', styles['Title']),
        Spacer(1, 6),
        Paragraph('<b>Student Name:</b> K J NIKHIL REDDY', styles['BodyText']),
        Paragraph('<b>USN:</b> 24BTRCL091', styles['BodyText']),
        Paragraph(f'<b>Lab 18 URL:</b> {docker_hub_url}', styles['BodyText']),
        Spacer(1, 12),
        Paragraph('<b>Aim:</b> Compare MongoDB, Cassandra and Neo4j for threat-intelligence workload performance, false-positive analysis and data-model suitability.', styles['BodyText']),
        Paragraph('<b>Objective:</b> Generate synthetic threat data, insert the same records into all three databases, benchmark latency and produce a comparative report.', styles['BodyText']),
        Paragraph('<b>Procedure:</b> Create synthetic dataset, initialize database schemas, insert 100,000 records, run benchmark queries 10 times, collect latency, and export performance charts and PDF output.', styles['BodyText']),
        Paragraph('<b>What We Did:</b> Implemented Python applications for MongoDB, Cassandra and Neo4j, generated realistic synthetic threat data, created schema/index setup and benchmark routines for history, target spread, daily analytics and insert throughput.', styles['BodyText']),
        Paragraph('<b>Output:</b> CSV benchmark results, chart images, architecture diagram and PDF report.', styles['BodyText']),
        Paragraph('<b>Result:</b> The system generated comparative benchmark data with synthetic records labelled as synthetic. Docker image publishing could not be completed in this environment because the Docker daemon/API is unavailable.', styles['BodyText']),
        Spacer(1, 8),
        Paragraph(f'<b>Docker Hub image:</b> {docker_hub_url}', styles['BodyText']),
        Spacer(1, 12),
    ]

    table_data = [['Database', 'Query', 'Run Count', 'Median Latency (ms)']]
    for row in results:
        table_data.append([
            row.get('database', 'N/A'),
            row.get('query', 'N/A'),
            str(row.get('run_count', 0)),
            f"{row.get('median_latency_ms', 0)}",
        ])

    table = Table(table_data, colWidths=[120, 220, 70, 120])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dfeeff')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 18))

    if chart_path:
        try:
            from reportlab.platypus import Image
            story.append(Image(str(chart_path), width=450, height=260))
        except Exception:
            pass

    doc.build(story)
    return str(output)
