"""Generate the dashboard's atmospheric textures with a diffusion model (reproducible art).

Design rule: **art is atmosphere only.** Diffusion supplies full-bleed, non-figurative textures
that cover-scale at any window size; every structural / interactive element (the constellation,
the two-brains star fields, particles, charts) is procedural SVG. We never drop a framed image into
the layout and hope it fits.

Motif: baroque celestial cartography (Cellarius, *Harmonia Macrocosmica*, 1660) — "a constellation
is meaning drawn from chaos." Model: stable-diffusion-3.5-large via the DigitalOcean
OpenAI-compatible endpoint (gpt-image tiers were unavailable; SD3.5 caps at 1024² on this tier).

Run:  python -m nocturne.viz.generate_art      (needs OPENAI_* in .env)
Outputs commit to artifacts/art/ and are base64-embedded into the self-contained dashboard.
"""
from __future__ import annotations

import base64
import io
from pathlib import Path

from ..config import get_settings

OUT = Path("artifacts/art")

PROMPTS = {
    "nebula": (
        "abstract deep-space nebula filling the entire frame edge to edge, vast dark midnight-indigo "
        "and near-black cosmos, faint scattered gold and amber stardust and tiny distant stars, soft "
        "wispy cosmic clouds, low-contrast, atmospheric, painterly, baroque celestial atlas palette, "
        "no border, no frame, no circle, no vignette, no text, no lettering, seamless full bleed"),
    "parchment": (
        "seamless aged parchment paper texture, warm cream tan and faint gold, subtle fibers, gentle "
        "foxing and age stains, antique star-map paper, even flat lighting, no text, no border, "
        "no figures, tileable"),
    "hero": (
        "a grand circular celestial planisphere, gold constellation figures and thin golden grid "
        "lines over a deep indigo starfield, ornate engraved circular border, baroque celestial "
        "atlas, Andreas Cellarius Harmonia Macrocosmica 1660 style, hand-colored copperplate "
        "engraving, deep midnight indigo and antique gold, aged parchment, no text, no lettering"),
}


def generate(model: str = "stable-diffusion-3.5-large", size: str = "1024x1024",
             quality: int = 82) -> list[Path]:
    from openai import OpenAI
    from PIL import Image
    s = get_settings()
    client = OpenAI(base_url=s.openai_base_url, api_key=s.openai_api_key)
    OUT.mkdir(parents=True, exist_ok=True)
    saved = []
    for name, prompt in PROMPTS.items():
        r = client.images.generate(model=model, prompt=prompt, size=size, n=1)
        raw = base64.b64decode(r.data[0].b64_json)
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        p = OUT / f"{name}.jpg"
        im.save(p, "JPEG", quality=quality, optimize=True)
        saved.append(p)
        print(f"  {name}: {im.size} -> {p} ({p.stat().st_size // 1024}KB)")
    return saved


if __name__ == "__main__":
    print("generating celestial-atlas textures via diffusion ...")
    generate()
