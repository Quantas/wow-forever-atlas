"""Builds the static SEO pages of wow-travelcraft.com (routes hub, one page per trip, flight paths)
from data.json and fp.json (made by extract.py and extract_fp.py from the live map). Run: python3 build.py <site folder>"""
import json, re, os, sys, html
from urllib.parse import quote
HERE=os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE,'pairs.py')).read()); exec(open(os.path.join(HERE,'l10n.py')).read())
SITE=sys.argv[1] if len(sys.argv)>1 else os.path.join(HERE,'..')
D=json.load(open(os.path.join(HERE,'data.json'))); FP=json.load(open(os.path.join(HERE,'fp.json')))
DOM='https://wow-travelcraft.com'; KOFI='https://ko-fi.com/fistao'; ADDON='https://www.curseforge.com/wow/addons/travelcraft'
LANGS=['en','fr','es']; e=lambda s: html.escape(str(s),quote=True)
def mins(eta):
    m=re.search(r'(\d+)\s*min',eta or ''); h=re.search(r'(\d+)\s*h',eta or '')
    return (int(h.group(1))*60 if h else 0)+(int(m.group(1)) if m else 0)
def fmt(n): return f"{n} min" if n<60 else f"{n//60} h {n%60:02d}"
CONF_RE={'en':r'(Official|Reported|To confirm|Classic)$','fr':r'(Officiel|Signalé|À confirmer|Classic)$','es':r'(Oficial|Reportado|Por confirmar|Classic)$'}
def fix_sub(L,s): return re.sub(r'(\S)'+CONF_RE[L],r'\1 · \2',s)
TRANSPORT=re.compile(r'\b(ship|zeppelin|tram|portal|airship|skyship|boat|bateau|zeppelin|tram|portail|dirigeable|vaisseau|barco|zepelín|tren|portal|dirigible|nave)\b',re.I)
def url(L,kind,slug=None):
    t=T[L]; base={'home':t['home'],'routes':t['routes'],'flights':t['flights']}[kind]
    return base+(slug+'/' if slug else '')
