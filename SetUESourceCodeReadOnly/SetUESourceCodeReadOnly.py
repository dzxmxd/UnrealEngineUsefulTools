import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import threading
import stat
import ctypes

# 默认设置
DEFAULT_EXCLUDED_DIRS = {
    'Intermediate', 'Saved', 'DerivedDataCache', 'Binaries', 'Build', 'ThirdParty', 'Content', 'obj'
}

DEFAULT_EXTENSIONS = {
    '.h', '.hpp', '.c', '.cpp'
}

# 当前使用的设置
EXCLUDED_DIRS = DEFAULT_EXCLUDED_DIRS.copy()
EXTENSIONS = DEFAULT_EXTENSIONS.copy()


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


# 通用列表管理函数
def add_to_list(list_name, listbox, items_set, title, prompt):
    """通用的添加项目到列表的函数"""
    new_item = simpledialog.askstring(title, prompt)
    if new_item and new_item.strip():
        new_item = new_item.strip()
        if new_item.startswith('.') or list_name == "排除目录":
            if new_item not in items_set:
                items_set.add(new_item)
                update_list(listbox, items_set)
                messagebox.showinfo("成功", f"已添加 '{new_item}' 到{list_name}")
            else:
                messagebox.showinfo("提示", f"'{new_item}' 已在{list_name}列表中")
        else:
            # 文件扩展名自动添加点前缀
            if list_name == "文件类型" and not new_item.startswith('.'):
                new_item = '.' + new_item
            if new_item not in items_set:
                items_set.add(new_item)
                update_list(listbox, items_set)
                messagebox.showinfo("成功", f"已添加 '{new_item}' 到{list_name}")
            else:
                messagebox.showinfo("提示", f"'{new_item}' 已在{list_name}列表中")


def remove_from_list(list_name, listbox, items_set):
    """通用的从列表中移除项目的函数"""
    selected_index = listbox.curselection()
    if not selected_index:
        messagebox.showwarning("警告", f"请先选择要删除的{list_name}项")
        return

    item_to_remove = listbox.get(selected_index)
    items_set.remove(item_to_remove)
    update_list(listbox, items_set)
    messagebox.showinfo("成功", f"已从{list_name}中移除 '{item_to_remove}'")


def reset_list(list_name, listbox, items_set, default_set):
    """通用的重置列表到默认值的函数"""
    items_set.clear()
    items_set.update(default_set)
    update_list(listbox, items_set)
    messagebox.showinfo("成功", f"已重置{list_name}列表为默认值")


def update_list(listbox, items_set):
    """通用的更新列表显示的函数"""
    listbox.delete(0, tk.END)
    for item in sorted(items_set):
        listbox.insert(tk.END, item)


# 排除目录特定函数
def add_excluded_dir():
    add_to_list("排除目录", excluded_dirs_listbox, EXCLUDED_DIRS, "添加排除目录", "请输入要排除的目录名称:")


def remove_excluded_dir():
    remove_from_list("排除目录", excluded_dirs_listbox, EXCLUDED_DIRS)


def reset_excluded_dirs():
    reset_list("排除目录", excluded_dirs_listbox, EXCLUDED_DIRS, DEFAULT_EXCLUDED_DIRS)


# 文件类型特定函数
def add_extension():
    add_to_list("文件类型", extensions_listbox, EXTENSIONS, "添加文件类型", "请输入要设置为只读的文件扩展名(如 .h):")


def remove_extension():
    remove_from_list("文件类型", extensions_listbox, EXTENSIONS)


def reset_extensions():
    reset_list("文件类型", extensions_listbox, EXTENSIONS, DEFAULT_EXTENSIONS)


def start_task():
    directory_path = entry_path.get()

    if not directory_path or not EXTENSIONS:
        messagebox.showwarning("警告", "请选择一个目录和至少一个文件扩展名。")
        return

    # 使用线程处理长时间任务
    task_thread = threading.Thread(target=set_files_readonly,
                                   args=(directory_path, EXTENSIONS, text_output, start_button))
    task_thread.daemon = True  # 设为守护线程，主程序退出时自动结束
    task_thread.start()


