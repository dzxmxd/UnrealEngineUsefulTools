import os
import tkinter as tk
from tkinter import filedialog

def set_files_readonly(directory_path, selected_extensions):
    # 获取指定路径下的所有文件
    modified_files = []

    for root, dirs, files in os.walk(directory_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_extension = os.path.splitext(file_path)[1].lower()

            # 检查文件后缀是否在允许的列表中
            if file_extension in selected_extensions:
                try:
                    # 将文件设为只读
                    os.chmod(file_path, 0o444)
                    modified_files.append(file_path)
                    print(f"Set {file_path} to read-only.")
                except Exception as e:
                    print(f"Error setting {file_path} to read-only: {e}")

    return modified_files

def browse_directory():
    directory_path = filedialog.askdirectory()
    entry_path.delete(0, tk.END)
    entry_path.insert(0, directory_path)

def start_task():
    directory_path = entry_path.get()
    selected_extensions = [ext for ext, var in checkboxes.items() if var.get() == 1]

    if not directory_path or not selected_extensions:
        return

    modified_files = set_files_readonly(directory_path, selected_extensions)

    # 将已修改成功的文件路径显示在滚动框中
    text_output.config(state=tk.NORMAL)
    text_output.delete(1.0, tk.END)
    for file_path in modified_files:
        text_output.insert(tk.END, f"Set {file_path} to read-only.\n")
    text_output.config(state=tk.DISABLED)

# 创建主窗口
root = tk.Tk()
root.title("Set Files Read-only - @FiveMileFog")
root.geometry("530x450")  # 设置窗口大小

# 创建选择路径的部件
tk.Label(root, text="Select Directory:").grid(row=0, column=0, padx=10, pady=10)
entry_path = tk.Entry(root, width=40)
entry_path.grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Browse", command=browse_directory).grid(row=0, column=2, padx=10, pady=10)

# 创建勾选框部件
tk.Label(root, text="Select Extensions:").grid(row=1, column=0, padx=10, pady=10)
checkboxes = {}
default_extensions = [".h", ".hpp", ".c", ".cpp", ".cs"]
for i, extension in enumerate([".h", ".hpp", ".c", ".cpp", ".cs", ".uplugin", ".ush", ".usf", ".ini"]):
    var = tk.IntVar(value=1 if extension in default_extensions else 0)
    checkboxes[extension] = var
    tk.Checkbutton(root, text=extension, variable=var, onvalue=1, offvalue=0).grid(row=i // 3 + 2, column=i % 3, padx=10, pady=5)

# 创建开始任务按钮
start_button = tk.Button(root, text="Start Task", command=start_task)
start_button.grid(row=(len(checkboxes) - 1) // 3 + 3, column=0, columnspan=3, pady=10)

# 创建滚动框
tk.Label(root, text="Modified Files:").grid(row=(len(checkboxes) - 1) // 3 + 4, column=0, pady=10, columnspan=3)
text_output = tk.Text(root, height=10, width=50, state=tk.DISABLED)
text_output.grid(row=(len(checkboxes) - 1) // 3 + 5, column=0, columnspan=3, pady=10, padx=10, sticky="ew")

# 设置"Start Task"按钮居中
root.grid_rowconfigure((len(checkboxes) - 1) // 3 + 3, weight=1)

# 运行主循环
root.mainloop()
