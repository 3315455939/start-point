import json
import tempfile
import pathlib
import shutil
from backend import organizer_module as m

out = 'backups/preview_result.json'
tmp = pathlib.Path('backups') / 'preview_tmp_desktop'
try:
    # create a small temporary desktop folder with sample files
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / 'example.txt').write_text('hello')
    (tmp / 'photo.jpg').write_text('binary')

    # monkeypatch desktop_path to point to our tmp folder
    original_desktop_path = getattr(m, 'desktop_path', None)
    m.desktop_path = lambda: str(tmp)

    # call preview (safe: will not move files)
    res = m.preview_desktop_organize(None)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print('WROTE', out)
finally:
    # restore and cleanup
    if original_desktop_path is not None:
        m.desktop_path = original_desktop_path
    try:
        shutil.rmtree(tmp)
    except Exception:
        pass
