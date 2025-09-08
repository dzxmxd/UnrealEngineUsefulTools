import zipfile
import xml.etree.ElementTree as ET
import sys

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"

def diagnose_xlsx(path):
    issues = []
    with zipfile.ZipFile(path, "r") as z:
        files = set(z.namelist())

        # 1. check [Content_Types].xml
        if "[Content_Types].xml" in files:
            tree = ET.fromstring(z.read("[Content_Types].xml"))
            for over in tree.findall("{http://schemas.openxmlformats.org/package/2006/content-types}Override"):
                part = over.attrib["PartName"].lstrip("/")
                if part not in files:
                    issues.append(f"[Content_Types].xml: Override references missing part '{part}'")

        # 2. check workbook relationships
        if "xl/_rels/workbook.xml.rels" in files:
            rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
            for rel in rels.findall(REL_NS + "Relationship"):
                rid = rel.attrib["Id"]
                target = "xl/" + rel.attrib["Target"].lstrip("/")
                if target not in files:
                    issues.append(f"workbook.xml.rels: Relationship {rid} -> missing part '{target}'")

        # 3. check workbook.xml sheets
        if "xl/workbook.xml" in files:
            tree = ET.fromstring(z.read("xl/workbook.xml"))
            for sheet in tree.findall(NS + "sheets/" + NS + "sheet"):
                rid = sheet.attrib.get(f"{{http://schemas.openxmlformats.org/officeDocument/2006/relationships}}id")
                name = sheet.attrib.get("name")
                if rid is None:
                    issues.append(f"workbook.xml: sheet '{name}' references unknown relationship 'None'")

        # 4. check worksheets formulas
        for name in files:
            if name.startswith("xl/worksheets/") and name.endswith(".xml"):
                root = ET.fromstring(z.read(name))
                for f in root.findall(".//" + NS + "f"):
                    txt = f.text or ""
                    if not txt.strip():
                        issues.append(f"{name}: empty formula tag at cell {f.attrib.get('r','?')}")

    if issues:
        print("Potential issues detected:")
        for i in issues:
            print(" -", i)
    else:
        print("No obvious structural issues found. Excel error may be style/theme related.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python xlsx_diagnose.py file.xlsx")
    else:
        diagnose_xlsx(sys.argv[1])
