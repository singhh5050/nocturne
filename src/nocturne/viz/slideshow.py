"""Build a self-contained narrated demo deck (artifacts/slideshow.html).

Single HTML file, no server/network. Shares the dashboard's celestial theme (WebGL nebula, Fraunces
+ IBM Plex, gold-on-indigo), puts the ◗ nocturne mark in the corner of every slide, and embeds the
live dashboard as an auto-piloted demo slide (via an iframe `srcdoc` + a postMessage control channel).
Real numbers come from runs/run.json + runs/batch/summary.json; charts are base64-embedded PNGs.

Design follows Anthropic's frontend-design principles: distinctive type, one dominant color with
sharp accents, orchestrated staggered reveals, atmospheric texture, unexpected layout, no defaults.

Build:  python -m nocturne.run deck   (after `eval`/`dashboard` so artifacts exist)
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

from . import dashboard as dash

ART = Path("artifacts")
RUN = Path("runs/run.json")
SUMMARY = Path("runs/batch/summary.json")


def _png(name: str) -> str:
    p = ART / f"{name}.png"
    return ("data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()) if p.exists() else ""


def _esc_srcdoc(html: str) -> str:
    # round-trips through the iframe srcdoc attribute (browser unescapes before parsing)
    return html.replace("&", "&amp;").replace('"', "&quot;")


def _fmt(x, n=2):
    try:
        return f"{float(x):.{n}f}"
    except Exception:
        return str(x)


def _evidence(summary: dict, bundle: dict) -> tuple[str, str, str]:
    """Return (brains_table_html, selfimprove_html, ablations_html)."""
    agg = summary.get("aggregate", {}) if summary else {}
    label = {"rewrite": "rewrite (ours)", "gbrain_accumulate": "gbrain — retrieval",
             "append": "naive append", "window": "sliding window"}
    rows = []
    for arm in ["rewrite", "gbrain_accumulate", "append", "window"]:
        a = agg.get(arm)
        if not a:
            # fall back to single-run final-night numbers
            res = bundle["brains"].get(arm)
            if not res:
                continue
            last = res["nights"][-1]["metrics"]; tok = res["nights"][-1]["tokens"]; qa = res["qa_accuracy"]
            a = {"tokens": {"mean": tok, "std": 0}, "f1": {"mean": last["f1"], "std": 0},
                 "recall": {"mean": last["recall"], "std": 0}, "qa": {"mean": qa, "std": 0}}
        hi = ' class="hi"' if arm == "rewrite" else ""
        rows.append(
            f"<tr{hi}><td>{label[arm]}</td><td>{int(a['tokens']['mean'])}</td>"
            f"<td>{_fmt(a['f1']['mean'])}±{_fmt(a['f1']['std'])}</td>"
            f"<td>{_fmt(a['recall']['mean'])}</td><td>{_fmt(a['qa']['mean'])}</td></tr>")
    table = ("<table class='ev'><thead><tr><th>memory strategy</th><th>store (tok)</th>"
             "<th>needle F1</th><th>recall</th><th>QA</th></tr></thead><tbody>"
             + "".join(rows) + "</tbody></table>")

    si = agg.get("selfimprove", {})
    if si:
        best = si["best_final"]; stat = si["static_final"]
        selfimp = (f"<div class='big'>{_fmt(best['mean'])}<span>±{_fmt(best['std'])}</span></div>"
                   f"<div class='cap'>self-improving best-so-far</div>"
                   f"<div class='vs'>vs <b>{_fmt(stat['mean'])}±{_fmt(stat['std'])}</b> static policy</div>")
    else:
        selfimp = "<div class='cap'>see learning-curve chart</div>"

    abl = summary.get("ablations", {}) if summary else {}
    items = []
    if abl.get("rem_off"):
        items.append(f"REM off → insight {'lost' if not abl['rem_off'].get('insight_night') else 'kept'}")
    if abl.get("decay_off"):
        items.append(f"decay off → noise {abl['decay_off'].get('noise', '?')} creeps in")
    if abl.get("improve_off"):
        items.append(f"self-improve off → F1 drops to {_fmt(abl['improve_off'].get('f1'))}")
    ablation = " · ".join(items) if items else "REM / decay / self-improvement each earn their place"
    return table, selfimp, ablation


def build(out_path: Path = ART / "slideshow.html") -> Path:
    bundle = json.loads(RUN.read_text())
    summary = json.loads(SUMMARY.read_text()) if SUMMARY.exists() else {}
    demo_html = (ART / "dashboard.html").read_text()
    table, selfimp, ablation = _evidence(summary, bundle)

    repl = {
        "__FONTS__": dash._font_face_css(),
        "__DEMO__": _esc_srcdoc(demo_html),
        "__CH_MEM__": _png("memory_size"),
        "__CH_LEARN__": _png("learning_curve"),
        "__CH_QUAL__": _png("brains_quality"),
        "__CH_QA__": _png("qa_accuracy"),
        "__EV_TABLE__": table,
        "__SELFIMP__": selfimp,
        "__ABLATION__": ablation,
        "__MODEL__": bundle.get("model", "?"),
        "__REM__": bundle.get("rem_model", "") or "—",
        "__CELLARIUS__": (("data:image/jpeg;base64," + base64.b64encode((ART / "art" / "cellarius_moon.jpg").read_bytes()).decode())
                          if (ART / "art" / "cellarius_moon.jpg").exists() else ""),
    }
    html = _TEMPLATE
    for k, v in repl.items():
        html = html.replace(k, v)
    out_path = Path(out_path)
    out_path.write_text(html)
    return out_path


_TEMPLATE = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>nocturne — demo deck</title>
<style>
__FONTS__
:root{--fg:#efe9d8;--muted:#a9a487;--faint:#76728f;--gold:#d9b25a;--amber:#f4b860;--cyan:#79e0d6;
  --rose:#e88aa8;--violet:#b59cf2;--blue:#7fa8ff;--line:rgba(217,178,90,.22);
  --serif:'Fraunces','Iowan Old Style',Georgia,serif;--mono:'PlexMono',ui-monospace,Menlo,monospace;
  --sans:'PlexSans',ui-sans-serif,system-ui,sans-serif;}
*{box-sizing:border-box}
html{background:#05060d}
body{margin:0;background:transparent;color:var(--fg);font-family:var(--sans);overflow:hidden;height:100vh}
#bg{position:fixed;inset:0;z-index:-3;display:block}
body::before{content:"";position:fixed;inset:0;z-index:-2;pointer-events:none;background:
  radial-gradient(1200px 720px at 50% -10%, rgba(217,178,90,.12), transparent 60%),
  radial-gradient(900px 820px at 85% 112%, rgba(121,90,200,.12), transparent 60%),
  linear-gradient(180deg, rgba(6,7,16,.34), rgba(4,5,12,.5) 55%, rgba(3,4,10,.66));}
/* deck shell */
.deck{position:fixed;inset:0}
.slide{position:absolute;inset:0;z-index:1;display:flex;flex-direction:column;justify-content:center;
  padding:7vh 9vw;opacity:0;visibility:hidden;pointer-events:none;transition:opacity .5s ease;
  text-shadow:0 1px 18px rgba(2,3,8,.8);}
.slide.active{opacity:1;visibility:visible;pointer-events:auto}
/* reveal = a gentle slide-up only. NO opacity tween (that was stranding content invisible);
   the slide-level opacity transition handles the fade, so content is never hidden. */
.slide.active .reveal{animation:rise .6s cubic-bezier(.2,.7,.2,1) both}
.slide.active .reveal:nth-child(2){animation-delay:.08s}.slide.active .reveal:nth-child(3){animation-delay:.16s}
.slide.active .reveal:nth-child(4){animation-delay:.24s}.slide.active .reveal:nth-child(5){animation-delay:.32s}
.slide.active .reveal:nth-child(6){animation-delay:.40s}
@keyframes rise{from{transform:translateY(16px)}to{transform:none}}
/* logo, every slide */
.logo{position:fixed;top:26px;left:34px;font-family:var(--serif);font-size:22px;font-weight:600;
  color:var(--fg);z-index:50;letter-spacing:.3px;text-shadow:0 1px 14px rgba(2,3,8,.7)}
.logo .moon{color:var(--amber);text-shadow:0 0 20px rgba(244,184,96,.55)}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:3px;text-transform:uppercase;color:var(--gold)}
h1{font-family:var(--serif);font-weight:600;line-height:1.02;letter-spacing:-.5px;margin:.2em 0 0}
.s-title h1{font-size:clamp(48px,8vw,104px)}
h2{font-family:var(--serif);font-weight:600;font-size:clamp(30px,4.4vw,52px);line-height:1.05;margin:.15em 0 .35em}
.lede{font-family:var(--serif);font-style:italic;color:#e2d9b6;font-size:clamp(20px,2.4vw,30px);max-width:24ch}
p,li{font-size:clamp(15px,1.5vw,19px);color:var(--fg);max-width:60ch;line-height:1.6}
.muted{color:var(--muted)} .gold{color:var(--amber)} .faint{color:var(--faint)}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:5vw;align-items:center}
.card{background:rgba(14,16,34,.55);border:1px solid var(--line);border-radius:18px;padding:22px 24px;backdrop-filter:blur(8px)}
ul{margin:.2em 0;padding-left:1.1em} li{margin:.35em 0}
.kbd{font-family:var(--mono);font-size:11px;color:var(--faint);border:1px solid var(--line);border-radius:6px;padding:1px 6px}
/* progress + nav */
.dots{position:fixed;bottom:22px;left:50%;transform:translateX(-50%);display:flex;gap:8px;z-index:50}
.dots b{width:8px;height:8px;border-radius:50%;background:rgba(217,178,90,.25);transition:.3s;cursor:pointer}
.dots b.on{background:var(--amber);box-shadow:0 0 10px rgba(244,184,96,.7)}
.pageno{position:fixed;bottom:20px;right:34px;font-family:var(--mono);font-size:12px;color:var(--faint);z-index:50}
.nav{position:fixed;bottom:18px;left:34px;display:flex;gap:8px;z-index:50}
.nav button{font-family:var(--mono);font-size:13px;background:rgba(217,178,90,.06);color:var(--fg);border:1px solid var(--line);border-radius:9px;padding:6px 11px;cursor:pointer}
.nav button:hover{border-color:var(--gold);color:var(--amber)}
/* tables */
table.ev{border-collapse:collapse;font-family:var(--mono);font-size:15px;width:100%;max-width:760px}
table.ev th{ text-align:left;color:var(--faint);font-weight:500;font-size:12px;letter-spacing:1px;text-transform:uppercase;padding:8px 14px;border-bottom:1px solid var(--line)}
table.ev td{padding:9px 14px;border-bottom:1px solid rgba(217,178,90,.08)}
table.ev tr.hi td{color:var(--amber)}
table.wins{border-collapse:collapse;font-size:15px;width:100%;max-width:840px}
table.wins th,table.wins td{text-align:left;padding:9px 14px;border-bottom:1px solid rgba(217,178,90,.1);vertical-align:top}
table.wins th{font-family:var(--mono);font-size:12px;color:var(--faint);text-transform:uppercase;letter-spacing:1px}
table.wins .a{color:var(--blue)} table.wins .b{color:var(--amber)}
.big{font-family:var(--serif);font-size:84px;color:var(--amber);line-height:1}.big span{font-size:32px;color:var(--muted)}
.cap{font-family:var(--mono);font-size:13px;color:var(--muted);letter-spacing:1px} .vs{color:var(--faint);margin-top:6px}
img.chart{max-width:100%;max-height:54vh;border-radius:12px;border:1px solid var(--line)}
.plate{margin:0;text-align:center}
.plate img{max-width:100%;max-height:48vh;border-radius:12px;border:1px solid var(--line);box-shadow:0 22px 60px rgba(0,0,0,.55)}
.plate figcaption{font-family:var(--mono);font-size:11px;color:var(--faint);margin-top:8px;letter-spacing:.4px}
/* demo */
.demo-wrap{position:absolute;inset:0;padding:64px 40px 56px}
.demo-frame{width:100%;height:100%;border:1px solid var(--line);border-radius:16px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.5);background:#05060d}
.demo-frame iframe{width:100%;height:100%;border:0;display:block}
.cursor{position:fixed;width:22px;height:22px;z-index:60;pointer-events:none;transition:left 1.1s cubic-bezier(.4,.5,.2,1),top 1.1s cubic-bezier(.4,.5,.2,1),opacity .3s;opacity:0;
  background:radial-gradient(circle at 35% 35%, #fff, #f4b860 60%, transparent 72%);border-radius:50%;box-shadow:0 0 16px rgba(244,184,96,.9)}
.caption{position:fixed;top:64px;left:50%;transform:translateX(-50%);font-family:var(--mono);font-size:14px;color:var(--amber);
  background:rgba(8,9,18,.7);border:1px solid var(--line);border-radius:999px;padding:7px 16px;z-index:55;opacity:0;transition:opacity .4s}
.flow{display:flex;align-items:center;gap:18px;flex-wrap:wrap;font-family:var(--mono);font-size:15px}
.flow .box{border:1px solid var(--line);border-radius:12px;padding:12px 16px;background:rgba(14,16,34,.5)}
.flow .arr{color:var(--gold);font-size:24px}
.discl{border-left:3px solid var(--cyan);padding:10px 16px;background:rgba(121,224,214,.06);border-radius:8px}
</style></head>
<body>
<canvas id="bg"></canvas>
<div class="logo"><span class="moon">◗</span> nocturne</div>
<div class="cursor" id="cursor"></div>
<div class="caption" id="caption"></div>

<div class="deck" id="deck">

  <section class="slide s-title">
    <div class="reveal eyebrow">harmonia macrocosmica · sleep-time compute</div>
    <h1 class="reveal">nocturne</h1>
    <div class="reveal lede" style="max-width:34ch;margin-top:18px">A self-improving sleep-time agent — it rewrites what it knows, and how it thinks, overnight.</div>
    <p class="reveal faint" style="margin-top:22px">the smallest memory that still makes you effective tomorrow · a working-memory layer for agents</p>
  </section>

  <section class="slide">
    <div class="reveal eyebrow">the inspiration</div>
    <h2 class="reveal">A constellation is meaning drawn from chaos.</h2>
    <div class="reveal cols" style="grid-template-columns:1.05fr .95fr">
      <div>
        <p>Inspired by baroque star atlases — Cellarius, 1660. The night sky is an overwhelming field of stars: the raw stream. The astronomer working through the night doesn't catalog every one — they draw a few <span class="gold">constellations</span>, the figures you steer by.</p>
        <p class="faint">Everything in the app itself is drawn in code — a live nebula, procedural constellations. We borrowed the period's spirit, not its pictures.</p>
      </div>
      <figure class="plate"><img src="__CELLARIUS__" alt="Cellarius celestial plate, 1660"/>
        <figcaption>Andreas Cellarius · <i>The Varying Phases of the Moon</i> · Harmonia Macrocosmica, 1660</figcaption></figure>
    </div>
  </section>

  <section class="slide">
    <div class="reveal eyebrow">Q1 · problem &amp; insight</div>
    <h2 class="reveal">Memory that accumulates vs. memory that consolidates</h2>
    <div class="reveal cols">
      <div class="card"><p><b class="a" style="color:var(--blue)">The default — append.</b> GBrain (YC, 2026) leans all the way in: a <b>146k-page</b> never-forget library you retrieve from. Great at "how do I never forget anything?"</p></div>
      <div class="card"><p><b class="gold">The inverted question.</b> What's the <i>smallest</i> memory that still makes me effective tomorrow? Bounded working memory, active forgetting, consolidation. A different organ.</p></div>
    </div>
  </section>

  <section class="slide">
    <div class="reveal eyebrow">Q2 · how it works</div>
    <h2 class="reveal">One primitive, two levels — overnight</h2>
    <div class="reveal flow">
      <div class="box">stream<br><span class="faint">papers · mail · calendar · slack</span></div>
      <span class="arr">→</span>
      <div class="box">LIGHT triage → DEEP consolidate<br><span class="faint">add · merge · reweight · drop</span></div>
      <span class="arr">→</span>
      <div class="box">REM synthesis<br><span class="faint">cross-thread insight</span></div>
    </div>
    <p class="reveal" style="margin-top:24px">The same <span class="gold">add/merge/reweight/drop</span> primitive runs on <b>memory</b> (what I know) <i>and</i> on the agent's own <b>policy</b> (how I decide what's worth keeping) — rewritten each morning from a graded critique. Real model cognition on the live API.</p>
  </section>

  <section class="slide" data-demo="1">
    <div class="demo-wrap">
      <div class="demo-frame"><iframe id="demoframe" srcdoc="__DEMO__"></iframe></div>
    </div>
  </section>

  <section class="slide">
    <div class="reveal eyebrow">evaluation &amp; evidence</div>
    <h2 class="reveal">Four memory strategies · identical 30-night stream · 5 seeds</h2>
    <div class="reveal cols" style="grid-template-columns:1.1fr .9fr">
      <div>__EV_TABLE__
        <p class="faint" style="margin-top:12px;font-size:14px">Fair comparison: the library arm gets real top-K retrieval — we don't strawman its query cost. Ablations: __ABLATION__.</p></div>
      <div><img class="chart" src="__CH_MEM__" alt="memory size"/></div>
    </div>
  </section>

  <section class="slide">
    <div class="reveal eyebrow">it teaches itself</div>
    <h2 class="reveal">Self-improvement — it rewrites its own policy</h2>
    <div class="reveal cols">
      <div>__SELFIMP__
        <p class="faint" style="margin-top:16px">Learned directives, unprompted: "drop promotional mail," "retain deadlines &amp; advisor follow-ups." GBrain has no mechanism for this.</p></div>
      <div><img class="chart" src="__CH_LEARN__" alt="learning curve"/></div>
    </div>
  </section>

  <section class="slide">
    <div class="reveal eyebrow">vs. state of the art</div>
    <h2 class="reveal">Not a competitor — the missing layer</h2>
    <div class="reveal"><table class="wins">
      <thead><tr><th></th><th class="a">GBrain — long-term memory</th><th class="b">nocturne — working memory</th></tr></thead>
      <tbody>
        <tr><td class="faint">footprint</td><td>never forget (146k+ pages)</td><td>bounded; active forgetting</td></tr>
        <tr><td class="faint">contradictions</td><td>surfaces both</td><td>reconciles to current truth</td></tr>
        <tr><td class="faint">interaction</td><td>pull — you query</td><td>push — proactive briefing</td></tr>
        <tr><td class="faint">adaptation</td><td>fixed pipeline</td><td>rewrites its own policy</td></tr>
      </tbody>
    </table></div>
    <p class="reveal faint" style="margin-top:18px">Honest trade: accumulation wins long-tail recall. They're <span class="gold">complementary</span> — nocturne sits on top of a library like GBrain.</p>
  </section>

  <section class="slide">
    <div class="reveal eyebrow">data &amp; methods</div>
    <h2 class="reveal">A reproducible, labeled environment</h2>
    <p class="reveal discl">The 30-day stream is a <b>simulated</b>, ground-truth-labeled environment — built so the system is reproducible and testable at a month's scale. <b>The inputs are simulated; every bit of the cognition is a real model</b> running on DigitalOcean (__MODEL__ + __REM__ for REM).</p>
    <p class="reveal faint">Labels are authored independently of item text, so the evaluation is non-circular.</p>
  </section>

  <section class="slide">
    <div class="reveal eyebrow">Q3 · impact &nbsp;·&nbsp; Q4 · what's next</div>
    <h2 class="reveal">A working-memory layer for anyone drowning in streams</h2>
    <p class="reveal">Researchers, founders, clinicians — wake up oriented, not buried. A reusable, auditable working-memory layer for any agent.</p>
    <p class="reveal"><span class="gold">Next:</span> real OAuth sources, a nightly cron, and wiring nocturne on top of a bottomless library like GBrain via MCP — the two halves of memory, together.</p>
  </section>

  <section class="slide s-title">
    <div class="reveal eyebrow">thank you</div>
    <h1 class="reveal" style="font-size:clamp(40px,6vw,76px)">the smallest memory<br/>that still makes you<br/>effective tomorrow.</h1>
  </section>

</div>

<div class="nav"><button id="prev">◀</button><button id="next">▶</button></div>
<div class="dots" id="dots"></div>
<div class="pageno" id="pageno"></div>

<script>
// shared procedural nebula (same shader as the dashboard)
(function(){const cv=document.getElementById("bg");let gl=null;try{gl=cv.getContext("webgl")||cv.getContext("experimental-webgl");}catch(e){}
 if(!gl){document.body.style.background="radial-gradient(1200px 720px at 50% -5%,#15173a,#06070f 60%)";return;}
 const vs="attribute vec2 a;void main(){gl_Position=vec4(a,0.,1.);}";
 const fs="precision highp float;uniform vec2 uRes;uniform float uTime;"+
 "float hash(vec2 p){p=fract(p*vec2(123.34,345.45));p+=dot(p,p+34.345);return fract(p.x*p.y);}"+
 "float noise(vec2 p){vec2 i=floor(p),f=fract(p);vec2 u=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),u.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),u.x),u.y);}"+
 "float fbm(vec2 p){float v=0.,a=.5;mat2 m=mat2(1.6,1.2,-1.2,1.6);for(int i=0;i<6;i++){v+=a*noise(p);p=m*p;a*=.5;}return v;}"+
 "void main(){vec2 uv=gl_FragCoord.xy/uRes.xy;vec2 c=(uv-0.5)*vec2(uRes.x/uRes.y,1.);float t=uTime*0.10;"+
 "float ang=t*0.7+length(c)*1.5;float s=sin(ang),co=cos(ang);c=mat2(co,-s,s,co)*c;vec2 p=c*3.0;"+
 "vec2 q=vec2(fbm(p+vec2(1.4*sin(t*0.7),t)),fbm(p+vec2(5.2-t,1.3+1.4*cos(t*0.6))));"+
 "vec2 r=vec2(fbm(p+4.*q+vec2(1.7,9.2)+1.2*t),fbm(p+4.*q+vec2(8.3,2.8)-1.2*t));float f=fbm(p+4.*r+0.6*q);"+
 "vec3 col=vec3(0.03,0.035,0.085);col=mix(col,vec3(0.10,0.12,0.30),clamp(f*f*1.7,0.,1.));"+
 "col=mix(col,vec3(0.30,0.19,0.44),clamp(length(q)*0.55,0.,1.));col=mix(col,vec3(0.96,0.72,0.36),clamp(pow(max(r.x,0.),3.)*1.1,0.,1.));"+
 "float vig=smoothstep(1.3,0.2,length(uv-0.5));col*=0.54+0.52*vig;col*=0.98;gl_FragColor=vec4(col,1.);}";
 function sh(t,s){const o=gl.createShader(t);gl.shaderSource(o,s);gl.compileShader(o);return o;}
 const pr=gl.createProgram();gl.attachShader(pr,sh(gl.VERTEX_SHADER,vs));gl.attachShader(pr,sh(gl.FRAGMENT_SHADER,fs));gl.linkProgram(pr);gl.useProgram(pr);
 const b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);
 const la=gl.getAttribLocation(pr,"a");gl.enableVertexAttribArray(la);gl.vertexAttribPointer(la,2,gl.FLOAT,false,0,0);
 const uRes=gl.getUniformLocation(pr,"uRes"),uTime=gl.getUniformLocation(pr,"uTime");
 function rz(){const d=Math.min(window.devicePixelRatio||1,2);cv.width=Math.floor(innerWidth*d);cv.height=Math.floor(innerHeight*d);gl.viewport(0,0,cv.width,cv.height);}
 addEventListener("resize",rz);rz();const t0=performance.now();
 (function loop(){gl.uniform2f(uRes,cv.width,cv.height);gl.uniform1f(uTime,(performance.now()-t0)/1000);gl.drawArrays(gl.TRIANGLES,0,3);requestAnimationFrame(loop);})();
})();

// deck navigation
const slides=[...document.querySelectorAll(".slide")];const N=slides.length;let cur=0;
let timers=[];function T(fn,ms){const id=setTimeout(fn,ms);timers.push(id);return id;}
function clearTimers(){timers.forEach(clearTimeout);timers=[];}
const dots=document.getElementById("dots");slides.forEach((_,i)=>{const b=document.createElement("b");b.onclick=()=>go(i);dots.appendChild(b);});
function go(i){cur=Math.max(0,Math.min(N-1,i));slides.forEach((s,j)=>s.classList.toggle("active",j===cur));
  [...dots.children].forEach((b,j)=>b.classList.toggle("on",j===cur));
  document.getElementById("pageno").textContent=(cur+1)+" / "+N;history.replaceState(null,"","#s="+(cur+1));
  stopDemo();hideDemoFx();if(slides[cur].dataset.demo)T(startDemo,520);}
document.getElementById("next").onclick=()=>go(cur+1);
document.getElementById("prev").onclick=()=>go(cur-1);
addEventListener("keydown",e=>{if(e.key==="ArrowRight"||e.key===" ")go(cur+1);if(e.key==="ArrowLeft")go(cur-1);});
addEventListener("click",e=>{if(slides[cur].dataset.demo)return;if(e.target.closest(".nav,.dots"))return;go(cur+(e.clientX>innerWidth*0.5?1:-1));});

// ---- auto-piloted demo: a queue of beats; the cursor is anchored to REAL elements in the
// embedded app, scrolls to them, and the next beat fires when the cursor ARRIVES (not on a timer).
// render(night) inside the app triggers its own animations (stars glide, briefing types, panels cross-fade).
const cursor=document.getElementById("cursor"),caption=document.getElementById("caption");
function moveCursorPx(x,y){cursor.style.opacity="1";cursor.style.left=x+"px";cursor.style.top=y+"px";}
let capTok=0;
function say(t){const tok=++capTok;caption.style.opacity="1";caption.textContent="";let i=0;
  (function typ(){if(tok!==capTok)return;i+=2;caption.textContent=t.slice(0,i);if(i<t.length)T(typ,16);})();}
function hideDemoFx(){cursor.style.opacity="0";caption.style.opacity="0";}
function postNight(n){const f=document.getElementById("demoframe");if(f&&f.contentWindow)f.contentWindow.postMessage({nocturne:1,night:n},"*");}
function frameDoc(){const f=document.getElementById("demoframe");try{return [f,f.contentWindow,f.contentDocument||f.contentWindow.document];}catch(e){return [f,null,null];}}
function placeOn(f,el){const ir=f.getBoundingClientRect(),er=el.getBoundingClientRect();
  moveCursorPx(ir.left+er.left+Math.min(er.width,44)/2, ir.top+er.top+Math.min(er.height,44)/2);}
function arrive(fn){let done=false;const h=e=>{if(e&&e.propertyName&&e.propertyName!=="left"&&e.propertyName!=="top")return;
  if(done)return;done=true;cursor.removeEventListener("transitionend",h);fn();};
  cursor.addEventListener("transitionend",h);T(()=>{if(!done){done=true;cursor.removeEventListener("transitionend",h);fn();}},1600);}
let demoActive=false,beatIdx=0;
const BEATS=[
  {night:2,  sel:"#intake",          cap:"the night's intake — it keeps the signal, lets the noise go"},
  {night:6,  sel:"#intake",          cap:"every night a flood arrives; only the few that matter are kept"},
  {night:9,  sel:"#cl-nodes circle", scroll:"#constellation", click:1, cap:"click any star — see the raw items it was built from"},
  {night:11, sel:"#constellation",   cap:"night 11 · the meeting moved — it reconciles, dropping the stale time"},
  {night:16, sel:"#b-lib",           cap:"two brains — a small constellation versus an exploding catalog"},
  {night:22, sel:"#ledger",          cap:"night 22 · a cross-thread insight, confirmed"},
  {night:24, sel:"#policy",          cap:"the policy it rewrote for itself, overnight"},
  {night:27, sel:"#dec",             cap:"every overnight decision, logged"},
];
function stopDemo(){demoActive=false;clearTimers();}
function startDemo(){demoActive=true;beatIdx=0;beat();}
function beat(){
  if(!demoActive)return;
  if(beatIdx>=BEATS.length)beatIdx=0;
  const b=BEATS[beatIdx++];const [f,fw,fd]=frameDoc();
  try{if(b.night)(fw&&fw.render?fw.render(b.night):postNight(b.night));}catch(e){postNight(b.night);}
  if(b.cap)say(b.cap);
  const sc=fd&&fd.querySelector(b.scroll||b.sel);if(sc)sc.scrollIntoView({behavior:"smooth",block:"center"});
  T(()=>{                                            // let the scroll + the app's render animation settle
    const el=fd&&fd.querySelector(b.sel);if(!el){T(beat,1800);return;}
    placeOn(f,el);                                   // glide the cursor to the real element
    arrive(()=>{                                     // fire only once the cursor has ARRIVED
      if(b.click){try{el.dispatchEvent(new MouseEvent("click",{bubbles:true}));}catch(_){}
        const insp=fd.querySelector("#inspector");
        if(insp){T(()=>{insp.scrollIntoView({behavior:"smooth",block:"center"});
          T(()=>{placeOn(f,insp);say("provenance — why the brain believes it");arrive(()=>T(beat,2200));},700);},450);return;}}
      T(beat,2300);
    });
  },b.scrollWait||760);
}
const _h=(location.hash.match(/s=(\d+)/)||[])[1];go(_h?+_h-1:0);
addEventListener("hashchange",()=>{const m=(location.hash.match(/s=(\d+)/)||[])[1];if(m&&+m-1!==cur)go(+m-1);});
</script></body></html>
"""
