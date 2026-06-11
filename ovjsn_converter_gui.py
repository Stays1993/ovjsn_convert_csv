import json
import csv
import re
import os
import threading
import subprocess
import platform
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# 尝试导入拖拽支持
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    from tkinter import Tk as TkinterDnD

# ================== 辅助函数 ==================
def get_desktop_path():
    """获取桌面路径，如果不存在则返回用户目录"""
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.exists(desktop):
        desktop = os.path.expanduser("~")
    return desktop

def get_default_output_dir():
    """默认输出目录：桌面/OVJSN_Output"""
    return os.path.join(get_desktop_path(), "OVJSN_Output")

# ================== 核心转换逻辑 ==================
def parse_comment(comment):
    """解析Comment字符串，返回设备名到数量的字典"""
    if not comment:
        return {}
    lines = comment.split('\r\n')
    devices = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = re.match(r'([^×x]+)[×x](\d+)', line)
        if match:
            name = match.group(1).strip()
            count = int(match.group(2))
            devices[name] = count
        else:
            devices[line] = 1
    return devices

def convert_ovjsn_to_csv(input_path, output_dir, add_timestamp):
    """转换单个ovjsn文件，返回 (成功标志, 消息)"""
    try:
        with open(input_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
    except Exception as e:
        return False, f"读取文件失败: {e}"

    obj_items = data.get('ObjItems', [])
    if not obj_items:
        return False, "未找到 ObjItems"

    first_item = obj_items[0]
    folder_obj = first_item.get('Object', {})
    original_name = folder_obj.get('Name', 'output')
    original_name = original_name.replace('/', '_').replace('\\', '_')
    if add_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"{timestamp}_{original_name}.csv"
    else:
        csv_filename = f"{original_name}.csv"
    full_output_path = os.path.join(output_dir, csv_filename)

    obj_detail = folder_obj.get('ObjectDetail', {})
    children = obj_detail.get('ObjChildren', [])

    all_devices = set()
    rows_data = []
    for child in children:
        child_obj = child.get('Object', {})
        name = child_obj.get('Name', '')
        comment = child_obj.get('Comment', '')
        devices = parse_comment(comment)
        rows_data.append({'Name': name, 'devices': devices})
        all_devices.update(devices.keys())

    sorted_devices = sorted(all_devices)

    try:
        with open(full_output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Name'] + sorted_devices)
            for row in rows_data:
                row_list = [row['Name']]
                for dev in sorted_devices:
                    count = row['devices'].get(dev, '')
                    row_list.append(count if count != '' else '')
                writer.writerow(row_list)
        return True, f"成功: {os.path.basename(input_path)} -> {csv_filename} ({len(rows_data)} 条记录)"
    except Exception as e:
        return False, f"写入CSV失败: {e}"

def batch_convert(file_list, output_dir, add_timestamp, log_callback):
    """批量转换，在子线程中运行，通过回调更新日志"""
    if not file_list:
        log_callback("没有文件需要转换。")
        return
    total = len(file_list)
    log_callback(f"开始转换 {total} 个文件，输出目录: {output_dir}")
    success_count = 0
    for idx, file_path in enumerate(file_list, 1):
        log_callback(f"[{idx}/{total}] 处理: {os.path.basename(file_path)}")
        ok, msg = convert_ovjsn_to_csv(file_path, output_dir, add_timestamp)
        log_callback(f"  {msg}")
        if ok:
            success_count += 1
    log_callback(f"转换完成！成功: {success_count}, 失败: {total - success_count}")

# ================== GUI 界面 ==================
class OvjsnConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("奥维地图 OVJSN 转 CSV 工具")
        self.root.geometry("700x520")
        self.root.resizable(True, True)

        # 变量：默认输出目录为桌面/OVJSN_Output
        default_output = get_default_output_dir()
        self.output_dir = tk.StringVar(value=default_output)
        self.add_timestamp = tk.BooleanVar(value=True)

        # 创建控件
        self.create_widgets()

        # 设置拖拽（如果可用）
        if DND_AVAILABLE:
            self.setup_drag_drop()

    def create_widgets(self):
        # 输出目录设置
        frame_output = tk.Frame(self.root)
        frame_output.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frame_output, text="输出目录:").pack(side=tk.LEFT)
        tk.Entry(frame_output, textvariable=self.output_dir, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_output, text="浏览", command=self.select_output_dir).pack(side=tk.LEFT, padx=2)
        tk.Button(frame_output, text="打开输出目录", command=self.open_output_dir).pack(side=tk.LEFT, padx=2)

        # 时间戳选项
        frame_timestamp = tk.Frame(self.root)
        frame_timestamp.pack(fill=tk.X, padx=10, pady=5)
        tk.Checkbutton(frame_timestamp, text="在输出文件名前添加时间戳", variable=self.add_timestamp).pack(side=tk.LEFT)

        # 转换方式按钮组
        frame_buttons = tk.Frame(self.root)
        frame_buttons.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(frame_buttons, text="选择文件", command=self.select_files, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_buttons, text="选择目录", command=self.select_directory, width=12).pack(side=tk.LEFT, padx=5)

        # 拖拽提示
        self.drag_label = tk.Label(self.root, text="拖拽 .ovjsn 文件到此处（支持多文件）",
                                   bg="lightgray", relief=tk.RAISED, height=3)
        self.drag_label.pack(fill=tk.X, padx=10, pady=5)
        if not DND_AVAILABLE:
            self.drag_label.config(text="拖拽功能未启用（未安装 tkinterdnd2），请使用按钮选择。")

        # 日志显示区域
        frame_log = tk.Frame(self.root)
        frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tk.Label(frame_log, text="转换日志:").pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(frame_log, wrap=tk.WORD, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def setup_drag_drop(self):
        self.drag_label.drop_target_register(DND_FILES)
        self.drag_label.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        files_raw = event.data
        file_paths = []
        for item in files_raw.split():
            item = item.strip('{}')
            if os.path.isfile(item) and item.lower().endswith('.ovjsn'):
                file_paths.append(item)
        if file_paths:
            self.start_conversion(file_paths)
        else:
            self.log("未检测到有效的 .ovjsn 文件。")

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="选择 OVJSN 文件",
            filetypes=[("奥维地图文件", "*.ovjsn"), ("所有文件", "*.*")]
        )
        if files:
            self.start_conversion(list(files))

    def select_directory(self):
        dir_path = filedialog.askdirectory(title="选择包含 OVJSN 文件的目录")
        if not dir_path:
            return
        files = []
        for root, dirs, filenames in os.walk(dir_path):
            for f in filenames:
                if f.lower().endswith('.ovjsn'):
                    files.append(os.path.join(root, f))
        if files:
            self.start_conversion(files)
        else:
            self.log(f"目录 {dir_path} 下未找到任何 .ovjsn 文件。")

    def select_output_dir(self):
        dir_path = filedialog.askdirectory(title="选择输出目录")
        if dir_path:
            self.output_dir.set(dir_path)

    def open_output_dir(self):
        """打开当前设置的输出目录"""
        target_dir = self.output_dir.get().strip()
        if not target_dir:
            self.log("输出目录未设置。")
            return
        if not os.path.exists(target_dir):
            self.log(f"输出目录不存在，正在创建: {target_dir}")
            try:
                os.makedirs(target_dir, exist_ok=True)
            except Exception as e:
                self.log(f"创建目录失败: {e}")
                return
        try:
            if platform.system() == "Windows":
                os.startfile(target_dir)
            elif platform.system() == "Darwin":
                subprocess.run(["open", target_dir])
            else:
                subprocess.run(["xdg-open", target_dir])
        except Exception as e:
            self.log(f"打开目录失败: {e}")

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def start_conversion(self, file_list):
        output_dir = self.output_dir.get().strip()
        if not output_dir:
            self.log("错误：输出目录不能为空。")
            return
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            self.log(f"创建输出目录失败: {e}")
            return

        add_ts = self.add_timestamp.get()
        self.log(f"开始处理 {len(file_list)} 个文件...")
        thread = threading.Thread(target=batch_convert, args=(file_list, output_dir, add_ts, self.log))
        thread.daemon = True
        thread.start()

def main():
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = TkinterDnD()
    app = OvjsnConverterApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()