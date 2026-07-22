import os
import json
import time
import datetime
try:
    from plyer import notification
except Exception:
    notification = None

DATA_DIR = os.path.join(os.path.expanduser("~"), ".desktop_tools")
os.makedirs(DATA_DIR, exist_ok=True)

def reminders_path():
    return os.path.join(DATA_DIR, "reminders.json")

class ReminderManager:
    def __init__(self):
        self.reminders = self.load_reminders()

    def load_reminders(self):
        try:
            with open(reminders_path(), 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def save_reminders(self):
        with open(reminders_path(), 'w', encoding='utf-8') as f:
            json.dump(self.reminders, f, ensure_ascii=False, indent=2)

    def add_reminder(self, title, time_str, content=''):
        reminder = {
            'id': str(int(time.time() * 1000)),
            'title': title,
            'time': time_str,
            'content': content,
            'completed': False,
            'created': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.reminders.append(reminder)
        self.save_reminders()
        return reminder

    def delete_reminder(self, reminder_id):
        self.reminders = [r for r in self.reminders if r.get('id') != reminder_id]
        self.save_reminders()

    def list_reminders(self):
        return sorted(self.reminders, key=lambda x: x.get('time'))

    def check_and_notify(self):
        now = datetime.datetime.now()
        triggered = []
        for r in self.reminders:
            if r.get('completed'):
                continue
            try:
                rt = datetime.datetime.strptime(r['time'], "%Y-%m-%d %H:%M")
                delta = abs((rt - now).total_seconds())
                if delta <= 60:
                    # send notification
                    try:
                        if notification:
                            notification.notify(title=r['title'], message=r.get('content',''), timeout=10)
                    except:
                        pass
                    triggered.append(r['id'])
            except:
                continue
        for r in self.reminders:
            if r['id'] in triggered:
                r['completed'] = True
        if triggered:
            self.save_reminders()
        return triggered
