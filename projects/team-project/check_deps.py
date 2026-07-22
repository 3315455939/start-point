import importlib, pathlib, sys
req = pathlib.Path('requirements.txt')
missing = []
installed = []
if not req.exists():
    print('requirements.txt not found')
    sys.exit(2)
for line in req.read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    pkg = line.split()[0]
    # strip version specifiers
    for sep in ('==','>=','<=','>','<','~='):
        if sep in pkg:
            pkg = pkg.split(sep)[0]
    name = pkg.replace('-', '_')
    try:
        importlib.import_module(name)
        installed.append(name)
    except Exception as e:
        missing.append((name, repr(e)))
print('installed:', installed)
print('missing:', missing)