CSS='''
:root{--bg:#0a1422;--surface:#0f1c2f;--surface-2:#15253b;--line:#22354f;--line-2:#2f4766;--text:#e7eef8;--soft:#c9d6e8;--muted:#8da2bd;--accent:#3d9bff;--accent-ink:#06121f;--gold:#e0b95a;--horde:#e2665a;--alliance:#3d9bff;--both:#3fb27a;--get:#2fa56a;--kofi:#e0607e}
@media (prefers-color-scheme: light){:root{--bg:#eef2f7;--surface:#ffffff;--surface-2:#f3f6fa;--line:#d5dde8;--line-2:#b9c6d6;--text:#0e1a2b;--soft:#2b3d55;--muted:#566a84;--accent:#1769d1;--accent-ink:#ffffff;--gold:#8a6410;--horde:#c23b2e;--alliance:#1769d1;--both:#1f8a57;--get:#1f8a57;--kofi:#c8456a}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.6 "Hanken Grotesk",system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
a{color:var(--accent)}
.hd{display:flex;align-items:center;gap:14px 20px;flex-wrap:wrap;padding:12px 28px;border-bottom:1px solid var(--line);background:var(--surface)}
.brand{display:flex;align-items:center;gap:10px;color:var(--text);text-decoration:none;font-weight:700;font-size:18px}
.nav{display:flex;gap:6px 20px;font-size:14.5px;flex-wrap:wrap}
.nav a{color:var(--text);text-decoration:none}.nav a:hover{color:var(--accent)}.nav a[aria-current]{font-weight:700}
.hr{margin-left:auto;display:flex;gap:10px;align-items:center}
.kofi{background:var(--kofi);color:#fff;text-decoration:none;font-weight:600;font-size:14px;padding:8px 14px;border-radius:8px}
.langs{display:flex;border:1px solid var(--line-2);border-radius:10px;overflow:hidden}
.langs a{padding:6px 10px;font-size:13px;font-weight:600;color:var(--muted);text-decoration:none}.langs a[aria-current]{background:var(--surface-2);color:var(--text)}
main{max-width:1120px;margin:0 auto;padding:26px 28px 60px}
.crumb{font-size:13.5px;color:var(--muted);margin-bottom:14px}.crumb a{color:var(--muted)}
h1{font-size:36px;line-height:1.15;letter-spacing:-.015em;margin:0 0 12px}
h2{font-size:22px;margin:0 0 10px}
.lead{font-size:18px;color:var(--soft);margin:0 0 6px;max-width:64ch}.lead strong{color:var(--text)}
.muted{color:var(--muted)}
.btn{display:inline-block;background:var(--accent);color:var(--accent-ink);font-weight:700;text-decoration:none;padding:12px 18px;border-radius:10px;font-size:15px}
.chip{display:inline-flex;align-items:center;padding:10px 14px;border:1px solid var(--line-2);border-radius:999px;color:var(--text);text-decoration:none;font-size:14px;background:var(--surface)}
.row{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:14px 0 0}
.grid{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:40px;margin-top:8px}
.col{display:flex;flex-direction:column;gap:30px;min-width:0}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px}
.times{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px}
.time{padding:14px}.time .l{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:600}
.time .v{font-size:26px;font-weight:700;margin-top:4px}.time .s{font-size:13px;color:var(--muted)}
.time.best{border-color:var(--accent)}.time.best .l{color:var(--accent)}
ol.steps{list-style:none;margin:0;padding:0;counter-reset:st}
ol.steps li{display:grid;grid-template-columns:28px minmax(0,1fr) auto;gap:14px;padding:14px 0;border-top:1px solid var(--line);counter-increment:st}
ol.steps li::before{content:counter(st);width:26px;height:26px;border-radius:50%;border:1px solid var(--line-2);background:var(--surface-2);font-size:12px;font-weight:600;display:flex;align-items:center;justify-content:center}
ol.steps li.end::before{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.st{font-weight:600}.ss{color:var(--muted);font-size:14px}.sm{color:var(--soft);font-size:14px;white-space:nowrap}
.warn{display:block;color:var(--horde);font-size:13.5px;margin-top:4px}
.box{padding:18px 20px}.box p{margin:6px 0 0;color:var(--soft)}
.faq dt{font-weight:600;margin-top:14px}.faq dd{margin:4px 0 0;color:var(--soft)}
aside{display:flex;flex-direction:column;gap:18px}
.side{padding:18px}.side .k{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:600;margin-bottom:8px}
.side ul{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:9px;font-size:15px}
.side p{margin:0 0 8px;color:var(--soft);font-size:14.5px}
.get{color:var(--get);font-weight:600}
table{width:100%;border-collapse:collapse;font-size:15px}
th,td{text-align:left;padding:12px 16px;border-top:1px solid var(--line)}
th{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:600;border-top:0}
td.n,th.n{white-space:nowrap;width:150px}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:8px;vertical-align:1px}
.new{display:inline-block;font-size:11px;font-weight:600;color:var(--gold);border:1px solid var(--gold);border-radius:4px;padding:0 5px;margin-left:8px;vertical-align:2px;line-height:1.6}
.narrow{max-width:960px}
section{display:flex;flex-direction:column;gap:12px}
.zone{display:grid;grid-template-columns:210px minmax(0,1fr);gap:14px;padding:14px 18px;border-top:1px solid var(--line)}
.zone:first-child{border-top:0}
.zn{font-weight:600}.zl{font-size:13px;color:var(--muted)}
.fms{display:flex;flex-direction:column;gap:8px}
details.fm{border:1px solid var(--line-2);border-radius:10px;background:var(--surface-2)}
details.fm>summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:8px;padding:9px 12px;font-weight:600;font-size:15px}
details.fm>summary::-webkit-details-marker{display:none}
details.fm>summary .ft{margin-left:auto;font-size:12.5px;font-weight:600;color:var(--muted)}
details.fm .fl{padding:2px 12px 10px;font-size:14px;color:var(--soft);display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:2px 18px}
details.fm .fl span{display:flex;justify-content:space-between;gap:10px;border-bottom:1px dashed var(--line)}
details.fm .fl em{font-style:normal;color:var(--muted)}
details.fm .note{padding:2px 12px 12px;font-size:14px;color:var(--soft)}
details.fm.f-horde{border-left:3px solid var(--horde)}details.fm.f-alliance{border-left:3px solid var(--alliance)}details.fm.f-both{border-left:3px solid var(--both)}
details.fm>summary::after{content:"+";color:var(--muted);font-weight:700;margin-left:10px;width:12px;text-align:center}details.fm[open]>summary::after{content:"−"}
.filter{display:inline-flex;border:1px solid var(--line-2);border-radius:10px;padding:3px;background:var(--surface)}
.filter button{border:0;border-radius:8px;padding:8px 16px;font:inherit;font-size:14.5px;background:transparent;color:var(--soft);cursor:pointer}
.filter button[aria-pressed=true]{background:var(--accent);color:var(--accent-ink);font-weight:700}
.conf{display:inline-block;font-size:11.5px;font-weight:600;color:var(--muted);border:1px solid var(--line-2);border-radius:4px;padding:0 5px;margin-right:6px}
footer{border-top:1px solid var(--line);padding:22px 28px 30px;color:var(--muted);font-size:13.5px;display:flex;flex-wrap:wrap;gap:8px 20px;justify-content:center;text-align:center}
footer a{color:var(--muted)}
@media (max-width:900px){.grid{grid-template-columns:1fr}}
@media (max-width:640px){.hd{padding:10px 14px}.nav{order:3;width:100%;overflow-x:auto;flex-wrap:nowrap;gap:18px;padding-bottom:2px}.nav a{white-space:nowrap}
 main{padding:18px 16px 44px}h1{font-size:27px}.lead{font-size:16px}.kofi{padding:7px 10px;font-size:13px}
 .zone{grid-template-columns:minmax(0,1fr);gap:8px} details.fm>summary{flex-wrap:wrap;row-gap:2px}td.n,th.n{width:auto}th,td{padding:11px 12px}ol.steps li{grid-template-columns:28px minmax(0,1fr)}.sm{grid-column:2}}
'''
LOGO='<svg width="30" height="30" viewBox="0 0 32 32" aria-hidden="true"><rect x="1" y="1" width="30" height="30" rx="7.5" fill="#0f1c2f" stroke="#2f4766" stroke-width="1.5"/><path d="M8.5 22.5C13 23.5 11.8 16.5 16 16.3 20.3 16.1 18.8 11.4 23 9.8" fill="none" stroke="#e0b95a" stroke-width="2" stroke-dasharray="2.5 2.5" stroke-linecap="round"/><circle cx="8.5" cy="22.5" r="2.2" fill="#3fb27a"/><circle cx="23" cy="9.8" r="2.6" fill="#3d9bff"/></svg>'
def head(L,title,desc,path_by_lang,jsonld,ogtype='article'):
    alts=''.join(f'<link rel="alternate" hreflang="{x}" href="{DOM}{path_by_lang[x]}">' for x in LANGS)+f'<link rel="alternate" hreflang="x-default" href="{DOM}{path_by_lang["en"]}">'
    return (f'<!doctype html>\n<html lang="{L}"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
      f'<title>{e(title)}</title>\n<meta name="description" content="{e(desc)}">\n<link rel="canonical" href="{DOM}{path_by_lang[L]}">\n{alts}\n'
      f'<meta property="og:type" content="{ogtype}"><meta property="og:site_name" content="Travelcraft"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{DOM}{path_by_lang[L]}"><meta property="og:locale" content="{T[L]["locale"]}"><meta property="og:image" content="{DOM}/share.png">\n'
      f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}"><meta name="twitter:image" content="{DOM}/share.png">\n'
      '<link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="icon" href="/icon-192.png" type="image/png" sizes="192x192"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
      '<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;600;700&display=swap" rel="stylesheet">\n'
      + ''.join(f'<script type="application/ld+json">{json.dumps(j,ensure_ascii=False)}</script>\n' for j in jsonld) + f'<style>{CSS}</style>\n</head>\n<body>\n')
