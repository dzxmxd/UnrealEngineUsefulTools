import os
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import stat
import ctypes

EXCLUDED_DIRS = {
    'Intermediate', 'Saved', 'DerivedDataCache', 'Binaries', 'Build', 'ThirdParty', 'Content'
}


def set_files_readonly(directory_path, selected_extensions, text_output, start_button):
    modified_files = []
    file_count = 0

    try:
        # 禁用开始按钮
        root.after(0, lambda: start_button.config(state=tk.DISABLED))

        # 清空文本框
        root.after(0, lambda: text_output.config(state=tk.NORMAL))
        root.after(0, lambda: text_output.delete(1.0, tk.END))
        root.after(0, lambda: text_output.config(state=tk.DISABLED))

        for root_dir, dirs, files in os.walk(directory_path):
            # 排除不需要设置为只读的目录
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for file_name in files:
                file_path = os.path.join(root_dir, file_name)
                file_extension = os.path.splitext(file_path)[1].lower()

                # 检查文件后缀是否在允许的列表中
                if file_extension in selected_extensions:
                    try:
                        # Windows平台特定的设置只读属性
                        if os.name == 'nt':
                            # 获取当前文件属性
                            file_attributes = ctypes.windll.kernel32.GetFileAttributesW(file_path)
                            # 设置只读属性 (FILE_ATTRIBUTE_READONLY = 0x1)
                            ctypes.windll.kernel32.SetFileAttributesW(file_path, file_attributes | 0x1)
                        else:
                            # 非Windows平台使用chmod
                            os.chmod(file_path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)

                        modified_files.append(file_path)
                        file_count += 1

                        # 每处理10个文件更新一次UI
                        if file_count % 10 == 0:
                            # 使用after方法在主线程中更新UI
                            root.after(0, update_ui, text_output, f"已处理{file_count}个文件...\n")

                    except Exception as e:
                        error_msg = f"设置{file_path}为只读时出错: {e}"
                        print(error_msg)
                        root.after(0, update_ui, text_output, error_msg + "\n")

    finally:
        # 任务完成，更新UI并重新启用按钮
        root.after(0, lambda: start_button.config(state=tk.NORMAL))
        root.after(0, update_ui, text_output, f"\n任务完成！共设置{len(modified_files)}个文件为只读。\n")
        root.after(0, lambda: messagebox.showinfo("完成", f"已将{len(modified_files)}个文件设置为只读"))


def update_ui(text_output, message):
    """线程安全的UI更新函数"""
    text_output.config(state=tk.NORMAL)
    text_output.insert(tk.END, message)
    text_output.see(tk.END)  # 滚动到最新内容
    text_output.config(state=tk.DISABLED)


def browse_directory():
    directory_path = filedialog.askdirectory()
    entry_path.delete(0, tk.END)
    entry_path.insert(0, directory_path)


def start_task():
    directory_path = entry_path.get()
    selected_extensions = [ext for ext, var in checkboxes.items() if var.get() == 1]

    if not directory_path or not selected_extensions:
        messagebox.showwarning("警告", "请选择一个目录和至少一个文件扩展名。")
        return

    # 使用线程处理长时间任务
    task_thread = threading.Thread(target=set_files_readonly, args=(directory_path, selected_extensions, text_output, start_button))
    task_thread.daemon = True  # 设为守护线程，主程序退出时自动结束
    task_thread.start()


# 创建主窗口
root = tk.Tk()
root.title("UE引擎源码只读工具 - @FiveMileFog")
root.geometry("530x450")  # 设置窗口大小

# 创建选择路径的部件
tk.Label(root, text="选择目录:").grid(row=0, column=0, padx=10, pady=10)
entry_path = tk.Entry(root, width=40)
entry_path.grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="浏览", command=browse_directory).grid(row=0, column=2, padx=10, pady=10)

# 创建勾选框部件
tk.Label(root, text="选择文件类型:").grid(row=1, column=0, padx=10, pady=10)
checkboxes = {}
default_extensions = [".h", ".hpp", ".c", ".cpp", ".cs", ".uplugin"]
for i, extension in enumerate([".h", ".hpp", ".c", ".cpp", ".cs", ".uplugin", ".ush", ".usf", ".ini"]):
    var = tk.IntVar(value=1 if extension in default_extensions else 0)
    checkboxes[extension] = var
    tk.Checkbutton(root, text=extension, variable=var, onvalue=1, offvalue=0).grid(row=i // 3 + 2, column=i % 3, padx=10, pady=5)

# 创建开始任务按钮
start_button = tk.Button(root, text="开始处理", command=start_task)
start_button.grid(row=(len(checkboxes) - 1) // 3 + 3, column=0, columnspan=3, pady=10)

# 创建滚动框
tk.Label(root, text="处理日志:").grid(row=(len(checkboxes) - 1) // 3 + 4, column=0, pady=10, columnspan=3)
text_output = tk.Text(root, height=10, width=50, state=tk.DISABLED)
text_output.grid(row=(len(checkboxes) - 1) // 3 + 5, column=0, columnspan=3, pady=10, padx=10, sticky="ew")

# 添加滚动条
scrollbar = tk.Scrollbar(root, command=text_output.yview)
scrollbar.grid(row=(len(checkboxes) - 1) // 3 + 5, column=3, pady=10, sticky="ns")
text_output.config(yscrollcommand=scrollbar.set)

# 设置"Start Task"按钮居中
root.grid_rowconfigure((len(checkboxes) - 1) // 3 + 3, weight=1)

# 运行主循环
root.mainloop()
