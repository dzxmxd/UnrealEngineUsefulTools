import zipfile
import xml.etree.ElementTree as ET
import sys

def check_xlsx_cell_types(xlsx_path):
    with zipfile.ZipFile(xlsx_path, 'r') as z:
        # 遍历所有工作表
        for name in z.namelist():
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
                print(f"\nChecking {name}...")
                xml_data = z.read(name)
                root = ET.fromstring(xml_data)

                # 遍历 <c> 节点（cell）
                for c in root.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
                    ref = c.attrib.get("r")  # 单元格位置
                    cell_type = c.attrib.get("t", "number")  # 默认为数字
                    value_node = c.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
                    value = value_node.text if value_node is not None else None

                    if cell_type == "str":
                        print(f"  {ref}: '{value}' (stored as TEXT)")
                    elif cell_type == "s":
                        print(f"  {ref}: '{value}' (stored as SHARED STRING)")
                    else:
                        print(f"  {ref}: {value} (stored as NUMBER)")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_cell_types.py <file.xlsx>")
    else:
        check_xlsx_cell_types(sys.argv[1])