def header(L,cur,path_by_lang):
    t=T[L]; links=[(t['home'],t['nav'][0],'map'),(t['routes'],t['nav'][1],'routes'),(t['flights'],t['nav'][2],'flights'),(t['guide'],t['nav'][3],'guide'),(t['addons'],t['nav'][4],'addons')]
    nav=''.join(f'<a href="{h}"'+(' aria-current="page"' if k==cur else '')+f'>{e(n)}</a>' for h,n,k in links)
    langs=''.join(f'<a href="{path_by_lang[x]}" hreflang="{x}" lang="{x}"'+(' aria-current="true"' if x==L else '')+f'>{x.upper()}</a>' for x in LANGS)
    return (f'<header class="hd"><a class="brand" href="{t["home"]}">{LOGO}Travelcraft</a><nav class="nav" aria-label="Travelcraft">{nav}</nav>'
            f'<div class="hr"><a class="kofi" href="{KOFI}" target="_blank" rel="noopener" data-goatcounter-click="kofi-seo-header">{e(t["support"])}</a><nav class="langs" aria-label="Language">{langs}</nav></div></header>\n')
def footer(L):
    t=T[L]
    return (f'<footer><span>{e(t["footer"])}</span><a href="{t["home"]}">{e(t["nav"][0])}</a><a href="{t["routes"]}">{e(t["nav"][1])}</a><a href="{t["flights"]}">{e(t["nav"][2])}</a>'
            f'<a href="{t["guide"]}">{e(t["nav"][3])}</a><a href="{t["addons"]}">{e(t["nav"][4])}</a><a href="{KOFI}" target="_blank" rel="noopener">{e(t["kofi"])}</a></footer>\n'
            '<script data-goatcounter="https://benjamhu.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>\n</body></html>\n')
