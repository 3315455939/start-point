import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import json
import os
import time
import datetime
import shutil
import threading
import webbrowser

# 模块化后端
from backend.weather_module import fetch_weather as wm_fetch_weather, load_weather_history as wm_load_weather_history
from backend.reminder_module import ReminderManager
from backend.organizer_module import preview_desktop_organize as org_preview, organize_desktop as org_start, undo_organize as org_undo, desktop_path, load_favorite_software, save_favorite_software

# 确保中文显示正常
import locale
try:
    locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
except:
    pass

class DesktopToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("桌面工具插件")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # 初始化数据存储
        self.data_dir = os.path.join(os.path.expanduser("~"), ".desktop_tools")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 初始化提醒定时器
        self.reminder_timer = None
        # 初始化提醒管理器（后端模块）
        self.reminder_manager = ReminderManager()
        
        # 创建主界面
        self.create_main_ui()
        
        # 加载数据（使用后端模块）
        self.load_weather_history()
        self.load_reminders()
        self.load_favorite_software()
        self.load_operation_log()
        
        # 检查提醒
        self.check_reminders()

    def create_main_ui(self):
        # 创建选项卡控件
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 1. 天气查询选项卡
        self.weather_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.weather_frame, text="天气查询")
        self.create_weather_ui()
        
        # 2. 定时提醒选项卡
        self.reminder_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reminder_frame, text="定时提醒")
        self.create_reminder_ui()
        
        # 3. 桌面整理选项卡
        self.desktop_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.desktop_frame, text="桌面整理")
        self.create_desktop_ui()
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_weather_ui(self):
        # 搜索区域
        search_frame = ttk.Frame(self.weather_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(search_frame, text="城市名称:").pack(side=tk.LEFT, padx=5)
        self.city_entry = ttk.Entry(search_frame, width=30)
        self.city_entry.pack(side=tk.LEFT, padx=5)
        self.city_entry.bind("<Return>", lambda e: self.fetch_weather())
        
        ttk.Button(search_frame, text="查询", command=self.fetch_weather).pack(side=tk.LEFT, padx=5)
        
        # 天气结果区域
        result_frame = ttk.LabelFrame(self.weather_frame, text="天气信息")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 主要天气信息
        main_info_frame = ttk.Frame(result_frame)
        main_info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.city_name_var = tk.StringVar(value="未查询")
        self.temp_var = tk.StringVar(value="--°C")
        self.desc_var = tk.StringVar(value="暂无数据")
        
        ttk.Label(main_info_frame, textvariable=self.city_name_var, font=("Arial", 16, "bold")).pack(side=tk.LEFT, padx=10)
        ttk.Label(main_info_frame, textvariable=self.temp_var, font=("Arial", 20, "bold")).pack(side=tk.RIGHT, padx=10)
        ttk.Label(result_frame, textvariable=self.desc_var).pack(padx=10, pady=5)
        
        # 详细信息
        detail_frame = ttk.Frame(result_frame)
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 网格布局显示详细信息
        details = [
            ("湿度", "humidity_var", "--%"),
            ("风速", "wind_var", "-- m/s"),
            ("气压", "pressure_var", "-- hPa"),
            ("体感温度", "feels_like_var", "--°C"),
            ("日出", "sunrise_var", "--:--"),
            ("日落", "sunset_var", "--:--")
        ]
        
        for i, (label, var_name, default) in enumerate(details):
            ttk.Label(detail_frame, text=f"{label}:").grid(row=i//2, column=(i%2)*2, sticky=tk.W, padx=10, pady=5)
            setattr(self, var_name, tk.StringVar(value=default))
            ttk.Label(detail_frame, textvariable=getattr(self, var_name)).grid(row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=5, pady=5)
        
        # 历史记录
        history_frame = ttk.LabelFrame(self.weather_frame, text="查询历史")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.weather_history_listbox = tk.Listbox(history_frame, height=5)
        self.weather_history_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.weather_history_listbox.bind("<Double-Button-1>", self.on_history_select)

    def create_reminder_ui(self):
        # 添加提醒区域
        add_frame = ttk.LabelFrame(self.reminder_frame, text="添加新提醒")
        add_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 标题
        ttk.Label(add_frame, text="标题:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.reminder_title_entry = ttk.Entry(add_frame, width=50)
        self.reminder_title_entry.grid(row=0, column=1, columnspan=3, sticky=tk.EW, padx=10, pady=5)
        
        # 时间
        ttk.Label(add_frame, text="时间:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        # 默认时间：当前时间+30分钟
        default_time = datetime.datetime.now() + datetime.timedelta(minutes=30)
        default_time_str = default_time.strftime("%Y-%m-%d %H:%M")
        
        self.reminder_time_entry = ttk.Entry(add_frame)
        self.reminder_time_entry.insert(0, default_time_str)
        self.reminder_time_entry.grid(row=1, column=1, sticky=tk.EW, padx=10, pady=5)
        ttk.Label(add_frame, text="格式: YYYY-MM-DD HH:MM").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # 内容
        ttk.Label(add_frame, text="内容:").grid(row=2, column=0, sticky=tk.NW, padx=10, pady=5)
        self.reminder_content_text = tk.Text(add_frame, width=50, height=3)
        self.reminder_content_text.grid(row=2, column=1, columnspan=3, sticky=tk.EW, padx=10, pady=5)
        
        # 添加按钮
        ttk.Button(add_frame, text="添加提醒", command=self.add_reminder).grid(row=3, column=3, sticky=tk.E, padx=10, pady=10)
        
        # 提醒列表
        list_frame = ttk.LabelFrame(self.reminder_frame, text="提醒列表")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建树形视图
        columns = ("标题", "时间", "状态")
        self.reminder_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        # 设置列标题
        for col in columns:
            self.reminder_tree.heading(col, text=col)
            self.reminder_tree.column(col, width=200 if col == "标题" else 150)
        
        self.reminder_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 按钮框架
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(btn_frame, text="标记完成", command=self.mark_reminder_completed).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="编辑", command=self.edit_reminder).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除", command=self.delete_reminder).pack(side=tk.LEFT, padx=5)

    def create_desktop_ui(self):
        # 整理控制区域
        control_frame = ttk.LabelFrame(self.desktop_frame, text="桌面整理控制")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="预览整理效果", command=self.preview_desktop_organize).pack(side=tk.LEFT, padx=10, pady=10)
        ttk.Button(control_frame, text="开始整理", command=self.start_desktop_organize).pack(side=tk.LEFT, padx=10, pady=10)
        ttk.Button(control_frame, text="撤销整理", command=self.undo_desktop_organize).pack(side=tk.LEFT, padx=10, pady=10)
        
        # 进度条
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(control_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=10, pady=10)
        
        # 桌面文件预览
        file_frame = ttk.LabelFrame(self.desktop_frame, text="桌面文件")
        file_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.desktop_files_text = tk.Text(file_frame, height=10)
        self.desktop_files_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 常用软件管理
        fav_frame = ttk.LabelFrame(self.desktop_frame, text="常用软件管理")
        fav_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(fav_frame, text="常用软件（不会被整理）:").pack(side=tk.LEFT, padx=10, pady=5)
        self.fav_software_entry = ttk.Entry(fav_frame)
        self.fav_software_entry.pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(fav_frame, text="添加", command=self.add_favorite_software).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 常用软件列表
        self.fav_software_listbox = tk.Listbox(fav_frame, height=3)
        self.fav_software_listbox.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=10, pady=5)
        ttk.Button(fav_frame, text="删除选中", command=self.remove_favorite_software).pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 操作日志
        log_frame = ttk.LabelFrame(self.desktop_frame, text="操作日志")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=5)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 初始加载桌面文件
        self.load_desktop_files()

    # ==================== 天气查询功能 ====================
    def fetch_weather(self):
        city = self.city_entry.get().strip()
        if not city:
            messagebox.showwarning("警告", "请输入城市名称！")
            return
        
        self.status_var.set(f"正在查询 {city} 的天气...")
        try:
            # 使用后端模块获取天气
            data = wm_fetch_weather(city)
            # 解析天气数据并更新界面
            self.city_name_var.set(f"{data.get('name')}, {data.get('sys', {}).get('country')}")
            self.temp_var.set(f"{round(data.get('main', {}).get('temp',0))}°C")
            self.desc_var.set(data.get('weather',[{}])[0].get('description',''))
            self.humidity_var.set(f"{data.get('main',{}).get('humidity','%')}%")
            self.wind_var.set(f"{data.get('wind',{}).get('speed','')} m/s")
            self.pressure_var.set(f"{data.get('main',{}).get('pressure','')} hPa")
            self.feels_like_var.set(f"{round(data.get('main',{}).get('feels_like',0))}°C")
            sunrise = datetime.datetime.fromtimestamp(data.get('sys',{}).get('sunrise',0)) if data.get('sys') else None
            sunset = datetime.datetime.fromtimestamp(data.get('sys',{}).get('sunset',0)) if data.get('sys') else None
            if sunrise:
                self.sunrise_var.set(sunrise.strftime("%H:%M"))
            if sunset:
                self.sunset_var.set(sunset.strftime("%H:%M"))
            self.status_var.set("查询成功")
        except Exception as e:
            messagebox.showerror("错误", f"获取天气失败：{str(e)}")
            self.status_var.set("查询失败")

    def save_weather_history(self, city, data):
        # 已由后端模块处理，不再在 GUI 中重复实现
        pass

    def load_weather_history(self):
        # 从后端模块读取历史
        try:
            self.weather_history = wm_load_weather_history()
        except:
            self.weather_history = []
        self.update_weather_history_list()

    def update_weather_history_list(self):
        """更新历史记录列表"""
        self.weather_history_listbox.delete(0, tk.END)
        for record in self.weather_history:
            self.weather_history_listbox.insert(
                tk.END, 
                f"{record['time']} - {record['city']}: {record['temp']}°C"
            )

    def on_history_select(self, event):
        """选择历史记录"""
        index = self.weather_history_listbox.curselection()
        if index:
            record = self.weather_history[index[0]]
            data = record['data']
            
            # 显示选中的历史记录
            self.city_name_var.set(f"{data['name']}, {data['sys']['country']}")
            self.temp_var.set(f"{round(data['main']['temp'])}°C")
            self.desc_var.set(data['weather'][0]['description'])
            
            self.humidity_var.set(f"{data['main']['humidity']}%")
            self.wind_var.set(f"{data['wind']['speed']} m/s")
            self.pressure_var.set(f"{data['main']['pressure']} hPa")
            self.feels_like_var.set(f"{round(data['main']['feels_like'])}°C")
            
            sunrise = datetime.datetime.fromtimestamp(data['sys']['sunrise'])
            sunset = datetime.datetime.fromtimestamp(data['sys']['sunset'])
            self.sunrise_var.set(sunrise.strftime("%H:%M"))
            self.sunset_var.set(sunset.strftime("%H:%M"))

    # ==================== 定时提醒功能 ====================
    def add_reminder(self):
        """添加新提醒"""
        title = self.reminder_title_entry.get().strip()
        time_str = self.reminder_time_entry.get().strip()
        content = self.reminder_content_text.get("1.0", tk.END).strip()
        
        if not title or not time_str:
            messagebox.showwarning("警告", "标题和时间不能为空！")
            return
        
        try:
            # 解析时间
            reminder_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            
            # 检查时间是否在过去
            now = datetime.datetime.now()
            if reminder_time < now:
                if not messagebox.askyesno("确认", "提醒时间在过去，是否仍然添加？"):
                    return
            
            # 委托给后端管理器
            self.reminder_manager.add_reminder(title, time_str, content)
            self.reminders = self.reminder_manager.reminders
            self.update_reminder_list()
            
            # 清空输入
            self.reminder_title_entry.delete(0, tk.END)
            self.reminder_content_text.delete("1.0", tk.END)
            
            # 设置默认时间（当前+30分钟）
            default_time = datetime.datetime.now() + datetime.timedelta(minutes=30)
            self.reminder_time_entry.delete(0, tk.END)
            self.reminder_time_entry.insert(0, default_time.strftime("%Y-%m-%d %H:%M"))
            
            messagebox.showinfo("成功", "提醒添加成功！")
            
        except ValueError:
            messagebox.showerror("错误", "时间格式错误！请使用 YYYY-MM-DD HH:MM 格式")
        except Exception as e:
            messagebox.showerror("错误", f"添加提醒失败：{str(e)}")

    def load_reminders(self):
        """加载提醒列表"""
        # 使用后端管理器
        try:
            self.reminders = self.reminder_manager.reminders
        except:
            self.reminders = []
        self.update_reminder_list()

    def save_reminders(self):
        """保存提醒列表"""
        # 已由 ReminderManager 处理
        try:
            self.reminder_manager.save_reminders()
        except:
            pass

    def update_reminder_list(self):
        """更新提醒列表界面"""
        # 清空现有内容
        for item in self.reminder_tree.get_children():
            self.reminder_tree.delete(item)
        # 使用后端数据并排序显示
        try:
            sorted_reminders = sorted(
                self.reminder_manager.reminders,
                key=lambda x: datetime.datetime.strptime(x['time'], "%Y-%m-%d %H:%M")
            )
        except Exception:
            sorted_reminders = self.reminder_manager.reminders
        for reminder in sorted_reminders:
            status = "已完成" if reminder.get('completed') else "待提醒"
            self.reminder_tree.insert(
                "", tk.END,
                values=(reminder.get('title'), reminder.get('time'), status),
                iid=reminder.get('id'),
                tags=("completed",) if reminder.get('completed') else ()
            )
        self.reminder_tree.tag_configure("completed", foreground="gray")

    def mark_reminder_completed(self):
        """标记提醒为已完成"""
        selection = self.reminder_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要标记的提醒！")
            return
        
        reminder_id = selection[0]
        # 标记并保存
        for reminder in self.reminder_manager.reminders:
            if reminder.get('id') == reminder_id:
                reminder['completed'] = True
                break
        self.reminder_manager.save_reminders()
        self.update_reminder_list()
        messagebox.showinfo("成功", "标记为已完成！")

    def edit_reminder(self):
        """编辑提醒"""
        selection = self.reminder_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要编辑的提醒！")
            return
        
        reminder_id = selection[0]
        reminder = None
        for r in self.reminder_manager.reminders:
            if r.get('id') == reminder_id:
                reminder = r
                break
        if not reminder:
            return
        # 填充到编辑框
        self.reminder_title_entry.delete(0, tk.END)
        self.reminder_title_entry.insert(0, reminder.get('title',''))
        self.reminder_time_entry.delete(0, tk.END)
        self.reminder_time_entry.insert(0, reminder.get('time',''))
        self.reminder_content_text.delete("1.0", tk.END)
        self.reminder_content_text.insert("1.0", reminder.get('content',''))
        # 删除原提醒
        self.reminder_manager.delete_reminder(reminder_id)
        self.reminders = self.reminder_manager.reminders
        self.update_reminder_list()

    def delete_reminder(self):
        """删除提醒"""
        selection = self.reminder_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的提醒！")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的提醒吗？"):
            reminder_id = selection[0]
            self.reminder_manager.delete_reminder(reminder_id)
            self.reminders = self.reminder_manager.reminders
            self.update_reminder_list()
            messagebox.showinfo("成功", "提醒已删除！")

    def check_reminders(self):
        """检查并触发到期的提醒"""
        # 使用后端管理器进行检查与通知
        try:
            triggered = self.reminder_manager.check_and_notify()
            if triggered:
                self.reminders = self.reminder_manager.reminders
                self.update_reminder_list()
        except Exception as e:
            self.add_log(f"检查提醒失败: {str(e)}")
        # 每分钟检查一次
        self.root.after(60000, self.check_reminders)

    def show_reminder_notification(self, reminder):
        """显示提醒通知"""
        # 后端已经尝试发送系统通知；这里显示弹窗以确保可见性
        try:
            messagebox.showinfo(
                f"提醒: {reminder.get('title')}",
                reminder.get('content', '无内容'),
                parent=self.root
            )
        except:
            pass

    # ==================== 桌面整理功能 ====================
    def load_desktop_files(self):
        """加载桌面文件列表"""
        try:
            # 获取桌面路径（使用 organizer 模块的 desktop_path 回退逻辑）
            dp = desktop_path()
            
            # 清空文本框
            self.desktop_files_text.delete("1.0", tk.END)
            
            # 列出桌面文件
            files = []
            for item in os.listdir(dp):
                item_path = os.path.join(dp, item)
                if os.path.isfile(item_path):
                    # 获取文件大小
                    try:
                        size = os.path.getsize(item_path)
                        size_str = self.format_file_size(size)
                    except:
                        size_str = "未知大小"
                    
                    # 获取修改时间
                    try:
                        mtime = os.path.getmtime(item_path)
                        mtime_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                    except:
                        mtime_str = "未知时间"
                    
                    files.append((item, size_str, mtime_str))
            
            # 显示文件列表
            for filename, size, mtime in sorted(files):
                self.desktop_files_text.insert(tk.END, f"{filename:<40} {size:>10} {mtime:>15}\n")

            self.add_log(f"加载了 {len(files)} 个桌面文件")
            
        except Exception as e:
            self.add_log(f"加载桌面文件失败: {str(e)}")
            messagebox.showerror("错误", f"加载桌面文件失败：{str(e)}")

    def load_favorite_software(self):
        """加载常用软件列表"""
        try:
            with open(os.path.join(self.data_dir, "favorite_software.json"), "r", encoding="utf-8") as f:
                self.favorite_software = json.load(f)
        except:
            # 默认常用软件
            self.favorite_software = ["微信", "QQ", "Chrome", "Edge", "VSCode"]
        
        # 更新列表框
        self.fav_software_listbox.delete(0, tk.END)
        for software in self.favorite_software:
            self.fav_software_listbox.insert(tk.END, software)

    def save_favorite_software(self):
        """保存常用软件列表"""
        with open(os.path.join(self.data_dir, "favorite_software.json"), "w", encoding="utf-8") as f:
            json.dump(self.favorite_software, f, ensure_ascii=False, indent=2)

    def add_favorite_software(self):
        """添加常用软件"""
        software = self.fav_software_entry.get().strip()
        if not software:
            messagebox.showwarning("警告", "请输入软件名称！")
            return
        
        if software not in self.favorite_software:
            self.favorite_software.append(software)
            self.fav_software_listbox.insert(tk.END, software)
            self.save_favorite_software()
            self.fav_software_entry.delete(0, tk.END)
            self.add_log(f"添加常用软件: {software}")
        else:
            messagebox.showinfo("提示", "该软件已在常用列表中！")

    def remove_favorite_software(self):
        """移除选中的常用软件"""
        selection = self.fav_software_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的软件！")
            return
        
        index = selection[0]
        software = self.fav_software_listbox.get(index)
        
        self.favorite_software.remove(software)
        self.fav_software_listbox.delete(index)
        self.save_favorite_software()
        self.add_log(f"移除常用软件: {software}")

    def preview_desktop_organize(self):
        """预览桌面整理效果"""
        self.add_log("开始预览桌面整理效果...")
        try:
            organized = org_preview(self.favorite_software)
            preview_text = "桌面整理预览结果：\n\n"
            for category, files in organized.items():
                if files:
                    preview_text += f"{category} ({len(files)}个文件):\n"
                    preview_text += f"  {', '.join(files[:10])}{'...' if len(files) > 10 else ''}\n\n"
            preview_text += "常用软件（不会移动）：\n"
            preview_text += f"  {', '.join(self.favorite_software)}\n"
            preview_window = tk.Toplevel(self.root)
            preview_window.title("桌面整理预览")
            preview_window.geometry("600x400")
            text_widget = tk.Text(preview_window)
            text_widget.insert(tk.END, preview_text)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            ttk.Button(preview_window, text="关闭", command=preview_window.destroy).pack(pady=10)
            self.add_log("桌面整理预览完成")
        except Exception as e:
            self.add_log(f"预览失败: {str(e)}")
            messagebox.showerror("错误", f"预览失败：{str(e)}")

    def start_desktop_organize(self):
        """开始整理桌面"""
        if not messagebox.askyesno("确认", "确定要整理桌面吗？\n常用软件不会被移动。"):
            return
        # 在新线程中执行，避免界面卡死；调用后端整理函数
        def _runner():
            try:
                self.root.after(0, lambda: self.progress_var.set(0))
                self.root.after(0, lambda: self.status_var.set("开始整理桌面..."))
                self.add_log("开始整理桌面文件...")
                moved = org_start(self.favorite_software)
                self.root.after(0, lambda: self.progress_var.set(100))
                self.root.after(0, lambda: self.status_var.set("桌面整理完成！"))
                self.add_log(f"桌面整理完成，共移动 {len(moved)} 个文件")
                # 保存记录已由模块处理
                self.root.after(0, self.load_desktop_files)
                self.root.after(0, lambda: messagebox.showinfo("完成", f"桌面整理完成！\n共移动 {len(moved)} 个文件到对应文件夹。"))
            except Exception as e:
                self.root.after(0, lambda: self.status_var.set("整理失败！"))
                self.add_log(f"整理失败: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("错误", f"整理失败：{str(e)}"))

        threading.Thread(target=_runner, daemon=True).start()

    def _organize_desktop(self):
        """已模块化：请使用 organizer_module.organize_desktop 或 GUI 的开始整理按钮。"""
        return

    def undo_desktop_organize(self):
        """撤销桌面整理"""
        try:
            if not messagebox.askyesno("确认", "确定要撤销上次的桌面整理吗？"):
                return
            def _runner():
                try:
                    self.root.after(0, lambda: self.progress_var.set(0))
                    self.root.after(0, lambda: self.status_var.set("正在撤销整理..."))
                    self.add_log("开始撤销桌面整理...")
                    restored = org_undo()
                    self.root.after(0, lambda: self.progress_var.set(100))
                    self.root.after(0, lambda: self.status_var.set("撤销完成！"))
                    self.add_log(f"撤销桌面整理完成，共恢复 {len(restored)} 个文件")
                    self.root.after(0, self.load_desktop_files)
                    self.root.after(0, lambda: messagebox.showinfo("完成", "撤销操作完成！\n文件已恢复到整理前的状态。"))
                except Exception as e:
                    self.root.after(0, lambda: self.status_var.set("撤销失败！"))
                    self.add_log(f"撤销失败: {str(e)}")
                    self.root.after(0, lambda: messagebox.showerror("错误", f"撤销失败：{str(e)}"))
            threading.Thread(target=_runner, daemon=True).start()
        except Exception as e:
            messagebox.showerror("错误", f"撤销失败：{str(e)}")

    def _undo_organize(self, undo_data):
        """已模块化：请使用 organizer_module.undo_organize 或 GUI 的撤销按钮。"""
        return

    def add_log(self, message):
        """添加操作日志"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # 添加到日志文本框
        self.root.after(0, lambda: self.log_text.insert(tk.END, log_entry))
        self.root.after(0, lambda: self.log_text.see(tk.END))
        
        # 保存到文件
        try:
            with open(os.path.join(self.data_dir, "operation_log.txt"), "a", encoding="utf-8") as f:
                f.write(log_entry)
        except:
            pass

    def load_operation_log(self):
        """加载操作日志"""
        try:
            with open(os.path.join(self.data_dir, "operation_log.txt"), "r", encoding="utf-8") as f:
                self.log_text.insert(tk.END, f.read())
        except:
            pass

    @staticmethod
    def format_file_size(size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

# ==================== 主程序 ====================
if __name__ == "__main__":
    # 检查依赖
    missing_packages = []
    try:
        import requests
    except ImportError:
        missing_packages.append("requests")
    
    try:
        import winshell
    except ImportError:
        missing_packages.append("winshell")
    
    try:
        from plyer import notification
    except ImportError:
        missing_packages.append("plyer")
    
    # 如果有缺失的包，提示安装
    if missing_packages:
        print("需要安装以下依赖包：")
        for pkg in missing_packages:
            print(f"  pip install {pkg}")
        
        # 如果是Windows系统，winshell可能需要特殊安装
        if "winshell" in missing_packages:
            print("  pip install pywin32 winshell")
        
        input("\n按回车键退出...")
        exit(1)
    
    # 创建并运行应用
    root = tk.Tk()
    app = DesktopToolApp(root)
    
    # 设置样式
    style = ttk.Style(root)
    style.theme_use("clam")
    
    root.mainloop()
