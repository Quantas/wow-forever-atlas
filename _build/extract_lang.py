"""Adds one more language to data.json, fp.json and dj.json by reading the map in that language.
Usage: python3 _build/extract_lang.py de   (the map must exist at /<lang>/index.html). Resumable."""
import os, sys, json, re
from playwright.sync_api import sync_playwright
from urllib.parse import quote
L=sys.argv[1]; HERE=os.path.dirname(os.path.abspath(__file__)); BASE='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'+L+'/index.html'
exec(open(os.path.join(HERE,'pairs.py')).read())
D=json.load(open(os.path.join(HERE,'data.json'))); FP=json.load(open(os.path.join(HERE,'fp.json'))); DJ=json.load(open(os.path.join(HERE,'dj.json')))
JS="""()=>{const q=s=>document.querySelector(s);
 const steps=[...document.querySelectorAll('ol.steps li')].map(li=>{const t=li.querySelector('.st-t');const m=li.querySelector('.st-m');
   const title=t?[...t.childNodes].filter(n=>n!==m).map(n=>n.textContent).join('').trim():'';const s=li.querySelector('.st-s');
   return {t:title,m:m?m.textContent.trim():'',s:s?[...s.childNodes].map(n=>n.textContent.trim()).filter(Boolean).join(' · '):'',w:[...li.querySelectorAll('.warn')].map(w=>w.textContent.trim()),end:li.classList.contains('end')};});
 const jr=q('.jr'); let card=null;
 if(jr){const r=jr.querySelector('.risk'); card={cls:r?[...r.classList].filter(c=>c!=='risk')[0]||'':'',risk:r?r.textContent.trim():'',items:[...jr.querySelectorAll('li')].map(l=>l.textContent.trim()),
   tip:(jr.querySelector('.jr-tip')||{}).textContent||'',facts:[...jr.querySelectorAll('.dj-facts span')].map(x=>x.textContent.trim()),ps:[...jr.querySelectorAll('p')].filter(p=>!p.classList.contains('jr-tip')).map(p=>p.textContent.trim())};}
 return {eta:q('.eta-n')?.textContent.trim()||null,sub:q('.eta-s')?.textContent.trim()||null,steps,card,alt:[],warnTop:[]};}"""
other={'horde':'alliance','alliance':'horde'}
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1440,'height':900})
    pg.route('**/*',lambda r: r.abort() if r.request.url.startswith('http') else r.continue_())
    def run(a,c,f,by,fp):
        pg.goto(BASE+f'#from={quote(a)}&to={quote(c)}&f={f}&by={by}'+('&fp=1' if fp else '')); pg.reload(); pg.wait_for_timeout(450); return pg.evaluate(JS)
    for s,a,c,f,g in PAIRS:
        if L in D[s] and D[s][L]: continue
        D[s][L]={'foot':run(a,c,f,'foot',False),'fly':run(a,c,f,'m100',True),'other':run(a,c,other[f],'foot',False)}
        json.dump(D,open(os.path.join(HERE,'data.json'),'w'),ensure_ascii=False); print('route',s,flush=True)
    if L not in FP:
        pg.goto(BASE); pg.wait_for_timeout(900)
        fps=pg.evaluate("""()=>POIS.filter(p=>p.fp).map(p=>({id:p.id,n:p.n,z:p.z,fp:p.fp,isNew:!!(p.isNew||p.new||p.status==='new'),tn:window.__tN(p.n),zn:window.__tN(ZONES[p.z].name),cont:ZONES[p.z].cont,lv:ZONES[p.z].lv,zf:ZONES[p.z].faction,zst:ZONES[p.z].status}))""")
        for f in fps:
            pg.evaluate(f"""()=>{{const s=document.getElementById('sheet');const b=document.createElement('button');b.dataset.goto='{f["id"]}';s.appendChild(b);b.click();}}"""); pg.wait_for_timeout(120)
            f['fl']=pg.evaluate("""()=>{const h=[...document.querySelectorAll('#sheet h2')].find(x=>/flight|vol|vuelo|flug/i.test(x.textContent)); if(!h) return [];
               const o=[]; let n=h.nextElementSibling; while(n && n.tagName!=='H2'){ if(n.matches('button.place')) o.push([n.querySelector('.pn')?.textContent, n.querySelector('.pm')?.textContent]); n=n.nextElementSibling;} return o;}""")
            if not f['fl']: f['lead']=pg.evaluate("document.querySelector('#sheet p.lead')?.textContent.trim().replace(/\\s+/g,' ')")
        FP[L]=fps; json.dump(FP,open(os.path.join(HERE,'fp.json'),'w'),ensure_ascii=False); print('fp',len(fps),flush=True)
    pg.goto(BASE); pg.wait_for_timeout(800)
    for n,d in DJ.items():
        if L in d.get('route_horde',{}) and L in d.get('route_alliance',{}): continue
        d[L]=dict(zip(['n','zone','d'],pg.evaluate("(a)=>[window.__tN(a[0]),window.__tN(a[1]),window.__tr?window.__tr(a[2]):a[2]]",[d['n'],d['zone'],d['d']])))
        for f in ['horde','alliance']: d['route_'+f][L]=run(d['best_'+f],d['n'],f,d['speed'],True)
        json.dump(DJ,open(os.path.join(HERE,'dj.json'),'w'),ensure_ascii=False); print('dj',n,flush=True)
    b.close()
print('done')
