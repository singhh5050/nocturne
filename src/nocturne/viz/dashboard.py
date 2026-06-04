"""Build a single self-contained HTML time-machine dashboard from a run bundle.

No server, no libraries, no network. Fonts + generated art are base64-embedded; the bundle is
inlined; the constellation / scrubber / charts are vanilla JS+SVG.

Motif: baroque celestial cartography (Cellarius's *Harmonia Macrocosmica*, 1660). The conceit —
"a constellation is meaning drawn from chaos." The raw stream is a field of stars; nocturne draws a
small constellation (bounded working memory) while an accumulate-everything library keeps the whole
catalog. The two-brains panel makes that literal. Art is SD-3.5 generated in the atlas style.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

ASSETS = Path(__file__).parent / "assets"
ART = Path("artifacts/art")


def _compact(bundle: dict) -> dict:
    ours = bundle["brains"]["rewrite"]
    nights = []
    for ni in ours["nights"]:
        m = ni["metrics"]
        nights.append({
            "night": ni["night"], "score": ni["score"], "best": ni["best_score"],
            "tokens": ni["tokens"], "facts": ni["facts"],
            "f1": m["f1"], "precision": m["precision"], "recall": m["recall"], "noise": m["noise_leak"],
            "memory": [{"content": it["content"], "weight": it["weight"], "tier": it["tier"],
                        "provenance": it.get("provenance", [])} for it in ni["memory"]],
            "briefing": ni.get("briefing", ""), "ledger": ni.get("ledger", []),
            "policy": ni.get("policy", []), "ops": ni.get("op_counts", {}),
        })
    brains = {}
    for arm, res in bundle["brains"].items():
        brains[arm] = {"tokens": [n["tokens"] for n in res["nights"]],
                       "facts": [n["facts"] for n in res["nights"]],
                       "f1": [n["metrics"]["f1"] for n in res["nights"]],
                       "qa": res["qa_accuracy"]}
    si = bundle.get("selfimprove", {})
    selfimp = ({"best": [n["best_score"] for n in si["self_improving"]["nights"]],
                "raw": [n["score"] for n in si["self_improving"]["nights"]],
                "static": [n["score"] for n in si["static_policy"]["nights"]]} if si else {})
    return {"persona": bundle.get("persona", ""), "engine": bundle.get("engine", "?"),
            "model": bundle.get("model", "?"), "rem_model": bundle.get("rem_model"),
            "num_nights": bundle.get("num_nights", len(nights)), "nights": nights,
            "final_policy": ours.get("final_policy", []),
            "insight_found_night": ours.get("insight_found_night"),
            "brains": brains, "selfimprove": selfimp}


def _b64_font(fn: str) -> str:
    p = ASSETS / fn
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else ""


def _font_face_css() -> str:
    faces = []
    for fam, fn, weight in [("Fraunces", "fraunces.woff2", "600"),
                            ("PlexMono", "plexmono.woff2", "500"),
                            ("PlexSans", "plexsans.woff2", "400 600")]:
        b = _b64_font(fn)
        if b:
            faces.append(f"@font-face{{font-family:'{fam}';font-weight:{weight};font-display:swap;"
                         f"src:url(data:font/woff2;base64,{b}) format('woff2');}}")
    return "\n".join(faces)


def _art_uri(name: str) -> str:
    p = ART / f"{name}.jpg"
    if not p.exists():
        return ""
    return "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()


def build(bundle: dict, out_path: Path) -> Path:
    html = (_TEMPLATE
            .replace("__FONTS__", _font_face_css())
            .replace("__NEBULA__", _art_uri("nebula"))
            .replace("__PARCH__", _art_uri("parchment"))
            .replace("__DATA__", json.dumps(_compact(bundle))))
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    return out_path


_TEMPLATE = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>nocturne — celestial time machine</title>
<style>
__FONTS__
:root{
  --bg:#070810; --panel:rgba(16,18,38,.72); --line:rgba(217,178,90,.22);
  --fg:#efe9d8; --muted:#a9a487; --faint:#76728f;
  --gold:#d9b25a; --amber:#f4b860; --cyan:#79e0d6; --rose:#e88aa8; --violet:#b59cf2; --blue:#7fa8ff;
  --serif:'Fraunces','Iowan Old Style',Georgia,serif;
  --mono:'PlexMono',ui-monospace,'SF Mono',Menlo,monospace;
  --sans:'PlexSans',ui-sans-serif,system-ui,sans-serif;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--sans);font-size:14px;line-height:1.55}
/* art = atmosphere only: a full-bleed generated nebula, dark-overlaid for legibility */
#bg{position:fixed;inset:0;z-index:-3;background:url(__NEBULA__) center/cover no-repeat;
  animation:drift 90s ease-in-out infinite alternate}
@keyframes drift{from{transform:scale(1.04) translate(-1%,-1%)}to{transform:scale(1.12) translate(2%,1.5%)}}
body::before{content:"";position:fixed;inset:0;z-index:-2;background:
  radial-gradient(1100px 640px at 50% -8%, rgba(217,178,90,.16), transparent 62%),
  linear-gradient(180deg, rgba(6,7,15,.40), rgba(5,6,12,.66) 52%, rgba(4,5,11,.82));}
#stars{position:fixed;inset:0;z-index:-1;pointer-events:none}
/* smoothness: SVG geometry + opacity transitions */
#cl-nodes circle{transition:cx .9s cubic-bezier(.3,.75,.2,1), cy .9s cubic-bezier(.3,.75,.2,1), r .5s ease, fill-opacity .6s ease}
#cl-web{transition:opacity .5s ease}
#b-ours,#b-lib{transition:opacity .45s ease}
.fade{transition:opacity .35s ease}
.gen-cur{display:inline-block;width:7px;height:1.02em;background:var(--amber);vertical-align:-2px;margin-left:1px;border-radius:1px;animation:blink 1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
.star{position:absolute;border-radius:50%;background:#fff;animation:tw var(--d) ease-in-out infinite alternate}
@keyframes tw{from{opacity:.12}to{opacity:.85}}

header{padding:46px 48px 8px;position:relative}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:3px;text-transform:uppercase;color:var(--gold)}
h1{font-family:var(--serif);font-weight:600;font-size:58px;line-height:1;letter-spacing:-.5px;margin:8px 0 0}
h1 .moon{color:var(--amber);text-shadow:0 0 28px rgba(244,184,96,.5)}
.epigraph{font-family:var(--serif);font-style:italic;font-size:21px;color:#d8cfa8;margin-top:14px;max-width:780px}
.epigraph small{display:block;font-size:13px;color:var(--faint);font-style:normal;font-family:var(--mono);letter-spacing:.5px;margin-top:6px}
.persona{color:var(--faint);font-size:13px;margin-top:10px;max-width:780px}
.badges{margin-top:14px;display:flex;gap:9px;flex-wrap:wrap}
.badge{font-family:var(--mono);font-size:11.5px;background:rgba(217,178,90,.06);border:1px solid var(--line);
  border-radius:999px;padding:5px 12px;color:var(--muted)} .badge b{color:var(--fg)}
.badge.hi{border-color:rgba(121,224,214,.5);color:var(--cyan)}

.scrub{display:flex;align-items:center;gap:16px;margin:22px 48px 6px;background:var(--panel);
  border:1px solid var(--line);border-radius:16px;padding:14px 18px;backdrop-filter:blur(8px)}
.scrub input[type=range]{flex:1;-webkit-appearance:none;height:4px;border-radius:4px;
  background:linear-gradient(90deg,var(--gold),rgba(217,178,90,.15));outline:none}
.scrub input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:18px;height:18px;border-radius:50%;
  background:var(--amber);box-shadow:0 0 14px rgba(244,184,96,.8);cursor:pointer;border:2px solid #1a1405}
button{font-family:var(--mono);font-size:13px;background:rgba(217,178,90,.06);color:var(--fg);
  border:1px solid var(--line);border-radius:10px;padding:7px 13px;cursor:pointer;transition:.15s}
button:hover{border-color:var(--gold);color:var(--amber)}
.nlabel{font-family:var(--mono);font-size:14px;color:var(--amber);min-width:118px;text-align:right;letter-spacing:.5px}
.chips{display:flex;gap:10px;flex-wrap:wrap;margin:12px 48px 4px}
.chip{font-family:var(--mono);background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:8px 13px;min-width:80px}
.chip .k{font-size:10px;letter-spacing:1.2px;text-transform:uppercase;color:var(--faint)}
.chip .v{font-size:19px;margin-top:2px} .chip .v.amber{color:var(--amber)} .chip .v.cyan{color:var(--cyan)} .chip .v.rose{color:var(--rose)}

.wrap{display:grid;grid-template-columns:1.5fr 1fr;gap:20px;padding:18px 48px 56px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:18px 20px;
  backdrop-filter:blur(10px);box-shadow:0 24px 60px rgba(0,0,0,.5);position:relative;overflow:hidden;
  opacity:0;transform:translateY(14px);animation:rise .7s cubic-bezier(.2,.7,.2,1) forwards}
.card::after{content:"";position:absolute;inset:0;background:url(__PARCH__) center/cover no-repeat;opacity:.04;pointer-events:none;mix-blend-mode:overlay}
.card>*{position:relative;z-index:1}
.card:nth-child(1){animation-delay:.05s}.card:nth-child(2){animation-delay:.12s}
.card:nth-child(3){animation-delay:.19s}.card:nth-child(4){animation-delay:.26s}
.card:nth-child(5){animation-delay:.33s}.card:nth-child(6){animation-delay:.4s}
@keyframes rise{to{opacity:1;transform:none}}
.card h2{font-family:var(--mono);margin:0 0 12px;font-size:11px;text-transform:uppercase;letter-spacing:2px;color:var(--gold)}
.full{grid-column:1/-1}
svg{display:block;width:100%}

.mem ul{padding:0;margin:0;max-height:300px;overflow:auto;list-style:none}
.mem li{padding:8px 10px;border-radius:10px;margin:4px 0;background:rgba(255,255,255,.03);display:flex;gap:10px;align-items:baseline;border:1px solid transparent;cursor:pointer;transition:.15s}
.mem li:hover{border-color:var(--line);background:rgba(217,178,90,.07)}
.w{font-family:var(--mono);font-size:12px;color:var(--faint);min-width:38px}
.tier{font-family:var(--mono);font-size:9px;text-transform:uppercase;letter-spacing:.7px;padding:2px 7px;border-radius:6px}
.tier.in_progress{background:rgba(244,184,96,.14);color:var(--amber)}
.tier.episodic{background:rgba(121,224,214,.14);color:var(--cyan)}
.tier.preferences{background:rgba(181,156,242,.16);color:var(--violet)}
.briefing{white-space:pre-wrap;background:rgba(255,255,255,.03);border:1px solid var(--line);border-radius:12px;padding:14px 16px;font-size:13.5px;max-height:220px;overflow:auto}
.hyp{padding:10px 12px;border-radius:11px;background:rgba(255,255,255,.03);margin:7px 0;border-left:3px solid var(--line)}
.hyp.confirmed{border-left-color:var(--cyan);background:rgba(121,224,214,.06)}
.hyp .meta{font-family:var(--mono);color:var(--faint);font-size:11px;margin-top:4px} .hyp.confirmed .meta{color:var(--cyan)}
.pol{padding:9px 12px;border-radius:10px;background:rgba(255,255,255,.03);margin:6px 0}
.pol.fresh{outline:1px solid var(--amber);background:rgba(244,184,96,.07)}
.pol .ln{font-family:var(--mono);color:var(--faint);font-size:11px;margin-top:3px}
.inspector{font-family:var(--mono);font-size:11.5px;color:var(--muted);border-top:1px dashed var(--line);margin-top:10px;padding-top:8px;min-height:34px}
.inspector b{color:var(--amber)}
.legend{display:flex;gap:16px;flex-wrap:wrap;color:var(--faint);font-family:var(--mono);font-size:11px;margin-top:8px}
.legend i{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px;vertical-align:middle}
/* two brains */
.brains{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.brain{border:1px solid var(--line);border-radius:16px;padding:12px;background:rgba(8,9,18,.5)}
.brain .ttl{font-family:var(--serif);font-size:17px;margin-bottom:2px}
.brain .sub{font-family:var(--mono);font-size:11px;color:var(--faint);margin-bottom:8px}
.brain.ours .ttl{color:var(--amber)} .brain.lib .ttl{color:var(--blue)}
.metaphor{font-family:var(--serif);font-style:italic;color:#d8cfa8;text-align:center;margin-top:12px;font-size:15px}
/* decision ledger */
.dec{font-family:var(--mono);font-size:12px}
.dec .row{display:flex;gap:10px;align-items:baseline;padding:5px 0;border-bottom:1px dashed rgba(217,178,90,.12)}
.dec .nn{color:var(--faint);min-width:54px} .dec .ev{color:var(--fg)}
.dec .recon{color:var(--cyan)}
.tag{display:inline-block;font-size:10px;padding:1px 6px;border-radius:5px;margin-right:4px}
.tag.add{background:rgba(244,184,96,.14);color:var(--amber)} .tag.merge{background:rgba(181,156,242,.16);color:var(--violet)}
.tag.drop{background:rgba(232,138,168,.16);color:var(--rose)} .tag.reweight{background:rgba(121,224,214,.14);color:var(--cyan)}
.charts{display:grid;grid-template-columns:1fr 1fr;gap:22px}
.chh{font-family:var(--mono);color:var(--muted);font-size:11.5px;margin-bottom:6px}
@media(max-width:1040px){.wrap,.charts,.brains{grid-template-columns:1fr}}
</style></head>
<body>
<div id="bg"></div><div id="stars"></div>
<header>
  <div class="eyebrow">harmonia macrocosmica · sleep-time compute</div>
  <h1><span class="moon">◗</span> nocturne</h1>
  <div class="epigraph">A constellation is meaning drawn from chaos.
    <small>the night sky is the raw stream · the catalog keeps every star · the mind draws the few worth steering by</small></div>
  <div class="persona" id="persona"></div>
  <div class="badges" id="badges"></div>
</header>

<div class="scrub">
  <button id="prev">◀ prev</button>
  <input type="range" id="slider" min="1" value="1"/>
  <button id="next">next ▶</button>
  <button id="play">▶ play</button>
  <span class="nlabel" id="nlabel"></span>
</div>
<div class="chips" id="chips"></div>

<div class="wrap">
  <div class="card">
    <h2>memory constellation</h2>
    <svg id="constellation" viewBox="0 0 580 380" style="height:380px"></svg>
    <div class="legend" id="legend"></div>
    <div class="inspector" id="inspector">click a star to see its provenance — why the brain believes it.</div>
  </div>
  <div class="card">
    <h2>morning briefing</h2>
    <div class="briefing" id="briefing"></div>
    <h2 style="margin-top:16px">hypothesis ledger</h2>
    <div id="ledger"></div>
  </div>

  <div class="card full">
    <h2>two brains — the constellation vs the catalog</h2>
    <div class="brains">
      <div class="brain ours">
        <div class="ttl">nocturne — the constellation</div>
        <div class="sub" id="ours-sub"></div>
        <svg id="b-ours" viewBox="0 0 460 240" style="height:240px"></svg>
      </div>
      <div class="brain lib">
        <div class="ttl">accumulation — the catalog</div>
        <div class="sub" id="lib-sub"></div>
        <svg id="b-lib" viewBox="0 0 460 240" style="height:240px"></svg>
      </div>
    </div>
    <div class="metaphor">GBrain keeps every star. nocturne draws the figure you steer by — and at night, lets the rest fade.</div>
  </div>

  <div class="card">
    <h2>bounded memory — this night</h2>
    <div class="mem"><ul id="mem"></ul></div>
  </div>
  <div class="card">
    <h2>decision ledger — what the brain did overnight</h2>
    <div class="dec" id="dec"></div>
  </div>

  <div class="card">
    <h2>policy the agent rewrote for itself</h2>
    <div id="policy"></div>
  </div>
  <div class="card">
    <h2>the evidence</h2>
    <div class="charts">
      <div><div class="chh">storage footprint — the catalog grows, the constellation holds</div>
        <svg id="ch_tokens" viewBox="0 0 460 210" style="height:210px"></svg></div>
      <div><div class="chh">self-improvement — best-so-far vs static policy</div>
        <svg id="ch_learn" viewBox="0 0 460 210" style="height:210px"></svg></div>
    </div>
  </div>
</div>

<script>
const DATA = __DATA__;
const ARMC={rewrite:"#f4b860",gbrain_accumulate:"#7fa8ff",append:"#e88aa8",window:"#79e0d6"};
const ARML={rewrite:"rewrite (ours)",gbrain_accumulate:"gbrain (retrieval)",append:"naive append",window:"window"};
const THREADS=[
  {key:"iclr",c:"#f4b860",t:s=>/review|ablation|rebuttal|iclr|camera|score/.test(s)},
  {key:"compute",c:"#7fa8ff",t:s=>/gpu|h100|2400|allocation/.test(s)},
  {key:"meeting",c:"#79e0d6",t:s=>/meeting|wednesday|thursday|11:00|14:00/.test(s)},
  {key:"memory",c:"#b59cf2",t:s=>/memory|saved|memgpt|paper|consolidat|interfer|bounded/.test(s)},
  {key:"collab",c:"#e88aa8",t:s=>/co-author|workshop|collab|okafor/.test(s)},
  {key:"other",c:"#a9a487",t:s=>true}];
function threadOf(s){s=(s||"").toLowerCase();for(const th of THREADS)if(th.t(s))return th;return THREADS[5];}
const $=id=>document.getElementById(id);
const N=DATA.nights.length;
let RECON=null; // night where lab meeting reconciled Thu->Wed
(function(){let seen14=false;for(const nt of DATA.nights){const txt=nt.memory.map(m=>m.content.toLowerCase()).join(" ");
  if(/thursday|14:00/.test(txt))seen14=true;
  if(seen14 && /wednesday|11:00/.test(txt)){RECON=nt.night;break;}}})();

// starfield
(function(){let s=9301;const r=()=>{s=(s*9301+49297)%233280;return s/233280;};let h="";
  for(let i=0;i<150;i++)h+=`<div class="star" style="left:${(r()*100).toFixed(2)}%;top:${(r()*100).toFixed(2)}%;width:${(r()*1.7+.4).toFixed(2)}px;height:${(r()*1.7+.4).toFixed(2)}px;--d:${(r()*4+2).toFixed(1)}s;animation-delay:${(r()*4).toFixed(1)}s"></div>`;
  $("stars").innerHTML=h;})();

$("persona").textContent=DATA.persona;
$("badges").innerHTML=`<span class="badge">engine <b>${DATA.engine}</b></span>`+
  `<span class="badge">bulk <b>${DATA.model}</b></span>`+(DATA.rem_model?`<span class="badge">REM <b>${DATA.rem_model}</b></span>`:"")+
  `<span class="badge"><b>${N}</b> nights · 4 arms</span>`+
  (DATA.insight_found_night?`<span class="badge hi">✦ latent insight · night ${DATA.insight_found_night}</span>`:"");

const slider=$("slider");slider.max=N;let cur=1,timer=null;
function chip(k,v,cls){return `<div class="chip"><div class="k">${k}</div><div class="v ${cls||''}">${v}</div></div>`;}
function opsGlyph(o){o=o||{};const p=[];if(o.add)p.push(`+${o.add}`);if(o.merge)p.push(`⊕${o.merge}`);if(o.reweight)p.push(`↕${o.reweight}`);if(o.drop)p.push(`−${o.drop}`);if(o.evicted)p.push(`⌫${o.evicted}`);return p.join(" ")||"·";}

function render(t){cur=t;const d=DATA.nights[t-1];$("nlabel").textContent=`night ${t} / ${N}`;slider.value=t;
  $("chips").innerHTML=chip("score",d.score.toFixed(3),"amber")+chip("best",d.best.toFixed(3),"amber")+
    chip("memory",`${d.facts}`)+chip("tokens",d.tokens)+chip("F1",d.f1.toFixed(2),"cyan")+
    chip("recall",d.recall.toFixed(2),"cyan")+chip("noise",d.noise,d.noise?"rose":"")+chip("ops",`<span style='font-size:14px'>${opsGlyph(d.ops)}</span>`);
  drawConstellation(d);drawTwoBrains(t,d);drawMemory(d);drawBriefing(d);drawLedger(d);drawPolicy(d,t);drawDecisions(t);drawCursor();}

function nodesByThread(mem){const g={};mem.forEach(it=>{const th=threadOf(it.content);(g[th.key]=g[th.key]||{th,items:[]}).items.push(it);});return g;}
const SVGNS="http://www.w3.org/2000/svg";
let CL_INIT=false, CL_WEBSIG="", CL_NODES={};
function initConstellation(){
  $("constellation").innerHTML=`<defs>
    <radialGradient id="sky" cx="50%" cy="44%" r="60%"><stop offset="0%" stop-color="rgba(40,46,92,.5)"/><stop offset="100%" stop-color="rgba(6,7,15,0)"/></radialGradient>
    <filter id="glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
    <rect width="580" height="380" fill="url(#sky)"/><g id="cl-web"></g><g id="cl-nodes"></g>`;
  CL_INIT=true;
}
function drawConstellation(d){
  if(!CL_INIT)initConstellation();
  const W=580,H=380,cx=W/2,cy=H/2;
  const groups=nodesByThread(d.memory),keys=Object.keys(groups);
  const cents=keys.map((k,i)=>{const a=(i/keys.length)*6.283-1.5708;return{key:k,c:groups[k].th.c,x:cx+Math.cos(a)*128,y:cy+Math.sin(a)*98};});
  // the faint web of cluster centres only redraws when the set of threads changes (so it never snaps mid-scrub)
  const sig=keys.join(",");
  if(sig!==CL_WEBSIG){let w="";
    for(let i=0;i<cents.length;i++){const a=cents[i],b=cents[(i+1)%cents.length];
      w+=`<line x1="${a.x.toFixed(1)}" y1="${a.y.toFixed(1)}" x2="${b.x.toFixed(1)}" y2="${b.y.toFixed(1)}" stroke="#d9b25a" stroke-opacity=".10"/>`;
      w+=`<line x1="${a.x.toFixed(1)}" y1="${a.y.toFixed(1)}" x2="${cx}" y2="${cy}" stroke="#d9b25a" stroke-opacity=".07"/>`;}
    cents.forEach(c=>{w+=`<text x="${c.x.toFixed(1)}" y="${(c.y-34).toFixed(1)}" fill="${c.c}" font-family="PlexMono,monospace" font-size="11" text-anchor="middle">${c.key}</text>`;});
    $("cl-web").innerHTML=w; CL_WEBSIG=sig;}
  // stars: persistent elements keyed by content -> CSS transitions glide them to new positions + fade in/out
  const NS=$("cl-nodes"), seen={};
  keys.forEach((k,gi)=>{const ct=cents[gi],g=groups[k];
    g.items.forEach((it,ii)=>{const a2=(ii/Math.max(1,g.items.length))*6.283,r=20+g.items.length*3.2;
      const x=ct.x+Math.cos(a2)*r, y=ct.y+Math.sin(a2)*r, rad=3.5+Math.min(11,it.weight*4.2);
      const op=(0.35+Math.min(0.6,it.weight*0.45)).toFixed(2); const key=it.content; seen[key]=1;
      let n=CL_NODES[key];
      if(!n){n=document.createElementNS(SVGNS,"circle");
        n.setAttribute("cx",x.toFixed(1));n.setAttribute("cy",y.toFixed(1));n.setAttribute("r",rad.toFixed(1));
        n.setAttribute("fill",ct.c);n.setAttribute("fill-opacity","0");n.setAttribute("filter","url(#glow)");n.style.cursor="pointer";
        n.dataset.c=it.content;n.dataset.p=(it.provenance||[]).join(", ")||"—";n.dataset.w=it.weight.toFixed(2);
        n.onclick=()=>{$("inspector").innerHTML=`<b>★</b> ${esc(n.dataset.c)} <span style="color:var(--faint)">(w=${n.dataset.w})</span><br><span style="color:var(--faint)">why:</span> from raw items [${esc(n.dataset.p)}]`;};
        NS.appendChild(n); CL_NODES[key]=n;
        requestAnimationFrame(()=>n.setAttribute("fill-opacity",op)); // fade in
      } else {n.setAttribute("cx",x.toFixed(1));n.setAttribute("cy",y.toFixed(1));n.setAttribute("r",rad.toFixed(1));
        n.setAttribute("fill",ct.c);n.setAttribute("fill-opacity",op);n.dataset.w=it.weight.toFixed(2);}});});
  Object.keys(CL_NODES).forEach(key=>{if(!seen[key]){const n=CL_NODES[key];
    n.setAttribute("fill-opacity","0");n.setAttribute("r","1");setTimeout(()=>{try{NS.removeChild(n);}catch(e){}},700);delete CL_NODES[key];}});
  $("legend").innerHTML=THREADS.slice(0,5).map(t=>`<span><i style="background:${t.c}"></i>${t.key}</span>`).join("")+(RECON&&cur>=RECON?` <span style="color:var(--cyan)">✓ reconciled night ${RECON}</span>`:"");
}

function drawTwoBrains(t,d){
  const W=460,H=240,cx=W/2,cy=H/2;
  // ours — cross-fade between configurations
  const ob=$("b-ours"); ob.style.opacity=".3";
  let so=`<rect width="${W}" height="${H}" rx="12" fill="rgba(8,9,18,.4)"/>`;
  const mem=d.memory.slice().sort((a,b)=>b.weight-a.weight).slice(0,14);
  mem.forEach((it,i)=>{const a=(i/Math.max(1,mem.length))*6.283,r=40+(i%3)*22,x=cx+Math.cos(a)*r*1.5,y=cy+Math.sin(a)*r;
    if(i>0){const a0=((i-1)/Math.max(1,mem.length))*6.283,r0=40+((i-1)%3)*22;so+=`<line x1="${(cx+Math.cos(a0)*r0*1.5).toFixed(1)}" y1="${(cy+Math.sin(a0)*r0).toFixed(1)}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" stroke="#f4b860" stroke-opacity=".3"/>`;}
    so+=`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${(3+it.weight*3).toFixed(1)}" fill="#f4b860"/>`;});
  ob.innerHTML=so; requestAnimationFrame(()=>requestAnimationFrame(()=>ob.style.opacity="1"));
  $("ours-sub").textContent=`${d.facts} stars · one figure you can hold in your head`;
  // catalog — dots fade in and STAY as the night advances (it never forgets); fade out on rewind
  const lib=DATA.brains.gbrain_accumulate, libN=lib?lib.facts[t-1]:0, target=Math.min(libN,520);
  const svg=$("b-lib");
  if(!svg._g){svg.innerHTML=`<rect width="${W}" height="${H}" rx="12" fill="rgba(8,9,18,.4)"/><g></g>`;svg._g=svg.querySelector("g");svg._dots=[];svg._s=98765;}
  const g=svg._g,dots=svg._dots,rnd=()=>{svg._s=(svg._s*9301+49297)%233280;return svg._s/233280;};
  while(dots.length<target){const c=document.createElementNS(SVGNS,"circle");
    c.setAttribute("cx",(rnd()*W).toFixed(1));c.setAttribute("cy",(rnd()*H).toFixed(1));c.setAttribute("r",(rnd()*1.3+.5).toFixed(2));
    c.setAttribute("fill","#7fa8ff");c.setAttribute("fill-opacity","0");c.style.transition="fill-opacity .6s ease";
    g.appendChild(c);dots.push(c);const o=(.3+rnd()*.5).toFixed(2);requestAnimationFrame(()=>c.setAttribute("fill-opacity",o));}
  while(dots.length>target){const c=dots.pop();c.setAttribute("fill-opacity","0");setTimeout(()=>{try{g.removeChild(c);}catch(e){}},500);}
  $("lib-sub").textContent=`${libN} pages · every star kept, none connected`;}

function drawMemory(d){const items=d.memory.slice().sort((a,b)=>b.weight-a.weight);
  fadeSwap($("mem"),items.length?items.map(it=>`<li onclick="document.getElementById('inspector').innerHTML='<b>★</b> '+this.dataset.c+' <span style=color:var(--faint)>why: ['+this.dataset.p+']</span>'" data-c="${esc(it.content)}" data-p="${esc((it.provenance||[]).join(', ')||'—')}"><span class="w">${it.weight.toFixed(2)}</span><span class="tier ${it.tier}">${it.tier.replace("_"," ")}</span><span>${esc(it.content)}</span></li>`).join(""):`<li style="color:var(--faint)">empty</li>`);}
let BRIEF_TOK=0;
function drawBriefing(d){const el=$("briefing");const full=d.briefing||"";const tok=++BRIEF_TOK;
  if(!full){el.innerHTML="<span style='color:var(--faint)'>no briefing</span>";return;}
  const words=full.split(/(\s+)/);let i=0;el.innerHTML="";
  (function step(){if(tok!==BRIEF_TOK)return;i+=2; // type it out, as if regenerating overnight
    el.innerHTML=md(words.slice(0,i).join(""))+(i<words.length?'<span class="gen-cur"></span>':'');
    el.scrollTop=el.scrollHeight;if(i<words.length)setTimeout(step,16);})();}
function fadeSwap(el,html){el.classList.add("fade");el.innerHTML=html;el.style.opacity="0";
  requestAnimationFrame(()=>requestAnimationFrame(()=>{el.style.opacity="1";}));}
function drawLedger(d){if(!d.ledger||!d.ledger.length){$("ledger").innerHTML="<span style='color:var(--faint)'>no hypotheses yet</span>";return;}
  const a=d.ledger.slice().sort((x,y)=>(y.status==="confirmed")-(x.status==="confirmed")||y.confidence-x.confidence).slice(0,4);
  fadeSwap($("ledger"),a.map(h=>`<div class="hyp ${h.status}"><div>${h.status==="confirmed"?"✦ ":""}${esc(h.statement)}</div><div class="meta">${h.status} · conf ${h.confidence.toFixed(2)}${h.confirmed_night?` · confirmed night ${h.confirmed_night}`:""}</div></div>`).join(""));}
function drawPolicy(d,t){if(!d.policy||!d.policy.length){$("policy").innerHTML="<span style='color:var(--faint)'>seed policy</span>";return;}
  fadeSwap($("policy"),d.policy.slice().sort((a,b)=>b.weight-a.weight).map(p=>`<div class="pol ${p.learned_night===t?'fresh':''}"><div>${esc(p.content)}</div><div class="ln">w=${p.weight.toFixed(2)} · learned night ${p.learned_night}${p.learned_night===t?' · NEW':''}</div></div>`).join(""));}
function drawDecisions(t){let rows="";for(let n=Math.max(1,t-6);n<=t;n++){const o=DATA.nights[n-1].ops||{};const tags=[];
  if(o.add)tags.push(`<span class="tag add">+${o.add} add</span>`);if(o.merge)tags.push(`<span class="tag merge">⊕${o.merge} merge</span>`);
  if(o.reweight)tags.push(`<span class="tag reweight">↕${o.reweight}</span>`);if(o.drop)tags.push(`<span class="tag drop">−${o.drop} drop</span>`);
  const recon=(n===RECON)?`<span class="recon">✓ resolved conflict — lab meeting Thu 14:00 → Wed 11:00</span>`:"";
  rows+=`<div class="row"><span class="nn">night ${n}</span><span class="ev">${tags.join("")||"<span style='color:var(--faint)'>·</span>"} ${recon}</span></div>`;}
  fadeSwap($("dec"),rows);}

function lineChart(id,series,opts){const svg=$(id),W=460,H=210,pad=34,xmax=opts.xmax,ymax=opts.ymax||Math.max(1,...series.flatMap(s=>s.pts));
  const X=i=>pad+(i/(xmax-1))*(W-pad-10),Y=v=>H-pad-(v/ymax)*(H-pad-14);
  let s=`<defs><filter id="cg"><feGaussianBlur stdDeviation="1.3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><rect width="${W}" height="${H}" rx="12" fill="rgba(255,255,255,.02)"/>`;
  for(let g=0;g<=4;g++){const y=(pad+(g/4)*(H-pad-14)).toFixed(1);s+=`<line x1="${pad}" y1="${y}" x2="${W-10}" y2="${y}" stroke="rgba(217,178,90,.08)"/>`;}
  series.forEach(se=>{s+=`<path d="${se.pts.map((v,i)=>`${i?'L':'M'}${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join(" ")}" fill="none" stroke="${se.c}" stroke-width="${se.w||2.4}" stroke-opacity="${se.o||1}" filter="url(#cg)"/>`;});
  s+=`<line id="${id}_cur" x1="0" y1="${pad}" x2="0" y2="${H-pad}" stroke="#d9b25a" stroke-opacity=".5" stroke-dasharray="3 4"/>`;
  series.forEach((se,i)=>{s+=`<circle cx="${pad+i*132+5}" cy="${H-12}" r="4" fill="${se.c}"/><text x="${pad+13+i*132}" y="${H-8}" fill="#a9a487" font-family="PlexMono" font-size="10">${se.name}</text>`;});
  svg.innerHTML=s;svg._X=X;}
function drawTokens(){const arms=Object.keys(DATA.brains);lineChart("ch_tokens",arms.map(a=>({name:ARML[a]||a,c:ARMC[a]||"#fff",pts:DATA.brains[a].tokens})),{xmax:N});}
function drawLearn(){const s=DATA.selfimprove;if(!s||!s.best)return;lineChart("ch_learn",[{name:"best (ours)",c:"#f4b860",pts:s.best,w:2.8},{name:"raw",c:"#f4b860",pts:s.raw,w:1.2,o:.4},{name:"static",c:"#a9a487",pts:s.static,w:2,o:.9}],{xmax:N,ymax:Math.max(.2,...s.best,...s.static,...s.raw)*1.12});}
function drawCursor(){["ch_tokens","ch_learn"].forEach(id=>{const svg=$(id);if(!svg._X)return;const x=svg._X(cur-1).toFixed(1);const c=$(id+"_cur");if(c){c.setAttribute("x1",x);c.setAttribute("x2",x);}});}

function esc(s){return(s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));}
function md(s){return esc(s).replace(/^#+\s*(.*)$/gm,'<b style="color:var(--amber);font-family:var(--serif);font-size:15px">$1</b>').replace(/\*\*(.*?)\*\*/g,'<b>$1</b>').replace(/^[-•]\s*(.*)$/gm,'• $1');}
slider.oninput=e=>render(+e.target.value);$("prev").onclick=()=>render(Math.max(1,cur-1));$("next").onclick=()=>render(Math.min(N,cur+1));
$("play").onclick=function(){if(timer){clearInterval(timer);timer=null;this.textContent="▶ play";return;}this.textContent="⏸ pause";timer=setInterval(()=>{if(cur>=N){clearInterval(timer);timer=null;$("play").textContent="▶ play";return;}render(cur+1);},1200);};
drawTokens();drawLearn();
const _h=(location.hash.match(/night=(\d+)/)||[])[1];render(_h?Math.max(1,Math.min(N,+_h)):1);
window.addEventListener("hashchange",()=>{const m=(location.hash.match(/night=(\d+)/)||[])[1];if(m)render(Math.max(1,Math.min(N,+m)));});
</script></body></html>
"""
