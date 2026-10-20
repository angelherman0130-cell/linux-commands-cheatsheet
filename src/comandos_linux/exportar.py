"""Exporta el dataset a HTML standalone y a Markdown."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------

PLANTILLA_HTML = """<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><title>__TITULO__</title>
<style>
:root{--bg:#fff;--card:#fff;--soft:#f4f3ee;--tx:#1f1f1d;--tx2:#5f5e5a;--bd:#d9d7cf;--ac:#185FA5;--acbg:#E6F1FB;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#1c1c1a;--card:#262624;--soft:#32322f;--tx:#f1efe8;--tx2:#b4b2a9;--bd:#444441;--ac:#85B7EB;--acbg:#0C447C}}
:root[data-theme="dark"]{--bg:#1c1c1a;--card:#262624;--soft:#32322f;--tx:#f1efe8;--tx2:#b4b2a9;--bd:#444441;--ac:#85B7EB;--acbg:#0C447C}
html{scroll-padding-top:env(safe-area-inset-top,0px)}
body{margin:0;background:var(--bg);color:var(--tx);font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:720px;margin:0 auto;padding:20px 16px 40px}
h1{font-size:22px;font-weight:500;margin:0 0 4px}.sub{color:var(--tx2);font-size:14px;margin:0 0 14px}
.seg,.bar{display:flex;gap:8px;margin-bottom:10px}
button{font:inherit;font-size:14px;color:var(--tx);background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:8px 10px;cursor:pointer}
.seg button,.bar button{flex:1}
.seg button.on{background:var(--acbg);color:var(--ac);border-color:var(--ac);font-weight:500}
.note{font-size:13px;color:var(--tx2);margin:0 0 14px}
.root{display:inline-block;background:var(--acbg);color:var(--ac);border-radius:8px;padding:8px 14px;font-weight:500;margin-bottom:4px}
.tree{margin-left:14px;border-left:1px solid var(--bd)}
.cat{position:relative;padding:4px 0 4px 18px}
.cat:before{content:"";position:absolute;left:0;top:26px;width:14px;border-top:1px solid var(--bd)}
.hd{width:100%;display:flex;align-items:center;gap:10px;text-align:left;font-weight:500}
.hd .n{margin-left:auto;font-size:13px;font-weight:400;color:var(--tx2)}
.cat.open .hd{border-color:var(--ac)}
.body{display:none;margin:6px 0 4px 10px;border-left:1px solid var(--bd);padding-left:12px}
.cat.open .body{display:block}
.grp{font-size:13px;color:var(--tx2);margin:10px 0 2px}
.cmd{display:flex;gap:10px;align-items:baseline;padding:4px 0}
code{font:13px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--soft);padding:2px 6px;border-radius:4px;flex:none}
.cmd code{white-space:nowrap}.cmd span{color:var(--tx2);font-size:14px;line-height:1.4}
.ex{font:12px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:var(--ac);margin:0 0 6px 6px;overflow-x:auto;white-space:nowrap}
.v{display:flex;gap:8px;align-items:baseline;margin:3px 0 3px 6px}
.v b{font-size:11px;font-weight:500;color:var(--ac);background:var(--acbg);border-radius:4px;padding:1px 6px;flex:none;width:52px;text-align:center}
.v code.x{flex:1;min-width:0;white-space:pre-wrap;word-break:break-word;font-size:12px}
#t[data-f="u"] .v:not([data-k="u"]),#t[data-f="f"] .v:not([data-k="f"]),#t[data-f="a"] .v:not([data-k="a"]){display:none}
#q{width:100%;font:inherit;font-size:14px;color:var(--tx);background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:8px 10px;margin-bottom:10px}
#q:focus{outline:2px solid var(--ac);outline-offset:-1px}
.hidden{display:none!important}
#info{font-size:13px;color:var(--tx2);margin:0 0 10px}
</style></head><body><main>
<h1>__TITULO__</h1><p class="sub">__SUBTITULO__</p>
<input id="q" type="search" placeholder="Buscar comando, descripción o ejemplo…" autocomplete="off">
<div class="seg" id="s"><button class="on" data-f="">Todas</button><button data-f="u">Ubuntu</button><button data-f="f">Fedora</button><button data-f="a">Arch</button></div>
<p class="note">__NOTA__</p>
<div class="bar"><button id="ex">Expandir todo</button><button id="co">Contraer todo</button></div>
<p id="info"></p>
<div class="root">Linux</div><div class="tree" id="t"></div></main>
<script>
var D=__DATOS__, N=__DISTROS__;
function e(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function pre(x){return (x[0]=='#'?'':'$ ')+e(x)}
var t=document.getElementById('t');
D.categorias.forEach(function(c,i){
  var n=0;c.grupos.forEach(function(g){n+=g.comandos.length});
  var h='<div class="cat"><button class="hd" aria-expanded="false">'+(i+1)+'. '+e(c.nombre)+'<span class="n">'+n+'</span></button><div class="body">';
  c.grupos.forEach(function(g){
    h+='<div class="grp">'+e(g.nombre)+'</div>';
    g.comandos.forEach(function(m){
      h+='<div class="cmd"><code>'+e(m.cmd)+'</code><span>'+e(m.desc||'')+'</span></div>';
      if(m.variantes){
        h+=['u','f','a'].map(function(k){return m.variantes[k]?'<div class="v" data-k="'+k+'"><b>'+N[k]+'</b><code class="x">'+e(m.variantes[k])+'</code></div>':''}).join('');
      } else if(m.ejemplo){
        h+='<div class="ex">'+pre(m.ejemplo)+'</div>';
      }
    });
  });
  t.insertAdjacentHTML('beforeend',h+'</div></div>');
});
function all(v){document.querySelectorAll('.cat').forEach(function(x){x.classList.toggle('open',v);x.firstChild.setAttribute('aria-expanded',v)})}
t.addEventListener('click',function(x){var b=x.target.closest('.hd');if(!b)return;var o=b.parentNode.classList.toggle('open');b.setAttribute('aria-expanded',o)});
document.getElementById('s').addEventListener('click',function(x){var b=x.target.closest('button');if(!b)return;
  this.querySelectorAll('button').forEach(function(y){y.classList.toggle('on',y===b)});t.setAttribute('data-f',b.getAttribute('data-f'));filtrar()});
document.getElementById('ex').onclick=function(){all(true)};document.getElementById('co').onclick=function(){all(false)};
var q=document.getElementById('q');
q.addEventListener('input',filtrar);
function filtrar(){
  var txt=q.value.trim().toLowerCase(), hits=0;
  document.querySelectorAll('.cat').forEach(function(cat){
    var visible=false;
    cat.querySelectorAll('.cmd').forEach(function(cmd){
      var bloque=cmd.nextElementSibling, txt2=cmd.textContent.toLowerCase();
      while(bloque&&bloque.classList.contains('ex')===false&&bloque.classList.contains('v')===false){bloque=bloque.nextElementSibling}
      if(bloque)txt2+=' '+bloque.textContent.toLowerCase();
      var ok=!txt||txt2.indexOf(txt)>-1;
      cmd.style.display=ok?'':'none';
      if(bloque){var sig=bloque;while(sig&&(sig.classList.contains('ex')||sig.classList.contains('v'))){sig.style.display=ok?'':'none';sig=sig.nextElementSibling}}
      if(ok)visible=true;
    });
    cat.querySelectorAll('.grp').forEach(function(g){
      var tiene=false,g2=g.nextElementSibling;
      while(g2&&g2.classList.contains('cmd')){if(g2.style.display!=='none')tiene=true;g2=g2.nextElementSibling}
      g.style.display=tiene?'':'none';
    });
    cat.style.display=visible?'':'none';
    if(visible&&txt){cat.classList.add('open');cat.firstChild.setAttribute('aria-expanded','true')}
    hits+=visible?1:0;
  });
  document.getElementById('info').textContent=txt?(hits+' categoría(s) coinciden'):'';
}
t.firstChild.classList.add('open');
</script></body></html>
"""


def export_html(datos: dict[str, Any], destino: str | Path) -> Path:
    """Escribe un HTML autocontenido (funciona sin conexión)."""
    destino = Path(destino)
    pagina = (
        PLANTILLA_HTML.replace("__TITULO__", html.escape(datos.get("titulo", "Comandos Linux")))
        .replace("__SUBTITULO__", html.escape(datos.get("subtitulo", "")))
        .replace("__NOTA__", html.escape(datos.get("nota", "")))
        .replace("__DISTROS__", json.dumps(datos.get("distros", {}), ensure_ascii=False))
        .replace("__DATOS__", json.dumps(datos, ensure_ascii=False))
    )
    destino.write_text(pagina, encoding="utf-8")
    return destino


# --------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------


def export_md(datos: dict[str, Any], destino: str | Path) -> Path:
    """Escribe la chuleta completa en Markdown."""
    destino = Path(destino)
    lineas: list[str] = []

    lineas.append(f"# {datos.get('titulo', 'Comandos Linux')}")
    lineas.append("")
    lineas.append(datos.get("subtitulo", ""))
    lineas.append("")
    if datos.get("nota"):
        lineas.append(datos["nota"])
        lineas.append("")

    for indice, categoria in enumerate(datos.get("categorias", []), start=1):
        lineas.append(f"## {indice}. {categoria['nombre']}")
        lineas.append("")
        for grupo in categoria.get("grupos", []):
            lineas.append(f"### {grupo['nombre']}")
            lineas.append("")
            for cmd in grupo.get("comandos", []):
                lineas.append(f"**`{cmd.get('cmd', '')}`** — {cmd.get('desc', '')}")
                lineas.append("")
                variantes = cmd.get("variantes")
                if variantes:
                    for clave, texto in variantes.items():
                        etiqueta = datos.get("distros", {}).get(clave, clave)
                        lineas.append(f"- **{etiqueta}:** `{texto}`")
                    lineas.append("")
                elif cmd.get("ejemplo"):
                    lineas.append("```bash")
                    lineas.append(cmd["ejemplo"])
                    lineas.append("```")
                    lineas.append("")

    destino.write_text("\n".join(lineas).rstrip() + "\n", encoding="utf-8")
    return destino
