from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def repair(s):
    for _ in range(3):
        out=[];i=0;changed=False
        while i<len(s):
            count={0xc2:2,0xc3:2,0xe2:3,0xf0:4}.get(ord(s[i]),0)
            part=s[i:i+count]
            if count and len(part)==count:
                try:
                    raw=b''.join(c.encode('cp1252') if not 0x80<=ord(c)<=0x9f else bytes([ord(c)]) for c in part)
                    fixed=raw.decode('utf8')
                    out.append(fixed);i+=count;changed=True;continue
                except (UnicodeError,ValueError):pass
            out.append(s[i]);i+=1
        s=''.join(out)
        if not changed:break
    return s
for base in [ROOT/'gui',ROOT/'refinement_artifacts']:
    for p in base.rglob('*'):
        if not p.is_file() or p.suffix not in ['.tsx','.ts','.css','.cjs','.mjs','.py','.ps1','.md']:continue
        if any(x in p.parts for x in ['node_modules','.runtime','dist','originals','source_renders','build']):continue
        text=p.read_text(encoding='utf8');fixed=repair(text)
        if text!=fixed:p.write_text(fixed,encoding='utf8');print(p.relative_to(ROOT))
