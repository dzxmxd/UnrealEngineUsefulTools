import csv
import polib
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

def contains_chinese(text):
    return any('\u4e00' <= ch <= '\u9fff' for ch in text)

def po_to_csv(po_file_path, only_chinese=False):
    po = polib.pofile(po_file_path)

    # 输出 CSV 文件路径：同目录，同名改扩展
    base_name = os.path.splitext(os.path.basename(po_file_path))[0]
    csv_file_path = os.path.join(os.path.dirname(po_file_path), f"{base_name}.csv")

    with open(csv_file_path, mode='w', newline='', encoding='utf-8-sig') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['comment', 'msgctxt', 'msgid'])

        for entry in po:
            msgid = entry.msgid or ''
            msgctxt = entry.msgctxt or ''
            comment = entry.comment or ''

            if only_chinese and not contains_chinese(msgid):
                continue

            csv_writer.writerow([comment, msgctxt, msgid])

    return csv_file_path

def main():
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    po_file_path = filedialog.askopenfilename(
        title="选择 PO 文件",
        filetypes=[("PO files", "*.po")]
    )
    if not po_file_path:
        messagebox.showinfo("取消", "未选择文件")
        return

    # 询问是否只保留含中文的行
    only_chinese = messagebox.askyesno("选项", "是否只保留包含中文的行？")

    csv_file_path = po_to_csv(po_file_path, only_chinese)
    messagebox.showinfo("完成", f"CSV 已输出到:\n{csv_file_path}")

if __name__ == "__main__":
    main()