# 创建主窗口
root = tk.Tk()
root.title("UE引擎源码只读工具 - @FiveMileFog")
root.geometry("460x550")  # 适当调整窗口大小

# 创建选择路径的部件
tk.Label(root, text="选择目录:").grid(row=0, column=0, padx=10, pady=10)
entry_path = tk.Entry(root, width=40)
entry_path.grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="浏览", command=browse_directory).grid(row=0, column=2, padx=10, pady=10)

# 添加排除目录列表部分
tk.Label(root, text="排除目录列表:").grid(row=1, column=0, pady=0, columnspan=3)

# 创建排除目录列表框
excluded_dirs_frame = tk.Frame(root)
excluded_dirs_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

excluded_dirs_listbox = tk.Listbox(excluded_dirs_frame, height=4, width=40)
excluded_dirs_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 添加排除目录列表滚动条
excluded_dirs_scrollbar = tk.Scrollbar(excluded_dirs_frame, command=excluded_dirs_listbox.yview)
excluded_dirs_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
excluded_dirs_listbox.config(yscrollcommand=excluded_dirs_scrollbar.set)

# 排除目录操作按钮
excluded_dirs_buttons_frame = tk.Frame(root)
excluded_dirs_buttons_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=5)

add_button = tk.Button(excluded_dirs_buttons_frame, text="添加目录", command=add_excluded_dir)
add_button.pack(side=tk.LEFT, padx=5)

remove_button = tk.Button(excluded_dirs_buttons_frame, text="删除选中", command=remove_excluded_dir)
remove_button.pack(side=tk.LEFT, padx=5)

reset_button = tk.Button(excluded_dirs_buttons_frame, text="重置为默认", command=reset_excluded_dirs)
reset_button.pack(side=tk.LEFT, padx=5)

# 添加文件类型列表部分
tk.Label(root, text="文件类型列表:").grid(row=4, column=0, pady=0, columnspan=3)

# 创建文件类型列表框
extensions_frame = tk.Frame(root)
extensions_frame.grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

extensions_listbox = tk.Listbox(extensions_frame, height=4, width=40)
extensions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 添加文件类型列表滚动条
extensions_scrollbar = tk.Scrollbar(extensions_frame, command=extensions_listbox.yview)
extensions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
extensions_listbox.config(yscrollcommand=extensions_scrollbar.set)

# 文件类型操作按钮
extensions_buttons_frame = tk.Frame(root)
extensions_buttons_frame.grid(row=6, column=0, columnspan=3, padx=10, pady=5)

add_ext_button = tk.Button(extensions_buttons_frame, text="添加类型", command=add_extension)
add_ext_button.pack(side=tk.LEFT, padx=5)

remove_ext_button = tk.Button(extensions_buttons_frame, text="删除选中", command=remove_extension)
remove_ext_button.pack(side=tk.LEFT, padx=5)

reset_ext_button = tk.Button(extensions_buttons_frame, text="重置为默认", command=reset_extensions)
reset_ext_button.pack(side=tk.LEFT, padx=5)

# 创建开始任务按钮
start_button = tk.Button(root, text="开始处理", command=start_task)
start_button.grid(row=7, column=0, columnspan=3, pady=10)

# 创建滚动框
# tk.Label(root, text="处理日志:").grid(row=8, column=0, pady=0, columnspan=3)
text_output = tk.Text(root, height=10, width=50, state=tk.DISABLED)
text_output.grid(row=9, column=0, columnspan=3, pady=10, padx=10, sticky="ew")

# 添加滚动条
scrollbar = tk.Scrollbar(root, command=text_output.yview)
scrollbar.grid(row=9, column=3, pady=10, sticky="ns")
text_output.config(yscrollcommand=scrollbar.set)

# 初始化列表显示
update_list(excluded_dirs_listbox, EXCLUDED_DIRS)
update_list(extensions_listbox, EXTENSIONS)

# 运行主循环
root.mainloop()