def crumbs(L,items):
    li=[{"@type":"ListItem","position":i+1,"name":n,"item":DOM+u} for i,(n,u) in enumerate(items)]
    vis=' › '.join((f'<a href="{u}">{e(n)}</a>' if i<len(items)-1 else e(n)) for i,(n,u) in enumerate(items))
    return {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":li}, f'<nav class="crumb" aria-label="Breadcrumb">{vis}</nav>'
def steps_html(L,steps):
    out=[]
    for s in steps:
        w=''.join(f'<span class="warn">{e(x)}</span>' for x in s['w'])
        out.append(f'<li class="{"end" if s["end"] else ""}"><div><div class="st">{e(s["t"])}</div><div class="ss">{e(fix_sub(L,s["s"]))}</div>{w}</div><div class="sm">{e(s["m"])}</div></li>')
    return '<ol class="steps">'+''.join(out)+'</ol>'
def maplink(L,a,b,f,fp=False): return T[L]['home']+f'#from={quote(a)}&amp;to={quote(b)}&amp;f={f}'+('&amp;by=m100&amp;fp=1' if fp else '')
def write(rel,content):
    p=os.path.join(SITE,rel.lstrip('/')); 
    if p.endswith('/'): p+='index.html'
    os.makedirs(os.path.dirname(p),exist_ok=True); open(p,'w',encoding='utf-8').write(content)
pages=[]
# ---------- route pages ----------
for slug,a,b,f,g in PAIRS:
    d=D[slug]; en=d['en']; ft=mins(en['foot']['eta']); fl=mins(en['fly']['eta'])
    tv=[mins(en[k]['eta']) for k in ['foot','form','m60','m100']]+[fl]
    rft=mins(en['rev_foot']['eta']); rfl=mins(en['rev_fly']['eta'])
    paths={L:url(L,'routes',slug) for L in LANGS}; pages.append(('route',slug,paths))
    for L in LANGS:
        t=T[L]; ld=d[L] if L!='en' else en
        foot,fly,oth=ld['foot'],ld['fly'],ld['other']
        title=t['title'](a,b); h1=t['h1'](a,b); desc=t['desc'](a,b,fmt(fl),fmt(ft))
        lead=(t['lead_fly'](fmt(fl),fmt(ft)) if fl<ft else t['lead_same'](fmt(ft)))+' '+t['lead_fac'][f]
        tr=[s['t'] for s,se in zip(foot['steps'],en['foot']['steps']) if TRANSPORT.search(se['t'])]
        a_tr=t['a_transport_yes'](tr) if tr else t['a_transport_no']
        ows=[]; [ows.append(w) for s in oth['steps'] for w in s['w'] if w not in ows]
        oft=mins(en['other']['eta'])
        faq=[(t['q_transport'],a_tr),(t['q_other'][f],t['a_other'](fmt(oft),ows[:2])),(t['q_times'],t['a_times'])]
        bc,bch=crumbs(L,[(t['crumb_home'],t['home']),(t['crumb_routes'],t['routes']),(pair_label(L,a,b),paths[L])])
        faqld={"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":an}} for q,an in faq]}
        times=''.join(f'<div class="card time{" best" if i==4 and fl<ft else ""}"><div class="l">{e(t["modes"][i])}</div><div class="v">{fmt(v)}</div><div class="s">{e(t["mode_sub"][i])}</div></div>' for i,v in enumerate(tv))
        fly_block=''
        if fl<ft and [s['t'] for s in fly['steps']]!=[s['t'] for s in foot['steps']]:
            fly_block=f'<section><h2>{e(t["fly_h"])}</h2><p class="muted" style="margin:0">{e(t["fly_sub"])}</p>{steps_html(L,fly["steps"])}</section>'
        rel=[p for p in PAIRS if p[0]!=slug and p[3]==f][:4]
        rel_html=''.join(f'<li><a href="{url(L,"routes",p[0])}">{e(pair_label(L,p[1],p[2]))}</a></li>' for p in rel)
        body=(header(L,'routes',paths)+f'<main>{bch}<h1>{e(h1)}</h1><p class="lead">{lead}</p>'
          f'<div class="row"><a class="btn" href="{maplink(L,a,b,f)}" data-goatcounter-click="seo-open-map">{e(t["open_map"])}</a></div>'
          f'<div class="grid"><div class="col"><section aria-label="{e(t["modes"][0])}"><div class="times">{times}</div></section>'
          f'<section><h2>{e(t["steps_h"])}</h2><p class="muted" style="margin:0">{e(t["steps_sub"])}</p>{steps_html(L,foot["steps"])}</section>'
          f'{fly_block}'
          f'<section class="card box"><h2 style="font-size:18px;margin:0">{e(t["back_h"])}</h2><p>{e(t["back"](b,a,fmt(rfl),fmt(rft)))}</p><p><a href="{maplink(L,b,a,f)}">{e(t["back_link"])}</a></p></section>'
          f'<section><h2>{e(t["faq_h"])}</h2><dl class="faq">'+''.join(f'<dt>{e(q)}</dt><dd>{e(an)}</dd>' for q,an in faq)+'</dl></section></div>'
          f'<aside><div class="card side"><div class="k">{e(t["others_h"](f))}</div><ul>{rel_html}<li><a class="muted" href="{t["routes"]}">{e(t["all_routes"])}</a></li></ul></div>'
          f'<div class="card side"><div class="k">{e(t["plan_h"])}</div><p>{e(t["plan_t"])}</p><a href="{t["home"]}">{e(t["open_map_short"])}</a></div>'
          f'<div class="card side"><div class="k">{e(t["addon_h"])}</div><p>{e(t["addon_t"])}</p><a class="get" href="{t["addons"]}">{e(t["addon_l"])}</a></div></aside></div></main>\n'+footer(L))
        write(paths[L],head(L,title,desc,paths,[bc,faqld])+body)
