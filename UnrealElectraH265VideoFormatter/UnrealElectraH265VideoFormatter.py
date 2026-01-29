import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import sys
import threading
import subprocess
import ffmpeg  # pip install ffmpeg-python


class VideoCompressorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Unreal H.265 视频格式化工具")
        self.root.geometry("600x550")

        # 获取内置 ffmpeg 路径
        self.ffmpeg_binary = self.resource_path("ffmpeg.exe")

        # 1. Tips 区域
        self.setup_tips_area()

        # 2. 操作按钮区域
        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(pady=20)

        self.btn_file = tk.Button(self.btn_frame, text="选择单文件处理", command=self.select_file, height=2, width=20,
                                  bg="#e1f5fe")
        self.btn_file.pack(side=tk.LEFT, padx=20)

        self.btn_folder = tk.Button(self.btn_frame, text="选择文件夹批量处理", command=self.select_folder, height=2,
                                    width=20, bg="#fff3e0")
        self.btn_folder.pack(side=tk.LEFT, padx=20)

        # 3. 日志输出区域
        tk.Label(root, text="处理日志:").pack(anchor=tk.W, padx=10)
        self.log_text = scrolledtext.ScrolledText(root, height=15, state='disabled')
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 检查环境
        if not os.path.exists(self.ffmpeg_binary):
            self.log(
                f"⚠️ 警告：未找到内置 FFmpeg 引擎。\n路径: {self.ffmpeg_binary}\n如果是开发运行，请确保 ffmpeg.exe 在脚本同级目录。")

    def resource_path(self, relative_path):
        """ 获取资源绝对路径 """
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def setup_tips_area(self):
        tip_frame = tk.LabelFrame(self.root, text="规则说明", padx=10, pady=10, fg="blue")
        tip_frame.pack(fill=tk.X, padx=10, pady=10)

        tips_content = (
            "1. 项目要求全屏视频固定比例为 1920:888\n"
            "2. 其它视频不做要求，工具会按原始比例处理\n"
            "3. 限制最大宽 1920，最大高 1088 (等比例缩放)\n"
            "4. 批量处理时请耐心等待，H.265编码较慢"
        )
        tk.Label(tip_frame, text=tips_content, justify=tk.LEFT, font=("微软雅黑", 10)).pack(anchor=tk.W)

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def process_video_ffmpeg_python(self, input_path, output_path):
        try:
            stream = ffmpeg.input(input_path)
            stream = ffmpeg.filter(stream, 'scale', w=1920, h=1088, force_original_aspect_ratio='decrease')
            stream = ffmpeg.filter(stream, 'pad', 'ceil(iw/2)*2', 'ceil(ih/2)*2')

            output_kwargs = {
                'vcodec': 'libx265',
                'pix_fmt': 'yuv420p',
                'x265-params': 'repeat-headers=1:aud=0:info=0:sei=0',
                'tag:v': 'hvc1',
                'movflags': '+faststart'
            }
            stream = ffmpeg.output(stream, output_path, **output_kwargs)

            cmd_args = ffmpeg.compile(stream, cmd=self.ffmpeg_binary, overwrite_output=True)

            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                # SW_HIDE = 0，强制隐藏窗口
                startupinfo.wShowWindow = 0

            process = subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,  # 防止 ffmpeg 等待输入
                startupinfo=startupinfo,  # <--- 这里传入隐藏配置
                encoding='utf-8',  # 自动解码
                errors='ignore'  # 忽略解码错误
            )

            # 等待执行完成
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                return True, None
            else:
                # 失败，返回 stderr
                return False, stderr

        except ffmpeg.Error as e:
            # compile 阶段出错
            return False, str(e)
        except Exception as e:
            # subprocess 阶段出错
            return False, str(e)

    def process_thread(self, files_to_process):
        self.btn_file.config(state='disabled')
        self.btn_folder.config(state='disabled')

        success_count = 0
        total = len(files_to_process)

        for idx, file_path in enumerate(files_to_process):
            directory, filename = os.path.split(file_path)
            name, ext = os.path.splitext(filename)

            output_dir = os.path.join(directory, "Output")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            output_path = os.path.join(output_dir, f"{filename}")
            if not output_path.lower().endswith(('.mp4', '.mov', '.mkv')):
                output_path = os.path.join(output_dir, f"{name}.mp4")

            self.log(f"[{idx + 1}/{total}] 处理中: {filename}")
            # 更新界面 UI，防止看起来像卡死
            self.root.update_idletasks()

            success, err_msg = self.process_video_ffmpeg_python(file_path, output_path)

            if success:
                self.log(f"   ---> ✅ 成功")
                success_count += 1
            else:
                self.log(f"   ---> ❌ 失败")
                if err_msg:
                    # 只显示最后一行关键报错，避免刷屏
                    last_line = err_msg.strip().splitlines()[-1] if err_msg else "Unknown"
                    self.log(f"   [Error]: {last_line}")

        self.log(f"\n✅ 全部任务结束。成功: {success_count} / 总计: {total}")
        messagebox.showinfo("完成", f"处理完成！\n成功: {success_count} 个文件")

        self.btn_file.config(state='normal')
        self.btn_folder.config(state='normal')

    def start_processing(self, files):
        if not files:
            return
        t = threading.Thread(target=self.process_thread, args=(files,))
        t.start()

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=[("Video Files", "*.mp4 *.mov *.avi *.mkv *.flv *.wmv"), ("All Files", "*.*")]
        )
        if file_path:
            self.start_processing([file_path])

    def select_folder(self):
        folder_path = filedialog.askdirectory(title="选择包含视频的文件夹")
        if folder_path:
            video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv')
            files = []
            for f in os.listdir(folder_path):
                if f.lower().endswith(video_extensions):
                    files.append(os.path.join(folder_path, f))

            if not files:
                self.log("⚠️ 选定文件夹中未找到视频文件。")
                return

            self.start_processing(files)


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoCompressorApp(root)
    root.mainloop()