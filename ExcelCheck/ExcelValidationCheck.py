# xlsx_part_checker.py
# 检查 .xlsx 文件中是否存在缺失的部件或错误的关系
# 用法:
#   python xlsx_part_checker.py <path_to_xlsx>

import sys
import zipfile
import xml.etree.ElementTree as ET
import posixpath

RELS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
SSML_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"

def read_xml_from_zip(zf: zipfile.ZipFile, name: str):
    try:
        with zf.open(name) as fp:
            return ET.fromstring(fp.read())
    except KeyError:
        return None
    except ET.ParseError as e:
        return f"XML parse error in {name}: {e}"

def resolve_target(base_part: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    base_dir = posixpath.dirname(base_part)
    combined = posixpath.normpath(posixpath.join(base_dir, target))
    return combined

def list_zip_names(zf: zipfile.ZipFile):
    return set(name for name in zf.namelist())

def check_relationships(zf: zipfile.ZipFile, rels_part: str, problems: list):
    xml = read_xml_from_zip(zf, rels_part)
    if xml is None:
        problems.append(f"Missing relationships part: {rels_part}")
        return {}
    if isinstance(xml, str):
        problems.append(xml)
        return {}
    mapping = {}
    for rel in xml.findall(f"{{{RELS_NS}}}Relationship"):
        rid = rel.get("Id")
        rtype = rel.get("Type")
        target = rel.get("Target")
        mode = rel.get("TargetMode", "Internal")
        if not rid or not target:
            problems.append(f"{rels_part}: Relationship missing Id/Target")
            continue
        mapping[rid] = (rtype, target, mode)
        if mode == "External":
            continue
        resolved = resolve_target(rels_part.replace("_rels/", "").replace(".rels", ""), target)
        if resolved not in zf.namelist():
            problems.append(f"{rels_part}: Relationship {rid} -> missing part '{resolved}' (Type={rtype})")
    return mapping

def main(path):
    problems = []
    try:
        zf = zipfile.ZipFile(path, "r")
    except Exception as e:
        print(f"Failed to open zip: {e}")
        return

    names = list_zip_names(zf)

    required = ["[Content_Types].xml", "_rels/.rels", "xl/workbook.xml", "xl/_rels/workbook.xml.rels"]
    for req in required:
        if req not in names:
            problems.append(f"Missing required part: {req}")

    root_map = {}
    if "_rels/.rels" in names:
        root_map = check_relationships(zf, "_rels/.rels", problems)

    wb_rels_map = {}
    if "xl/_rels/workbook.xml.rels" in names:
        wb_rels_map = check_relationships(zf, "xl/_rels/workbook.xml.rels", problems)

    wb = read_xml_from_zip(zf, "xl/workbook.xml")
    if isinstance(wb, str):
        problems.append(wb)
        wb = None
    if wb is not None:
        sheets = wb.find(f"{{{SSML_NS}}}sheets")
        if sheets is None:
            problems.append("workbook.xml: Missing <sheets> element")
        else:
            for sheet in sheets.findall(f"{{{SSML_NS}}}sheet"):
                rid = sheet.get(f"{{{RELS_NS}}}id")
                name = sheet.get("name", "?")
                if rid not in wb_rels_map:
                    problems.append(f"workbook.xml: sheet '{name}' references unknown relationship '{rid}'")
                else:
                    _, target, mode = wb_rels_map[rid]
                    if mode != "Internal":
                        problems.append(f"workbook.xml: sheet '{name}' relationship '{rid}' is External (unexpected)")
                    else:
                        resolved = resolve_target("xl/workbook.xml", target)
                        if resolved not in names:
                            problems.append(f"workbook.xml: sheet '{name}' target part missing: '{resolved}'")

    ct = read_xml_from_zip(zf, "[Content_Types].xml")
    if isinstance(ct, str):
        problems.append(ct)
        ct = None
    if ct is not None:
        for ov in ct.findall("{http://schemas.openxmlformats.org/package/2006/content-types}Override"):
            part_name = ov.get("PartName", "").lstrip("/")
            if part_name and part_name not in names:
                problems.append(f"[Content_Types].xml: Override references missing part '{part_name}'")

    for name in list(names):
        if name.startswith("xl/worksheets/") and name.endswith(".xml"):
            rels_name = "xl/worksheets/_rels/" + posixpath.basename(name) + ".rels"
            if rels_name in names:
                check_relationships(zf, rels_name, problems)

    if not problems:
        print("No packaging issues detected. The .xlsx looks structurally sound.")
    else:
        print("Potential issues detected:")
        for p in problems:
            print(" - " + p)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python xlsx_part_checker.py <path_to_xlsx>")
    else:
        main(sys.argv[1])
