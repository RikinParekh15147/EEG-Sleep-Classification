import sys, zipfile
from pathlib import Path
from xml.etree import ElementTree as E
source,candidate=map(Path,sys.argv[1:])
with zipfile.ZipFile(source) as src, zipfile.ZipFile(candidate) as dst:
    parts={n:dst.read(n) for n in dst.namelist()}
    kept=[n for n in src.namelist() if '/charts/' in n or n.startswith('ppt/embeddings/')]
    for n in kept: parts[n]=src.read(n)
    ns='http://schemas.openxmlformats.org/package/2006/content-types'
    E.register_namespace('',ns)
    types=E.fromstring(parts['[Content_Types].xml'])
    existing={(x.tag,x.get('PartName'),x.get('Extension')) for x in types}
    for x in E.fromstring(src.read('[Content_Types].xml')):
        key=(x.tag,x.get('PartName'),x.get('Extension'))
        if (x.get('Extension')=='xlsx' or x.get('PartName','').lstrip('/') in kept) and key not in existing:
            types.append(x);existing.add(key)
    parts['[Content_Types].xml']=E.tostring(types,encoding='utf-8',xml_declaration=True)
ns_a='http://schemas.openxmlformats.org/drawingml/2006/main'
ns_p='http://schemas.openxmlformats.org/presentationml/2006/main'
ns_c='http://schemas.openxmlformats.org/drawingml/2006/chart'
for prefix,uri in [('a',ns_a),('p',ns_p),('c',ns_c)]: E.register_namespace(prefix,uri)
count=0
for n,data in list(parts.items()):
    if not n.endswith('.xml') or not (n.startswith('ppt/slides/slide') or '/charts/chart' in n): continue
    root=E.fromstring(data);parents={c:p for p in root.iter() for c in p}
    chart='/charts/' in n
    for color in root.iter('{'+ns_a+'}srgbClr'):
        chain=[];cur=color
        while cur in parents:
            cur=parents[cur];chain.append(cur.tag.split('}')[-1])
        text=any(t in chain for t in ('rPr','defRPr','endParaRPr','txPr'))
        val=color.get('val','').upper()
        if text:
            mapping={'102E49':'FFFFFF','526977':'BED0E4','18A69B':'75D5FF','000000':'FFFFFF','595959':'BED0E4','666666':'BED0E4'}
        elif chart:
            mapping={'F5FAFC':'0E2C50','FFFFFF':'0E2C50','102E49':'84B9FF','18A69B':'6CDCDD','000000':'BED0E4','D9D9D9':'436280'}
        else:
            mapping={'F5FAFC':'0E2C50','FFFFFF':'123658','E8F2F5':'1D4770','102E49':'18558A','18A69B':'75D5FF','000000':'5F83A6'}
        if val in mapping: color.set('val',mapping[val]);count+=1
    if chart:
        for prop in root.iter():
            if prop.tag in ('{'+ns_a+'}rPr','{'+ns_a+'}defRPr','{'+ns_a+'}endParaRPr'):
                fill=prop.find('{'+ns_a+'}solidFill')
                if fill is None:
                    fill=E.Element('{'+ns_a+'}solidFill')
                    E.SubElement(fill,'{'+ns_a+'}srgbClr',{'val':'FFFFFF'})
                    prop.insert(0,fill)
                if not prop.get('sz'): prop.set('sz','1275')
    parts[n]=E.tostring(root,encoding='utf-8',xml_declaration=True)
tmp=candidate.with_suffix('.themed.pptx')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as out:
    for n,data in parts.items():out.writestr(n,data)
tmp.replace(candidate)
with zipfile.ZipFile(source) as src,zipfile.ZipFile(candidate) as dst:
    assert all(src.read(n)==dst.read(n) for n in kept if n.startswith('ppt/embeddings/') or n.endswith('.rels'))
print(f'Blue theme applied to {count} colors; source chart workbooks preserved')
