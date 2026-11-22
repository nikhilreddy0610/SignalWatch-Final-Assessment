"""Offline structural checks; does not require a running MongoDB/Ollama/Docker daemon."""
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
for path in [ROOT/'app/main.py',ROOT/'host_agent/scan_host.py']:
    ast.parse(path.read_text())
main=(ROOT/'app/main.py').read_text()
for route in ['/health','/api/threats','/api/scan','/api/findings','/api/chat','/api/feeds/refresh','/api/feeds']:
    assert route in main, f'missing route {route}'
for lab in range(7,19):
    assert (ROOT/'legacy_labs'/f'lab{lab:02d}').exists(), f'missing preserved lab {lab}'
assert (ROOT/'app/static/index.html').exists()
assert 'DEMO ONLY' in main
assert 'ingest_lab_documents' in main and 'last five' in main.lower() or 'limit(5)' in main
print('PASS: Python syntax, core API route declarations, frontend and preserved Labs 7–18 present.')
