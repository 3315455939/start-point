import os
import json
import shutil
import time

try:
    import winshell
except Exception:
    winshell = None

DATA_DIR = os.path.join(os.path.expanduser("~"), ".desktop_tools")
os.makedirs(DATA_DIR, exist_ok=True)

FILE_TYPES = {
    '文档': ['.docx', '.doc', '.pdf', '.txt', '.md', '.ppt', '.xls', '.xlsx', '.csv', '.rtf'],
    '图片': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff'],
    '视频': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm'],
    '音频': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
    '压缩包': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.iso'],
    '程序': ['.exe', '.msi', '.bat', '.cmd', '.ps1', '.lnk'],
    '代码': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.sql', '.json'],
    '其他': []
}

FAVORITES_PATH = os.path.join(DATA_DIR, 'favorite_software.json')

def desktop_path():
    if winshell:
        try:
            return winshell.desktop()
        except:
            pass
    return os.path.join(os.path.expanduser('~'), 'Desktop')

def preview_desktop_organize(favorite_software=None):
    favorite_software = favorite_software or load_favorite_software()
    dp = desktop_path()
    organized = {k: [] for k in FILE_TYPES.keys()}
    for item in os.listdir(dp):
        item_path = os.path.join(dp, item)
        if os.path.isdir(item_path):
            continue
        if any(sw in item for sw in favorite_software):
            continue
        ext = os.path.splitext(item)[1].lower()
        found = False
        for cat, exts in FILE_TYPES.items():
            if ext in exts:
                organized[cat].append(item)
                found = True
                break
        if not found:
            organized['其他'].append(item)
    return organized

def organize_desktop(favorite_software=None):
    favorite_software = favorite_software or load_favorite_software()
    dp = desktop_path()
    all_files = [f for f in os.listdir(dp) if os.path.isfile(os.path.join(dp, f))]
    moved = []
    for folder in FILE_TYPES.keys():
        os.makedirs(os.path.join(dp, folder), exist_ok=True)
    for item in all_files:
        if any(sw in item for sw in favorite_software):
            continue
        ext = os.path.splitext(item)[1].lower()
        target = '其他'
        for cat, exts in FILE_TYPES.items():
            if ext in exts:
                target = cat
                break
        src = os.path.join(dp, item)
        dst = os.path.join(dp, target, item)
        counter = 1
        name, e = os.path.splitext(item)
        while os.path.exists(dst):
            dst = os.path.join(dp, target, f"{name}_{counter}{e}")
            counter += 1
        shutil.move(src, dst)
        moved.append((item, target))
        time.sleep(0.05)
    # save undo info
    undo = {'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'), 'files': moved}
    with open(os.path.join(DATA_DIR, 'last_organize.json'), 'w', encoding='utf-8') as f:
        json.dump(undo, f, ensure_ascii=False, indent=2)
    return moved

def undo_organize():
    path = os.path.join(DATA_DIR, 'last_organize.json')
    if not os.path.exists(path):
        raise FileNotFoundError('没有可撤销的整理记录')
    with open(path, 'r', encoding='utf-8') as f:
        undo = json.load(f)
    dp = desktop_path()
    files = undo.get('files', [])
    restored = []
    for filename, folder in files:
        src = os.path.join(dp, folder, filename)
        dst = os.path.join(dp, filename)
        counter = 1
        name, e = os.path.splitext(filename)
        while os.path.exists(dst):
            dst = os.path.join(dp, f"{name}_{counter}{e}")
            counter += 1
        if os.path.exists(src):
            shutil.move(src, dst)
            restored.append((filename, folder))
    try:
        os.remove(path)
    except:
        pass
    # try remove empty folders
    for folder in FILE_TYPES.keys():
        fp = os.path.join(dp, folder)
        try:
            if os.path.exists(fp) and not os.listdir(fp):
                os.rmdir(fp)
        except:
            pass
    return restored

def load_favorite_software():
    try:
        with open(FAVORITES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return ["微信", "QQ", "Chrome", "Edge", "VSCode"]

def save_favorite_software(list_):
    try:
        with open(FAVORITES_PATH, 'w', encoding='utf-8') as f:
            json.dump(list_, f, ensure_ascii=False, indent=2)
    except:
        pass
