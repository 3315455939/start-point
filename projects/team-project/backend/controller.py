"""中控脚本（位于 backend）：提供简单的命令行子命令来调用后端模块功能。
用法示例：
  python -m backend.controller weather --city 北京
  python -m backend.controller reminder list
  python -m backend.controller organizer preview
"""
import argparse
import sys

from backend.weather_module import fetch_weather, load_weather_history
from backend.reminder_module import ReminderManager
from backend.organizer_module import preview_desktop_organize, organize_desktop, undo_organize


def cmd_weather(args):
    if args.city:
        data = fetch_weather(args.city)
        print(f"{data.get('name')}, {data.get('sys', {}).get('country')}: {round(data.get('main', {}).get('temp',0))}°C")
    else:
        hist = load_weather_history()
        for r in hist:
            print(f"{r['time']} - {r['city']}: {r['temp']}°C")


def cmd_reminder(args):
    mgr = ReminderManager()
    if args.action == 'list':
        for r in mgr.list_reminders():
            status = '已完成' if r.get('completed') else '待提醒'
            print(f"{r['id']}  {r['time']}  {status}  {r['title']}")
    elif args.action == 'add':
        r = mgr.add_reminder(args.title, args.time, args.content or '')
        print('添加成功:', r['id'])
    elif args.action == 'delete':
        mgr.delete_reminder(args.id)
        print('已删除', args.id)
    elif args.action == 'check':
        triggered = mgr.check_and_notify()
        print('触发提醒:', triggered)


def cmd_organizer(args):
    if args.action == 'preview':
        res = preview_desktop_organize()
        for k, v in res.items():
            print(f"{k} ({len(v)}): {', '.join(v[:10])}{'...' if len(v)>10 else ''}")
    elif args.action == 'start':
        moved = organize_desktop()
        print('已移动文件数:', len(moved))
    elif args.action == 'undo':
        restored = undo_organize()
        print('已恢复文件数:', len(restored))


def main():
    parser = argparse.ArgumentParser(description='桌面工具中控')
    sub = parser.add_subparsers(dest='cmd')

    p_weather = sub.add_parser('weather')
    p_weather.add_argument('--city', help='城市名 (例如 北京)')

    p_rem = sub.add_parser('reminder')
    p_rem.add_argument('action', choices=['list', 'add', 'delete', 'check'])
    p_rem.add_argument('--title')
    p_rem.add_argument('--time')
    p_rem.add_argument('--content')
    p_rem.add_argument('--id')

    p_org = sub.add_parser('organizer')
    p_org.add_argument('action', choices=['preview', 'start', 'undo'])

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)

    if args.cmd == 'weather':
        cmd_weather(args)
    elif args.cmd == 'reminder':
        cmd_reminder(args)
    elif args.cmd == 'organizer':
        cmd_organizer(args)


if __name__ == '__main__':
    main()
