"""Preserve original editable charts and their exact embedded workbook bytes."""
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

source, candidate = map(Path, sys.argv[1:])
with zipfile.ZipFile(source) as src, zipfile.ZipFile(candidate) as dst:
    parts = {name: dst.read(name) for name in dst.namelist()}
    kept = [name for name in src.namelist() if '/charts/' in name or name.startswith('ppt/embeddings/')]
    for name in kept:
        parts[name] = src.read(name)
    ns = 'http://schemas.openxmlformats.org/package/2006/content-types'
    ET.register_namespace('', ns)
    types = ET.fromstring(parts['[Content_Types].xml'])
    old_types = ET.fromstring(src.read('[Content_Types].xml'))
    existing = {(item.tag, item.get('PartName'), item.get('Extension')) for item in types}
    for item in old_types:
        relevant = item.get('Extension') == 'xlsx' or item.get('PartName', '').lstrip('/') in kept
        key = (item.tag, item.get('PartName'), item.get('Extension'))
        if relevant and key not in existing:
            types.append(item)
            existing.add(key)
    parts['[Content_Types].xml'] = ET.tostring(types, encoding='utf-8', xml_declaration=True)
temp = candidate.with_suffix('.chart-preserved.pptx')
with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) as out:
    for name, data in parts.items():
        out.writestr(name, data)
temp.replace(candidate)
with zipfile.ZipFile(source) as src, zipfile.ZipFile(candidate) as dst:
    assert all(src.read(name) == dst.read(name) for name in kept)
print(f'Preserved {len(kept)} source chart/workbook parts byte-for-byte')
