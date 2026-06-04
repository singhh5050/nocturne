"""Build a single self-contained HTML time-machine dashboard from a run bundle.

No server, no external libraries, no network. Fonts are vendored (OFL) and base64-embedded, the
bundle is inlined, and the constellation / scrubber / charts are drawn in-page with vanilla JS+SVG.
Open artifacts/dashboard.html in any browser.

Design follows Anthropic's frontend-design skill: distinctive type (Fraunces + IBM Plex), a
dominant night palette with sharp moonlight/cyan accents, orchestrated staggered motion, and an
atmospheric "observatory" background — not a generic dark dashboard.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

ASSETS = Path(__file__).parent / "assets"


def _compact(bundle: dict) -> dict:
    ours = bundle["brains"]["rewrite"]
    nights = []
    for ni in ours["nights"]:
        m = ni["metrics"]
        nights.append({
            "night": ni["night"], "score": ni["score"], "best": ni["best_score"],
            "tokens": ni["tokens"], "facts": ni["facts"],
            "f1": m["f1"], "precision": m["precision"], "recall": m["recall"],
            "noise": m["noise_leak"],
            "memory": [{"content": it["content"], "weight": it["weight"],
                        "tier": it["tier"], "provenance": it.get("provenance", [])}
                       for it in ni["memory"]],
            "briefing": ni.get("briefing", ""),
            "ledger": ni.get("ledger", []),
            "policy": ni.get("policy", []),
            "ops": ni.get("op_counts", {}),
        })
    brains = {}
    for arm, res in bundle["brains"].items():
        brains[arm] = {
            "tokens": [n["tokens"] for n in res["nights"]],
            "f1": [n["metrics"]["f1"] for n in res["nights"]],
            "qa": res["qa_accuracy"],
        }
    si = bundle.get("selfimprove", {})
    selfimp = {}
    if si:
        selfimp = {
            "best": [n["best_score"] for n in si["self_improving"]["nights"]],
            "raw": [n["score"] for n in si["self_improving"]["nights"]],
            "static": [n["score"] for n in si["static_policy"]["nights"]],
        }
    return {
        "persona": bundle.get("persona", ""),
        "engine": bundle.get("engine", "?"),
        "model": bundle.get("model", "?"),
        "num_nights": bundle.get("num_nights", len(nights)),
        "nights": nights,
        "final_policy": ours.get("final_policy", []),
        "insight_found_night": ours.get("insight_found_night"),
        "brains": brains,
        "selfimprove": selfimp,
    }


def _font_face_css() -> str:
    faces = []
    spec = [("Fraunces", "fraunces.woff2", "600"),
            ("PlexMono", "plexmono.woff2", "500"),
            ("PlexSans", "plexsans.woff2", "400 600")]
    for fam, fn, weight in spec:
        p = ASSETS / fn
        if not p.exists():
            continue
        b64 = base64.b64encode(p.read_bytes()).decode()
        faces.append(
            f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{weight};"
            f"font-display:swap;src:url(data:font/woff2;base64,{b64}) format('woff2');}}")
    return "\n".join(faces)


def build(bundle: dict, out_path: Path) -> Path:
    data = _compact(bundle)
    html = (_TEMPLATE
            .replace("__FONTS__", _font_face_css())
            .replace("__DATA__", json.dumps(data)))
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    return out_path


_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>nocturne — time machine</title>
<style>
__FONTS__
:root{
  --bg:#06070f; --ink:#0b0d1c;
  --fg:#edeaf7; --muted:#9aa0c6; --faint:#6b6f93;
  --amber:#f4b860; --cyan:#79e0d6; --rose:#e88aa8; --violet:#b59cf2; --blue:#7fa8ff;
  --line:rgba(255,255,255,.09); --panel:rgba(18,21,42,.62);
  --serif:'Fraunces','Iowan Old Style',Georgia,serif;
  --mono:'PlexMono',ui-monospace,'SF Mono',Menlo,monospace;
  --sans:'PlexSans',ui-sans-serif,system-ui,-apple-system,sans-serif;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--sans);font-size:14px;line-height:1.55}
/* atmosphere: layered moonlight + film grain */
body::before{content:"";position:fixed;inset:0;z-index:-3;
  background:
    radial-gradient(1100px 540px at 78% -12%, rgba(244,184,96,.16), transparent 60%),
    radial-gradient(900px 700px at 12% 8%, rgba(127,168,255,.12), transparent 55%),
    radial-gradient(1200px 900px at 50% 120%, rgba(121,224,214,.07), transparent 60%),
    linear-gradient(180deg,#070811 0%, #06070f 60%, #04050b 100%);}
body::after{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;opacity:.045;mix-blend-mode:overlay;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='2'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");}
#stars{position:fixed;inset:0;z-index:-2;pointer-events:none}
.star{position:absolute;border-radius:50%;background:#fff;animation:tw var(--d) ease-in-out infinite alternate}
@keyframes tw{from{opacity:.15}to{opacity:.9}}

header{padding:46px 48px 8px;position:relative}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:3px;text-transform:uppercase;color:var(--amber);opacity:.9}
h1{font-family:var(--serif);font-weight:600;font-size:56px;line-height:1;letter-spacing:-.5px;margin:8px 0 0}
h1 .moon{color:var(--amber);text-shadow:0 0 26px rgba(244,184,96,.5)}
.tag{font-family:var(--serif);font-style:italic;font-size:19px;color:var(--muted);margin-top:12px;max-width:760px}
.persona{color:var(--faint);font-size:13px;margin-top:8px;max-width:760px}
.badges{margin-top:16px;display:flex;gap:9px;flex-wrap:wrap}
.badge{font-family:var(--mono);font-size:11.5px;letter-spacing:.4px;background:rgba(255,255,255,.04);
  border:1px solid var(--line);border-radius:999px;padding:5px 12px;color:var(--muted)}
.badge b{color:var(--fg)}
.badge.hi{border-color:rgba(121,224,214,.5);color:var(--cyan)}

.scrub{display:flex;align-items:center;gap:16px;margin:22px 48px 6px;
  background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:14px 18px;backdrop-filter:blur(8px)}
.scrub input[type=range]{flex:1;-webkit-appearance:none;height:4px;border-radius:4px;
  background:linear-gradient(90deg,var(--amber),rgba(244,184,96,.15));outline:none}
.scrub input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:18px;height:18px;border-radius:50%;
  background:var(--amber);box-shadow:0 0 14px rgba(244,184,96,.8);cursor:pointer;border:2px solid #1a1405}
button{font-family:var(--mono);font-size:13px;background:rgba(255,255,255,.05);color:var(--fg);
  border:1px solid var(--line);border-radius:10px;padding:7px 13px;cursor:pointer;transition:.15s}
button:hover{border-color:var(--amber);color:var(--amber)}
.nlabel{font-family:var(--mono);font-size:14px;color:var(--amber);min-width:118px;text-align:right;letter-spacing:.5px}

.chips{display:flex;gap:10px;flex-wrap:wrap;margin:12px 48px 4px}
.chip{font-family:var(--mono);background:var(--panel);border:1px solid var(--line);border-radius:12px;
  padding:8px 13px;min-width:84px;backdrop-filter:blur(8px)}
.chip .k{font-size:10px;letter-spacing:1.2px;text-transform:uppercase;color:var(--faint)}
.chip .v{font-size:19px;color:var(--fg);margin-top:2px}
.chip .v.amber{color:var(--amber)} .chip .v.cyan{color:var(--cyan)} .chip .v.rose{color:var(--rose)}

.wrap{display:grid;grid-template-columns:1.5fr 1fr;gap:20px;padding:18px 48px 56px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:18px 20px;
  backdrop-filter:blur(10px);box-shadow:0 24px 60px rgba(0,0,0,.45);
  opacity:0;transform:translateY(14px);animation:rise .7s cubic-bezier(.2,.7,.2,1) forwards}
.card:nth-child(1){animation-delay:.05s}.card:nth-child(2){animation-delay:.12s}
.card:nth-child(3){animation-delay:.19s}.card:nth-child(4){animation-delay:.26s}
.card:nth-child(5){animation-delay:.33s}
@keyframes rise{to{opacity:1;transform:none}}
.card h2{font-family:var(--mono);margin:0 0 12px;font-size:11px;text-transform:uppercase;letter-spacing:2px;color:var(--faint)}
.full{grid-column:1/-1}
svg{display:block;width:100%}

.mem ul{padding:0;margin:0;max-height:300px;overflow:auto;list-style:none}
.mem li{padding:8px 10px;border-radius:10px;margin:4px 0;background:rgba(255,255,255,.03);
  display:flex;gap:10px;align-items:baseline;border:1px solid transparent;transition:.15s}
.mem li:hover{border-color:var(--line);background:rgba(255,255,255,.06)}
.w{font-family:var(--mono);font-size:12px;color:var(--faint);min-width:38px}
.tier{font-family:var(--mono);font-size:9px;text-transform:uppercase;letter-spacing:.7px;padding:2px 7px;border-radius:6px}
.tier.in_progress{background:rgba(244,184,96,.14);color:var(--amber)}
.tier.episodic{background:rgba(121,224,214,.14);color:var(--cyan)}
.tier.preferences{background:rgba(181,156,242,.16);color:var(--violet)}
.briefing{white-space:pre-wrap;background:rgba(255,255,255,.03);border:1px solid var(--line);border-radius:12px;
  padding:14px 16px;font-family:var(--sans);font-size:13.5px;max-height:230px;overflow:auto}
.hyp{padding:10px 12px;border-radius:11px;background:rgba(255,255,255,.03);margin:7px 0;border-left:3px solid var(--line)}
.hyp.confirmed{border-left-color:var(--cyan);background:rgba(121,224,214,.06)}
.hyp .meta{font-family:var(--mono);color:var(--faint);font-size:11px;margin-top:4px}
.hyp.confirmed .meta{color:var(--cyan)}
.pol{padding:9px 12px;border-radius:10px;background:rgba(255,255,255,.03);margin:6px 0;transition:.2s}
.pol.fresh{outline:1px solid var(--amber);background:rgba(244,184,96,.07)}
.pol .ln{font-family:var(--mono);color:var(--faint);font-size:11px;margin-top:3px}
.legend{display:flex;gap:16px;flex-wrap:wrap;color:var(--faint);font-family:var(--mono);font-size:11px;margin-top:8px}
.legend i{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px;vertical-align:middle}
.charts{display:grid;grid-template-columns:1fr 1fr;gap:22px}
.chh{font-family:var(--mono);color:var(--muted);font-size:11.5px;letter-spacing:.3px;margin-bottom:6px}
@media(max-width:1040px){.wrap,.charts{grid-template-columns:1fr}}
</style>
</head>
<body>
<div id="stars"></div>
<header>
  <div class="eyebrow">sleep-time compute · time machine</div>
  <h1><span class="moon">◗</span> nocturne</h1>
  <div class="tag">It rewrites what it knows — and how it thinks — overnight, and gets measurably better at being you each night.</div>
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
    <svg id="constellation" viewBox="0 0 580 380" preserveAspectRatio="xMidYMid meet" style="height:380px"></svg>
    <div class="legend" id="legend"></div>
  </div>
  <div class="card">
    <h2>morning briefing</h2>
    <div class="briefing" id="briefing"></div>
    <h2 style="margin-top:16px">hypothesis ledger</h2>
    <div id="ledger"></div>
  </div>

  <div class="card">
    <h2>bounded memory — this night</h2>
    <div class="mem"><ul id="mem"></ul></div>
  </div>
  <div class="card">
    <h2>policy the agent rewrote for itself</h2>
    <div id="policy"></div>
  </div>

  <div class="card full">
    <h2>the evidence</h2>
    <div class="charts">
      <div><div class="chh">memory size over nights — accumulation bloats, consolidation stays flat</div>
        <svg id="ch_tokens" viewBox="0 0 540 230" style="height:230px"></svg></div>
      <div><div class="chh">self-improvement — best-so-far climbs vs a static policy</div>
        <svg id="ch_learn" viewBox="0 0 540 230" style="height:230px"></svg></div>
    </div>
  </div>
</div>

<script>
const DATA = __DATA__;
const ARMC = {rewrite:"#f4b860", gbrain_accumulate:"#7fa8ff", append:"#e88aa8", window:"#79e0d6"};
const ARML = {rewrite:"rewrite (ours)", gbrain_accumulate:"gbrain accumulate", append:"naive append", window:"sliding window"};
const THREADS = [
  {key:"iclr", c:"#f4b860", test:t=>/review|ablation|rebuttal|iclr|camera|score/.test(t)},
  {key:"compute", c:"#7fa8ff", test:t=>/gpu|h100|2400|allocation/.test(t)},
  {key:"meeting", c:"#79e0d6", test:t=>/meeting|wednesday|thursday|11:00|14:00/.test(t)},
  {key:"memory", c:"#b59cf2", test:t=>/memory|saved|memgpt|paper|consolidat|interfer|bounded/.test(t)},
  {key:"collab", c:"#e88aa8", test:t=>/co-author|workshop|collab|okafor/.test(t)},
  {key:"other", c:"#9aa0c6", test:t=>true},
];
function threadOf(s){s=(s||"").toLowerCase();for(const th of THREADS){if(th.test(s))return th;}return THREADS[5];}
const $=id=>document.getElementById(id);
const N=DATA.nights.length;

// starfield (seeded so it's stable across reloads)
(function(){let s=9301;const rnd=()=>{s=(s*9301+49297)%233280;return s/233280;};
  let h="";for(let i=0;i<140;i++){const sz=(rnd()*1.8+0.4).toFixed(2);const d=(rnd()*4+2).toFixed(1);
    h+=`<div class="star" style="left:${(rnd()*100).toFixed(2)}%;top:${(rnd()*100).toFixed(2)}%;width:${sz}px;height:${sz}px;--d:${d}s;animation-delay:${(rnd()*4).toFixed(1)}s"></div>`;}
  $("stars").innerHTML=h;})();

$("persona").textContent=DATA.persona;
$("badges").innerHTML =
  `<span class="badge">engine <b>${DATA.engine}</b></span>`+
  `<span class="badge">model <b>${DATA.model}</b></span>`+
  `<span class="badge"><b>${N}</b> nights · 4 arms</span>`+
  (DATA.insight_found_night?`<span class="badge hi">✦ latent insight surfaced · night ${DATA.insight_found_night}</span>`:"");

const slider=$("slider"); slider.max=N; let cur=1, timer=null;

function opsGlyph(o){o=o||{};const p=[];
  if(o.add)p.push(`+${o.add}`);if(o.merge)p.push(`⊕${o.merge}`);
  if(o.reweight)p.push(`↕${o.reweight}`);if(o.drop)p.push(`−${o.drop}`);
  if(o.evicted)p.push(`⌫${o.evicted}`);return p.join(" ")||"·";}

function chip(k,v,cls){return `<div class="chip"><div class="k">${k}</div><div class="v ${cls||''}">${v}</div></div>`;}

function render(t){
  cur=t; const d=DATA.nights[t-1];
  $("nlabel").textContent=`night ${t} / ${N}`;
  slider.value=t;
  $("chips").innerHTML =
    chip("score",d.score.toFixed(3),"amber")+chip("best",d.best.toFixed(3),"amber")+
    chip("memory",`${d.facts} <span style='font-size:12px;color:var(--faint)'>items</span>`)+
    chip("tokens",d.tokens)+chip("F1",d.f1.toFixed(2),"cyan")+
    chip("recall",d.recall.toFixed(2),"cyan")+chip("noise",d.noise,d.noise?"rose":"")+
    chip("ops",`<span style='font-size:14px'>${opsGlyph(d.ops)}</span>`);
  drawConstellation(d);drawMemory(d);drawBriefing(d);drawLedger(d);drawPolicy(d,t);drawCursor();
}

function drawConstellation(d){
  const svg=$("constellation");const W=580,H=380,cx=W/2,cy=H/2;
  const groups={};
  d.memory.forEach(it=>{const th=threadOf(it.content);(groups[th.key]=groups[th.key]||{th,items:[]}).items.push(it);});
  const keys=Object.keys(groups);
  let s=`<defs>
    <radialGradient id="sky" cx="50%" cy="42%" r="62%"><stop offset="0%" stop-color="rgba(40,46,92,.55)"/><stop offset="100%" stop-color="rgba(6,7,15,0)"/></radialGradient>
    <filter id="glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>`;
  s+=`<rect x="0" y="0" width="${W}" height="${H}" fill="url(#sky)"/>`;
  // centroids first, so we can wire them into a faint constellation web behind the nodes
  const cents=keys.map((k,gi)=>{const ang=(gi/keys.length)*Math.PI*2 - Math.PI/2;
    return {x:cx+Math.cos(ang)*128, y:cy+Math.sin(ang)*98};});
  for(let i=0;i<cents.length;i++){
    const a=cents[i], b=cents[(i+1)%cents.length];
    s+=`<line x1="${a.x.toFixed(1)}" y1="${a.y.toFixed(1)}" x2="${b.x.toFixed(1)}" y2="${b.y.toFixed(1)}" stroke="#fff" stroke-opacity=".05"/>`;
    s+=`<line x1="${a.x.toFixed(1)}" y1="${a.y.toFixed(1)}" x2="${cx}" y2="${cy}" stroke="#fff" stroke-opacity=".045"/>`;
  }
  keys.forEach((k,gi)=>{
    const gx=cents[gi].x, gy=cents[gi].y;
    const g=groups[k];
    g.items.forEach((it,ii)=>{
      const a2=(ii/Math.max(1,g.items.length))*Math.PI*2;
      const r=20+g.items.length*3.2;
      const x=gx+Math.cos(a2)*r, y=gy+Math.sin(a2)*r;
      s+=`<line x1="${gx.toFixed(1)}" y1="${gy.toFixed(1)}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" stroke="${g.th.c}" stroke-opacity=".28"/>`;
      const rad=3.5+Math.min(11,it.weight*4.2);
      s+=`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${rad.toFixed(1)}" fill="${g.th.c}" fill-opacity=".9" filter="url(#glow)"><title>${esc(it.content)} (w=${it.weight.toFixed(2)})</title></circle>`;
    });
    s+=`<circle cx="${gx.toFixed(1)}" cy="${gy.toFixed(1)}" r="2.5" fill="#fff" fill-opacity=".7"/>`;
    s+=`<text x="${gx.toFixed(1)}" y="${(gy-16-g.items.length*3.2).toFixed(1)}" fill="${g.th.c}" font-family="PlexMono,monospace" font-size="11" text-anchor="middle" letter-spacing="1">${k}</text>`;
  });
  if(!keys.length)s+=`<text x="${cx}" y="${cy}" fill="#6b6f93" font-family="PlexMono,monospace" font-size="13" text-anchor="middle">memory empty</text>`;
  svg.innerHTML=s;
  $("legend").innerHTML=THREADS.slice(0,5).map(t=>`<span><i style="background:${t.c}"></i>${t.key}</span>`).join("");
}
function drawMemory(d){
  const items=[...d.memory].sort((a,b)=>b.weight-a.weight);
  $("mem").innerHTML=items.length?items.map(it=>
    `<li><span class="w">${it.weight.toFixed(2)}</span><span class="tier ${it.tier}">${it.tier.replace("_"," ")}</span><span>${esc(it.content)}</span></li>`).join("")
    :`<li style="color:var(--faint)">empty</li>`;
}
function drawBriefing(d){$("briefing").innerHTML=d.briefing?mdLite(d.briefing):"<span style='color:var(--faint)'>no briefing</span>";}
function drawLedger(d){
  if(!d.ledger||!d.ledger.length){$("ledger").innerHTML="<span style='color:var(--faint)'>no hypotheses yet</span>";return;}
  const all=[...d.ledger].sort((a,b)=>(b.status==="confirmed")-(a.status==="confirmed")||b.confidence-a.confidence);
  const top=all.slice(0,4);
  let html=top.map(h=>
    `<div class="hyp ${h.status}"><div>${h.status==="confirmed"?"✦ ":""}${esc(h.statement)}</div>
     <div class="meta">${h.status} · confidence ${h.confidence.toFixed(2)}${h.confirmed_night?` · confirmed night ${h.confirmed_night}`:""}</div></div>`).join("");
  if(all.length>top.length)html+=`<div style="font-family:var(--mono);color:var(--faint);font-size:11px;margin-top:6px">+ ${all.length-top.length} more hypotheses</div>`;
  $("ledger").innerHTML=html;
}
function drawPolicy(d,t){
  if(!d.policy||!d.policy.length){$("policy").innerHTML="<span style='color:var(--faint)'>seed policy</span>";return;}
  $("policy").innerHTML=[...d.policy].sort((a,b)=>b.weight-a.weight).map(p=>{
    const fresh=(p.learned_night===t)?"fresh":"";
    return `<div class="pol ${fresh}"><div>${esc(p.content)}</div><div class="ln">w=${p.weight.toFixed(2)} · learned night ${p.learned_night}${fresh?" · NEW":""}</div></div>`;}).join("");
}

function lineChart(svgId,series,opts){
  const svg=$(svgId),W=540,H=230,pad=36;
  const xmax=opts.xmax,ymax=opts.ymax||Math.max(1,...series.flatMap(s=>s.pts));
  const X=i=>pad+(i/(xmax-1))*(W-pad-12),Y=v=>H-pad-(v/ymax)*(H-pad-16);
  let s=`<rect x="0" y="0" width="${W}" height="${H}" rx="12" fill="rgba(255,255,255,.02)"/>`;
  for(let g=0;g<=4;g++){const y=(pad+(g/4)*(H-pad-16)).toFixed(1);s+=`<line x1="${pad}" y1="${y}" x2="${W-12}" y2="${y}" stroke="rgba(255,255,255,.06)"/>`;}
  series.forEach(se=>{const dp=se.pts.map((v,i)=>`${i?'L':'M'}${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join(" ");
    s+=`<path d="${dp}" fill="none" stroke="${se.c}" stroke-width="${se.w||2.4}" stroke-opacity="${se.o||1}" filter="url(#cg)"/>`;});
  s=`<defs><filter id="cg" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="1.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>`+s;
  s+=`<line id="${svgId}_cur" x1="0" y1="${pad}" x2="0" y2="${H-pad}" stroke="#f4b860" stroke-opacity=".55" stroke-dasharray="3 4"/>`;
  series.forEach((se,i)=>{s+=`<circle cx="${pad+i*150+5}" cy="${H-14}" r="4" fill="${se.c}"/><text x="${pad+i*150+15}" y="${H-10}" fill="#9aa0c6" font-family="PlexMono,monospace" font-size="10.5">${se.name}</text>`;});
  svg.innerHTML=s;svg._X=X;
}
function drawTokens(){const arms=Object.keys(DATA.brains);
  lineChart("ch_tokens",arms.map(a=>({name:ARML[a]||a,c:ARMC[a]||"#fff",pts:DATA.brains[a].tokens})),{xmax:N});}
function drawLearn(){const s=DATA.selfimprove;if(!s||!s.best)return;
  lineChart("ch_learn",[
    {name:"best-so-far (ours)",c:"#f4b860",pts:s.best,w:2.8},
    {name:"raw (ours)",c:"#f4b860",pts:s.raw,w:1.2,o:.4},
    {name:"static policy",c:"#9aa0c6",pts:s.static,w:2,o:.9},
  ],{xmax:N,ymax:Math.max(0.2,...s.best,...s.static,...s.raw)*1.12});}
function drawCursor(){["ch_tokens","ch_learn"].forEach(id=>{const svg=$(id);if(!svg._X)return;
  const x=svg._X(cur-1).toFixed(1);const c=$(id+"_cur");if(c){c.setAttribute("x1",x);c.setAttribute("x2",x);}});}

function esc(s){return(s||"").replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));}
function mdLite(s){return esc(s)
  .replace(/^#+\s*(.*)$/gm,'<b style="color:var(--amber);font-family:var(--serif);font-size:15px">$1</b>')
  .replace(/\*\*(.*?)\*\*/g,'<b>$1</b>').replace(/^[-•]\s*(.*)$/gm,'• $1');}

slider.oninput=e=>render(+e.target.value);
$("prev").onclick=()=>render(Math.max(1,cur-1));
$("next").onclick=()=>render(Math.min(N,cur+1));
$("play").onclick=function(){if(timer){clearInterval(timer);timer=null;this.textContent="▶ play";return;}
  this.textContent="⏸ pause";timer=setInterval(()=>{if(cur>=N){clearInterval(timer);timer=null;$("play").textContent="▶ play";return;}render(cur+1);},700);};
drawTokens();drawLearn();
const _h=(location.hash.match(/night=(\d+)/)||[])[1];
render(_h?Math.max(1,Math.min(N,+_h)):1);
window.addEventListener("hashchange",()=>{const m=(location.hash.match(/night=(\d+)/)||[])[1];if(m)render(Math.max(1,Math.min(N,+m)));});
</script>
</body>
</html>
"""
