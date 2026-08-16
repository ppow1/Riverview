"""Minimal bounded WebXR-capable spatial prototype surface.

This is a real browser-renderable prototype scaffold, not evidence of Quest
hardware acceptance. It keeps operational state read-only and labels
placeholder/proposed geometry honestly.
"""

WEBXR_PROTOTYPE_HTML = """<!doctype html>
<html lang="en"><meta charset="utf-8"><title>Riverview Spatial Prototype</title>
<style>body{background:#10131a;color:#e7eefc;font:16px sans-serif;margin:2rem}canvas{border:1px solid #65718a;max-width:100%}button{padding:.6rem;margin:.5rem 0}</style>
<h1>Riverview Spatial Prototype</h1>
<p id="state">Read-only logical scene. Geometry and resident visuals are marked proposed.</p>
<button id="enter">Enter immersive VR when a compatible headset is available</button>
<canvas id="scene" width="960" height="540" aria-label="Riverview logical spatial scene"></canvas>
<script>
const canvas=document.getElementById('scene'),ctx=canvas.getContext('2d');
ctx.fillStyle='#182235';ctx.fillRect(0,0,canvas.width,canvas.height);
ctx.strokeStyle='#5cc8ff';ctx.strokeRect(140,120,680,300);
ctx.fillStyle='#e7eefc';ctx.font='24px sans-serif';ctx.fillText('Riverview logical room (PROPOSED)',180,170);
ctx.font='18px sans-serif';ctx.fillText('Resident references: read-only',180,215);ctx.fillText('Operational ownership: PostgreSQL/Riverview',180,250);
document.getElementById('enter').onclick=async()=>{if(!navigator.xr){document.getElementById('state').textContent='WebXR unavailable; no headset session started.';return;}try{const session=await navigator.xr.requestSession('immersive-vr');document.getElementById('state').textContent='WebXR session active; operational controls remain disabled.';session.addEventListener('end',()=>document.getElementById('state').textContent='WebXR session ended.');}catch(error){document.getElementById('state').textContent='WebXR session unavailable: '+error.name;}};
</script></html>"""


def prototype_html() -> str:
    """Return the bounded renderable prototype without operational controls."""

    return WEBXR_PROTOTYPE_HTML
