import os
import json
from playwright.sync_api import sync_playwright
import os
HERE=os.path.dirname(os.path.abspath(__file__))
BASE='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
out={}
with sync_playwright() as p:
    b=p.chromium.launch()
    for L in ['en','fr','es']:
        pg=b.new_page(viewport={'width':1440,'height':900})
        pg.route('**/*',lambda r: r.abort() if r.request.url.startswith('http') else r.continue_())
        pg.goto(BASE+('' if L=='en' else L+'/')+'index.html'); pg.wait_for_timeout(900)
        fps=pg.evaluate("""()=>POIS.filter(p=>p.fp).map(p=>({id:p.id,n:p.n,z:p.z,fp:p.fp,isNew:!!(p.isNew||p.new||p.status==='new'),
            tn:(window.__tN?window.__tN(p.n):p.n), zn:(window.__tN?window.__tN(ZONES[p.z].name):ZONES[p.z].name), cont:ZONES[p.z].cont, lv:ZONES[p.z].lv, zf:ZONES[p.z].faction, zst:ZONES[p.z].status}))""")
        for f in fps:
            pg.evaluate(f"""()=>{{const s=document.getElementById('sheet');const b=document.createElement('button');b.dataset.goto='{f["id"]}';s.appendChild(b);b.click();}}""")
            pg.wait_for_timeout(120)
            f['fl']=pg.evaluate("""()=>{const h=[...document.querySelectorAll('#sheet h2')].find(x=>/flight|vol|vuelo/i.test(x.textContent)); if(!h) return [];
               const o=[]; let n=h.nextElementSibling; while(n && n.tagName!=='H2'){ if(n.matches('button.place')) o.push([n.querySelector('.pn')?.textContent, n.querySelector('.pm')?.textContent]); n=n.nextElementSibling;} return o;}""")
            f['h1']=pg.evaluate("document.querySelector('#sheet h1')?.textContent")
        out[L]=fps; print(L,len(fps),fps[0]['h1'],fps[0]['fl'][:3],flush=True)
    b.close()
json.dump(out,open(os.path.join(HERE,'fp.json'),'w'),ensure_ascii=False)
