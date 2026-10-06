"""Reads every dungeon and raid from the live map: route from each capital (with and without flight paths),
'Getting there' card and steps from the nearest capital, in EN, FR and ES. Resumable: delete dj.json to start over."""
import os, json, re
from playwright.sync_api import sync_playwright
from urllib.parse import quote
HERE=os.path.dirname(os.path.abspath(__file__)); BASE='file://'+os.path.abspath(os.path.join(HERE,'..'))+'/'
OUT=os.path.join(HERE,'dj.json'); data=json.load(open(OUT)) if os.path.exists(OUT) else {}
CAP={'horde':['Orgrimmar','Thunder Bluff','Undercity'],'alliance':['Stormwind City','Ironforge','Darnassus']}
JS="""()=>{const q=s=>document.querySelector(s);
 const steps=[...document.querySelectorAll('ol.steps li')].map(li=>{const t=li.querySelector('.st-t');const m=li.querySelector('.st-m');
   const title=t?[...t.childNodes].filter(n=>n!==m).map(n=>n.textContent).join('').trim():'';const s=li.querySelector('.st-s');
   return {t:title,m:m?m.textContent.trim():'',s:s?[...s.childNodes].map(n=>n.textContent.trim()).filter(Boolean).join(' · '):'',w:[...li.querySelectorAll('.warn')].map(w=>w.textContent.trim()),end:li.classList.contains('end')};});
 const jr=q('.jr'); let card=null;
 if(jr){const r=jr.querySelector('.risk'); card={cls:r?[...r.classList].filter(c=>c!=='risk')[0]||'':'',risk:r?r.textContent.trim():'',items:[...jr.querySelectorAll('li')].map(l=>l.textContent.trim()),
   tip:(jr.querySelector('.jr-tip')||{}).textContent||'',facts:[...jr.querySelectorAll('.dj-facts span')].map(x=>x.textContent.trim()),
   ps:[...jr.querySelectorAll('p')].filter(p=>!p.classList.contains('jr-tip')).map(p=>p.textContent.trim())};}
 return {eta:q('.eta-n')?.textContent.trim()||null,steps,card};}"""
def speed(lv): return 'foot' if lv[0]<40 else ('m60' if lv[0]<60 else 'm100')
def mins(e): m=re.search(r'(\d+)\s*min',e or ''); return int(m.group(1)) if m else 9999
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1440,'height':900})
    pg.route('**/*',lambda r: r.abort() if r.request.url.startswith('http') else r.continue_())
    def run(L,a,c,f,by,fp):
        pg.goto(BASE+('' if L=='en' else L+'/')+'index.html'+f'#from={quote(a)}&to={quote(c)}&f={f}&by={by}'+('&fp=1' if fp else '')); pg.reload(); pg.wait_for_timeout(450)
        return pg.evaluate(JS)
    pg.goto(BASE+'index.html'); pg.wait_for_timeout(700)
    DJ=pg.evaluate("""()=>POIS.filter(p=>p.t==='dungeon'||p.t==='raid').map(p=>({id:p.id,n:p.n,t:p.t,z:p.z,lv:p.lv,isNew:!!p.isNew,d:p.d||'',zone:ZONES[p.z].name,cont:ZONES[p.z].cont}))""")
    names={}
    for L in ['fr','es']:
        pg.goto(BASE+L+'/index.html'); pg.wait_for_timeout(700)
        names[L]=pg.evaluate("(a)=>a.map(d=>[window.__tN(d.n),window.__tN(d.zone),window.__tr?window.__tr(d.d):d.d])",DJ)
    for i,d in enumerate(DJ):
        if d['n'] in data: continue
        sp=speed(d['lv']); rec=dict(d); rec['speed']=sp; rec['fr']={'n':names['fr'][i][0],'zone':names['fr'][i][1],'d':names['fr'][i][2]}; rec['es']={'n':names['es'][i][0],'zone':names['es'][i][1],'d':names['es'][i][2]}
        rec['times']={}
        for f,caps in CAP.items():
            for c in caps:
                fl=run('en',c,d['n'],f,sp,True); nf=run('en',c,d['n'],f,sp,False)
                rec['times'][c]={'f':f,'fly':mins(fl['eta']),'foot':mins(nf['eta'])}
            best=min(caps,key=lambda c:rec['times'][c]['fly']); rec['best_'+f]=best
            for L in ['en','fr','es']: rec.setdefault('route_'+f,{})[L]=run(L,best,d['n'],f,sp,True)
        data[d['n']]=rec; json.dump(data,open(OUT,'w'),ensure_ascii=False); print(len(data),d['n'],{c:v['fly'] for c,v in rec['times'].items()},flush=True)
    b.close()
print('done',len(data))
