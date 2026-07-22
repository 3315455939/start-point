import importlib, inspect, pathlib, sys
print('cwd:', pathlib.Path.cwd())
# Import organizer_module
try:
    m = importlib.import_module('backend.organizer_module')
    names = [n for n in dir(m) if not n.startswith('_')]
    print('backend.organizer_module symbols:', names)
    preview_candidates = ['preview_desktop_organize','preview_organize','simulate_organize','preview']
    called = False
    for name in preview_candidates:
        if hasattr(m, name):
            func = getattr(m, name)
            sig = inspect.signature(func)
            print(f'Found {name} with signature {sig}')
            try:
                if len(sig.parameters) == 0:
                    print('Calling', name)
                    res = func()
                    print('Call returned:', res)
                else:
                    print('Skipping call due to parameters:', list(sig.parameters.keys()))
                called = True
            except Exception as e:
                print('Calling', name, 'raised', repr(e))
            break
    if not called:
        print('No preview candidate found or none called.')
except Exception as e:
    print('Importing backend.organizer_module failed:', repr(e))

# Check frontend GUI guard
gui_path = pathlib.Path('frontend') / 'desktop_tool_gui.py'
if gui_path.exists():
    text = gui_path.read_text(encoding='utf-8')
    has_guard = 'if __name__ == "__main__"' in text or "if __name__ == '__main__'" in text
    print('frontend/desktop_tool_gui.py exists:', gui_path)
    print('Has __main__ guard:', has_guard)
    # Print a short snippet around guard if present
    if has_guard:
        idx = text.find('__main__')
        start = max(0, idx-80)
        end = min(len(text), idx+80)
        print('Snippet:', text[start:end].replace('\n','\\n'))
else:
    print('frontend/desktop_tool_gui.py not found')

print('done')
