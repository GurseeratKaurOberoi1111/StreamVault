import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
source = (ROOT/'backend/app.py').read_text(encoding='utf-8')
assets = {}
for p in sorted((ROOT/'frontend').rglob('*')):
    if p.is_file():
        key = '/' if p.name == 'index.html' else '/' + p.relative_to(ROOT/'frontend').as_posix()
        mime = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.svg':'image/svg+xml'}[p.suffix]
        assets[key] = [mime, p.read_text(encoding='utf-8')]
source += '\nASSETS = ' + repr(assets) + '\nCATALOG = ' + repr(json.loads((ROOT/'backend/catalog.json').read_text(encoding='utf-8'))) + '\nIDS = {t["id"] for t in CATALOG}\n'
base = (ROOT/'infrastructure/base.yaml').read_text(encoding='utf-8')
code = '\n'.join('          '+line if line else '' for line in source.splitlines())
output = base.replace('          # GENERATED_APPLICATION', code)
(ROOT/'template.yaml').write_text(output, encoding='utf-8')
print('Created template.yaml:', len(output.encode()), 'bytes')
if len(output.encode()) > 51200:
    raise SystemExit('Template exceeds the direct request limit. Reduce embedded assets.')
compile(source, 'index.py', 'exec')