# ---------- routes hub ----------
hpaths={L:url(L,'routes') for L in LANGS}; pages.append(('hub','',hpaths))
COL={'horde':'var(--horde)','alliance':'var(--alliance)','neutral':'var(--both)','new':'var(--gold)'}
for L in LANGS:
    t=T[L]; bc,bch=crumbs(L,[(t['crumb_home'],t['home']),(t['crumb_routes'],t['routes'])])
    secs=''
    for g in ['horde','alliance','neutral','new']:
        rows=''.join(f'<tr><td><a href="{url(L,"routes",s)}">{e(pair_label(L,a,b))}</a>'+(f'<span class="new">{e(t["new"])}</span>' if g=="new" else '')+f'</td><td class="n">{fmt(mins(D[s]["en"]["fly"]["eta"]))}</td><td class="n">{fmt(mins(D[s]["en"]["foot"]["eta"]))}</td></tr>' for s,a,b,f,gg in PAIRS if gg==g)
        secs+=f'<section><h2><span class="dot" style="background:{COL[g]}"></span>{e(t["groups"][g])}</h2><div class="card" style="overflow-x:auto"><table><thead><tr><th>{e(t["th"][0])}</th><th class="n">{e(t["th"][1])}</th><th class="n">{e(t["th"][2])}</th></tr></thead><tbody>{rows}</tbody></table></div></section>'
    il={"@context":"https://schema.org","@type":"ItemList","itemListElement":[{"@type":"ListItem","position":i+1,"url":DOM+url(L,'routes',s),"name":pair_label(L,a,b)} for i,(s,a,b,f,g) in enumerate(PAIRS)]}
    body=(header(L,'routes',hpaths)+f'<main class="narrow">{bch}<h1>{e(t["hub_h1"])}</h1><p class="lead">{e(t["hub_lead"])}</p><div style="display:flex;flex-direction:column;gap:28px;margin-top:22px">{secs}'
          f'<p class="muted" style="margin:0;font-size:14px">{e(t["hub_note"])} <a href="{t["home"]}">{e(t["hub_note_l"])}</a>.</p></div></main>\n'+footer(L))
    write(hpaths[L],head(L,t['hub_title'],t['hub_desc'],hpaths,[bc,il],'website')+body)
