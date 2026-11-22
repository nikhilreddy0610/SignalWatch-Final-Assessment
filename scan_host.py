"""Explicit, read-only host inventory scanner. Does not install, remove or modify software."""
import json, os, platform, socket, subprocess, sys, urllib.request, hashlib
from datetime import datetime, timezone
import requests
API=os.getenv('SIGNALWATCH_API','http://localhost:8000').rstrip('/')
TOKEN=os.getenv('SIGNALWATCH_API_KEY','')

def run(cmd):
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
        return p.stdout.strip() if p.returncode==0 else ''
    except Exception: return ''

def inventory():
    system=platform.system().lower(); packages=[]; findings=[]
    if system=='darwin':
        raw=run(['brew','list','--versions'])
        for line in raw.splitlines():
            bits=line.split();
            if len(bits)>1: packages.append({'name':bits[0],'version':' '.join(bits[1:]),'manager':'homebrew'})
        outdated=run(['brew','outdated','--json=v2'])
        if outdated:
            try:
                for p in json.loads(outdated).get('formulae',[]): findings.append({'title':f"Outdated package: {p.get('name')}",'package':p.get('name'),'installed_version':p.get('installed_versions'),'severity':'unknown','recommendation':'Review Homebrew changelog and update policy; no automatic update was performed.'})
            except Exception: pass
    elif system=='linux':
        raw=run(['dpkg-query','-W','-f=${Package}\t${Version}\n'])
        for line in raw.splitlines():
            bits=line.split('\t')
            if len(bits)==2: packages.append({'name':bits[0],'version':bits[1],'manager':'dpkg'})
        updates=run(['bash','-lc','apt list --upgradable 2>/dev/null'])
        for line in updates.splitlines()[1:]:
            name=line.split('/')[0]
            if name: findings.append({'title':f'Package update available: {name}','package':name,'severity':'unknown','recommendation':'Review the vendor security advisory and maintenance window before updating.'})
    elif system=='windows':
        raw=run(['powershell','-NoProfile','-Command','Get-Package | Select-Object Name,Version | ConvertTo-Json -Compress'])
        if raw:
            try:
                data=json.loads(raw); data=data if isinstance(data,list) else [data]
                packages=[{'name':x.get('Name'),'version':x.get('Version'),'manager':'windows-package'} for x in data]
            except Exception: pass
        outdated=run(['winget','upgrade','--output','json'])
        if outdated:
            try:
                for p in json.loads(outdated).get('Data',[]): findings.append({'title':'Package update available','package':p.get('PackageIdentifier'),'severity':'unknown','recommendation':'Check publisher advisory and validate applicability before updating.'})
            except Exception: pass
    # Ask OSV for exact package+version matches where the ecosystem is known.
    ecosystem={'darwin':'Homebrew','linux':'Debian'} .get(system)
    if ecosystem and packages:
        queries=[]
        for pkg in packages[:500]:
            if pkg.get('name') and pkg.get('version'):
                queries.append({'package':{'name':pkg['name'],'ecosystem':ecosystem},'version':str(pkg['version']).split()[0]})
        if queries:
            try:
                response=requests.post('https://api.osv.dev/v1/querybatch',json={'queries':queries},timeout=60)
                response.raise_for_status()
                osv=response.json()
                for pkg,result in zip(packages,osv.get('results',[])):
                    for vuln in result.get('vulns',[]):
                        refs=vuln.get('references',[])
                        findings.append({'title':vuln.get('summary') or vuln.get('id'),'package':pkg.get('name'),'installed_version':pkg.get('version'),'cve':vuln.get('id'),'severity':'see_advisory','source_url':refs[0].get('url') if refs else 'https://osv.dev/','recommendation':'Verify the affected-version range and vendor fix before taking action. This is an advisory match, not proof of exploitation.'})
            except Exception as exc: print('OSV lookup skipped:',exc,file=sys.stderr)
    # Python packages are also queried through PyPI OSV ecosystem on all platforms.
    pyraw=run([sys.executable,'-m','pip','list','--format=json'])
    try:
        py_pkgs=json.loads(pyraw) if pyraw else []
        queries=[{'package':{'name':x['name'],'ecosystem':'PyPI'},'version':x['version']} for x in py_pkgs if x.get('name') and x.get('version')][:500]
        if queries:
            response=requests.post('https://api.osv.dev/v1/querybatch',json={'queries':queries},timeout=60)
            response.raise_for_status()
            osv=response.json()
            for pkg,result in zip(py_pkgs,osv.get('results',[])):
                for vuln in result.get('vulns',[]):
                    refs=vuln.get('references',[])
                    findings.append({'title':vuln.get('summary') or vuln.get('id'),'package':pkg.get('name'),'installed_version':pkg.get('version'),'cve':vuln.get('id'),'severity':'see_advisory','source_url':refs[0].get('url') if refs else 'https://osv.dev/','recommendation':'Verify affected-version range and vendor guidance before changing this package.'})
    except Exception as exc: print('PyPI OSV lookup skipped:',exc,file=sys.stderr)
    return {'hostname':socket.gethostname(),'platform':{'darwin':'macOS','linux':'Linux','windows':'Windows'}.get(system,platform.system()),'platform_version':platform.version(),'packages':packages,'findings':findings,'scanned_at':datetime.now(timezone.utc).isoformat()}

def main():
    data=inventory(); req=urllib.request.Request(API+'/api/scan',data=json.dumps(data).encode(),headers={'Content-Type':'application/json',**({'X-API-Key':TOKEN} if TOKEN else {})},method='POST')
    with urllib.request.urlopen(req,timeout=30) as r: print(r.read().decode())
    print(f"Inventory sent: {len(data['packages'])} packages; {len(data['findings'])} update signals. Read-only scan; no changes made.")
if __name__=='__main__': main()
