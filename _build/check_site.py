import os,re,json,sys
from urllib.parse import urlparse,unquote
SITE=sys.argv[1]; bad=[]; n=0; gc=0; pagesn=0
files=[]
for root,_,fs in os.walk(SITE):
    if '/_build' in root or '/.git' in root: continue
    for f in fs:
        if f.endswith('.html'): files.append(os.path.join(root,f))
def exists(path):
    p=os.path.join(SITE,unquote(path).lstrip('/'))
    return os.path.isfile(p) or os.path.isfile(os.path.join(p,'index.html'))
for f in files:
    s=open(f,encoding='utf-8').read(); rel='/'+os.path.relpath(f,SITE)
    if 'goatcounter' in s: gc+=1
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>',s,re.S):
        try: json.loads(m.group(1))
        except Exception as ex: bad.append(('jsonld',rel,str(ex)[:60]))
    for h in re.findall(r'href="([^"]+)"',s):
        if h.startswith(('http','mailto:','#','data:')) or '${' in h or "' +" in h: continue
        n+=1; path=h.split('#')[0].replace('&amp;','&')
        if not path: continue
        if not path.startswith('/'): path=os.path.normpath(os.path.join(os.path.dirname(rel),path))
        if not exists(path): bad.append(('link',rel,h))
print('html files',len(files),'links checked',n,'with goatcounter',gc,'problems',len(bad))
for b in bad[:30]: print(b)