# ---------- flight paths ----------
fpaths={L:url(L,'flights') for L in LANGS}; pages.append(('flights','',fpaths))
for L in LANGS:
    t=T[L]; items=FP[L]; bc,bch=crumbs(L,[(t['crumb_home'],t['home']),(t['crumb_flights'],t['flights'])])
    conts={}
    for it in items: conts.setdefault(it['cont'],{}).setdefault(it['z'],[]).append(it)
    secs=''
    for cont in ['Kalimdor','Eastern Kingdoms']:
        zones=sorted(conts.get(cont,{}).items(),key=lambda kv:(kv[1][0]['lv'][0],kv[1][0]['zn']))
        cname={'en':{'Kalimdor':'Kalimdor','Eastern Kingdoms':'Eastern Kingdoms'},'fr':{'Kalimdor':'Kalimdor','Eastern Kingdoms':"Royaumes de l'Est"},'es':{'Kalimdor':'Kalimdor','Eastern Kingdoms':'Reinos del Este'}}[L][cont]
        rows=''
        for z,fms in zones:
            z0=fms[0]; lv=z0['lv']; lvt=f"{t['level']} {lv[0]}–{lv[1]}" if lv[0]!=lv[1] else f"{t['level']} {lv[0]}"
            znew=f'<span class="new">{e(t["new"])}</span>' if z0['zst']=='new' else ''
            cards=''
            for m in fms:
                nw=f'<span class="new">{e(t["new"])}</span>' if m['isNew'] else ''
                if m['fl']: inner='<div class="fl">'+''.join(f'<span>{e(n)}<em>{e(tm)}</em></span>' for n,tm in m['fl'])+'</div>'
                else:
                    lead=m.get('lead') or ''; tag=''
                    for k in ['Reported','To confirm']:
                        v=t['conf'][k]
                        if lead.startswith(v+' '): tag=f'<span class="conf">{e(v)}</span>'; lead=lead[len(v)+1:]
                    inner=f'<div class="note">{tag}{e(lead)}</div>'
                cards+=f'<details class="fm f-{m["fp"]}" data-f="{m["fp"]}"><summary>{e(m["tn"])}{nw}<span class="ft">{e(t["fp_f"][m["fp"]])}</span></summary>{inner}</details>'
            rows+=f'<div class="zone"><div><div class="zn">{e(z0["zn"])}{znew}</div><div class="zl">{e(lvt)}</div></div><div class="fms">{cards}</div></div>'
        secs+=f'<section><h2>{e(cname)}</h2><div class="card">{rows}</div></section>'
    faq=t['fp_faq']; faqld={"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":an}} for q,an in faq]}
    filt=(f'<div class="row" style="margin:18px 0 6px"><div class="filter" role="group" aria-label="{e(t["fp_all"])}"><button type="button" data-fs="all" aria-pressed="true">{e(t["fp_all"])}</button>'
          f'<button type="button" data-fs="horde" aria-pressed="false">{e(t["fp_f"]["horde"])}</button><button type="button" data-fs="alliance" aria-pressed="false">{e(t["fp_f"]["alliance"])}</button></div>'
          f'<span class="muted" style="font-size:13.5px">{e(t["fp_key"])}</span></div>')
    js=('<script>document.querySelectorAll("[data-fs]").forEach(function(b){b.addEventListener("click",function(){var f=b.dataset.fs;'
        'document.querySelectorAll("[data-fs]").forEach(function(x){x.setAttribute("aria-pressed",x===b?"true":"false")});'
        'document.querySelectorAll("details.fm").forEach(function(d){d.hidden=!(f==="all"||d.dataset.f===f||d.dataset.f==="both")});'
        'document.querySelectorAll(".zone").forEach(function(z){z.hidden=![].some.call(z.querySelectorAll("details.fm"),function(d){return !d.hidden})});});});</script>\n')
    body=(header(L,'flights',fpaths)+f'<main class="narrow">{bch}<h1>{e(t["fp_h1"])}</h1><p class="lead">{e(t["fp_lead"])}</p>{filt}<div style="display:flex;flex-direction:column;gap:28px;margin-top:14px">{secs}'
          f'<section><h2>{e(T[L]["faq_h"])}</h2><dl class="faq">'+''.join(f'<dt>{e(q)}</dt><dd>{e(an)}</dd>' for q,an in faq)+'</dl></section></div></main>\n'+js+footer(L))
    write(fpaths[L],head(L,t['fp_title'],t['fp_desc'],fpaths,[bc,faqld],'website')+body)
json.dump(pages,open(os.path.join(HERE,'pages.json'),'w'))
print('pages written:',sum(1 for _ in pages)*3)
