#!/usr/bin/env python3
"""Build a single self-contained offline HTML knowledge base from the VOL-*.md files.
No external libraries, no network. Run:  python3 build_html.py
Output: OSCP-KB.html
"""
import os, re, html, glob, json

HERE = os.path.dirname(os.path.abspath(__file__))

# Ordered for USE (exam-day copilot flow). The number in each file's title is a
# stable internal ID used by cross-references; the sidebar order below is the reading order.
VOLS = [
    ("VOL-8_EXAM-WAR-ROOM.md",                            "① ⭐ EXAM WAR ROOM — open first on exam day"),
    ("VOL-9_BEGINNER-FOUNDATIONS.md",                     "② 👶 Foundations — setup · glossary · walkthroughs"),
    ("VOL-0_INDEX-MINDSET-METHODOLOGY.md",                "③ 🧭 Mindset · Golden Rules · Methodology"),
    ("VOL-1_ENUMERATION-NMAP.md",                         "④ 🔎 Enumeration & Nmap"),
    ("VOL-2_WEB-SQLI.md",                                 "⑤ 🌐 Web & SQL Injection"),
    ("VOL-3_ACCESS-SHELLS-TRANSFER-CREDS.md",             "⑥ 💥 Access · Shells · Transfer · Creds"),
    ("VOL-4_PRIVESC-LINUX-WINDOWS.md",                    "⑦ ⬆️ Privilege Escalation (Linux & Windows)"),
    ("VOL-5_ACTIVE-DIRECTORY-PIVOTING.md",                "⑧ 🏰 Active Directory & Pivoting"),
    ("VOL-6_LOOKUPS-TROUBLESHOOTING-REFERENCE.md",        "⑨ 🧰 Found-X · Troubleshooting · Toolbox · Top-100s"),
    ("VOL-7_SYLLABUS-CLIENTSIDE-AV-MSF-CLOUD-EXAMFLOW.md","⑩ 📚 Syllabus Extras & Exam-Day Flow"),
]

_slug_seen = {}
def slugify(text):
    s = re.sub(r'`', '', text)
    s = re.sub(r'\*\*', '', s)
    s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', s)  # link text
    s = s.lower().strip()
    s = re.sub(r'[^a-z0-9\[\]\-_ ]+', '', s)
    s = re.sub(r'[\s_]+', '-', s).strip('-')
    if not s:
        s = 'sec'
    n = _slug_seen.get(s, 0)
    _slug_seen[s] = n + 1
    return s if n == 0 else f"{s}-{n}"

_link = re.compile(r'\[([^\]]+)\]\((https?://[^)]+)\)')
_bold = re.compile(r'\*\*([^*]+)\*\*')

def inline(text):
    """Escape + apply inline code, links, bold. Code spans are protected first."""
    parts = re.split(r'(`[^`]*`)', text)
    out = []
    for p in parts:
        if p.startswith('`') and p.endswith('`') and len(p) >= 2:
            inner = p[1:-1]
            cls = ' class="tag"' if re.match(r'^\[[A-Z0-9][A-Z0-9\-\+/#]*\]$', inner) else ''
            out.append(f'<code{cls}>' + html.escape(inner) + '</code>')
        else:
            e = html.escape(p)
            e = _link.sub(lambda m: f'<a href="{html.escape(m.group(2))}" target="_blank" rel="noopener">{html.escape(m.group(1))}</a>', e)
            # bold: operate on escaped text; ** survive escaping
            e = _bold.sub(lambda m: '<strong>' + m.group(1) + '</strong>', e)
            out.append(e)
    return ''.join(out)

def convert(md, vol_idx):
    lines = md.split('\n')
    out = []
    toc = []            # (level, id, text)
    i = 0
    N = len(lines)
    list_stack = []     # list of ('ul'|'ol', indent)

    def close_lists(to_indent=-1):
        while list_stack and list_stack[-1][1] > to_indent:
            tag = list_stack.pop()[0]
            out.append(f'</{tag}>')

    while i < N:
        line = lines[i]

        # fenced code
        m = re.match(r'^```(.*)$', line)
        if m:
            close_lists()
            code = []
            i += 1
            while i < N and not lines[i].startswith('```'):
                code.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            out.append('<pre><code>' + html.escape('\n'.join(code)) + '</code></pre>')
            continue

        # horizontal rule
        if re.match(r'^\s*---+\s*$', line):
            close_lists()
            out.append('<hr>')
            i += 1
            continue

        # headings
        hm = re.match(r'^(#{1,6})\s+(.*)$', line)
        if hm:
            close_lists()
            level = len(hm.group(1))
            text = hm.group(2).strip()
            hid = slugify(f"v{vol_idx}-{text}")
            # the repeated "OSCP+ KNOWLEDGE BASE — VOLUME N" H1 → small muted kicker (declutter), not a giant title, not in nav
            if level == 1 and text.upper().startswith('OSCP+ KNOWLEDGE BASE'):
                out.append(f'<div class="volkicker" id="{hid}">{inline(text)}</div>')
                i += 1
                continue
            if level <= 3:
                toc.append((level, hid, text))
            out.append(f'<h{level} id="{hid}">{inline(text)}<a class="anchor" href="#{hid}">#</a></h{level}>')
            i += 1
            continue

        # table (header line followed by |---| line)
        if line.lstrip().startswith('|') and i + 1 < N and re.match(r'^\s*\|?[\s:|-]+\|[\s:|-]*$', lines[i+1]):
            close_lists()
            def cells(row):
                r = row.strip()
                if r.startswith('|'): r = r[1:]
                if r.endswith('|'): r = r[:-1]
                return [c.strip() for c in r.split('|')]
            header = cells(line)
            i += 2  # skip header + separator
            out.append('<div class="tablewrap"><table><thead><tr>' +
                       ''.join(f'<th>{inline(c)}</th>' for c in header) +
                       '</tr></thead><tbody>')
            while i < N and lines[i].lstrip().startswith('|'):
                row = cells(lines[i])
                out.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in row) + '</tr>')
                i += 1
            out.append('</tbody></table></div>')
            continue

        # blockquote
        if re.match(r'^\s*>\s?', line):
            close_lists()
            buf = []
            while i < N and re.match(r'^\s*>\s?', lines[i]):
                buf.append(re.sub(r'^\s*>\s?', '', lines[i]))
                i += 1
            out.append('<blockquote>' + inline(' '.join(buf)) + '</blockquote>')
            continue

        # list items (ordered / unordered, with indent nesting)
        lm = re.match(r'^(\s*)([-*]|\d+\.)\s+(.*)$', line)
        if lm:
            indent = len(lm.group(1))
            kind = 'ol' if re.match(r'\d+\.', lm.group(2)) else 'ul'
            if not list_stack or indent > list_stack[-1][1]:
                out.append(f'<{kind}>')
                list_stack.append((kind, indent))
            else:
                close_lists(indent)
                if not list_stack or list_stack[-1][1] < indent:
                    out.append(f'<{kind}>')
                    list_stack.append((kind, indent))
            out.append('<li>' + inline(lm.group(3)) + '</li>')
            i += 1
            continue

        # blank line
        if line.strip() == '':
            close_lists()
            i += 1
            continue

        # paragraph
        close_lists()
        out.append('<p>' + inline(line) + '</p>')
        i += 1

    close_lists()
    return '\n'.join(out), toc


_tag_in_head = re.compile(r'\[([A-Z0-9][A-Z0-9\-\+\*/ ]*?)\]')

def parse_sections(md, vlabel):
    """Split a volume's markdown into sections keyed by their [TAG] headings.
    A new section starts at any heading (#..######) whose text contains a [TAG].
    Returns list of {t:title, g:[tags], b:body, v:vlabel}."""
    lines = md.split('\n')
    secs = []
    cur = None
    for ln in lines:
        hm = re.match(r'^(#{1,6})\s+(.*)$', ln)
        if hm and '[' in hm.group(2) and _tag_in_head.search(hm.group(2)):
            if cur:
                secs.append(cur)
            title = re.sub(r'`', '', hm.group(2)).strip()
            tags = [t.strip() for t in _tag_in_head.findall(hm.group(2))]
            cur = {"t": title, "g": tags, "b": "", "v": vlabel, "_buf": []}
        elif cur is not None:
            cur["_buf"].append(ln)
    if cur:
        secs.append(cur)
    out = []
    for s in secs:
        body = "\n".join(s.pop("_buf")).strip("\n")
        body = re.sub(r'\n{3,}', '\n\n', body).strip()
        if len(body) > 4000:
            body = body[:4000].rstrip() + "\n… (open OSCP-KB.html for the rest)"
        s["b"] = body
        out.append(s)
    return out


def inject_copilot(all_sections):
    p = os.path.join(HERE, "OSCP-Copilot.html")
    if not os.path.exists(p):
        print("(skip) OSCP-Copilot.html not found — not injecting KB")
        return
    src = open(p, encoding="utf-8").read()
    data = json.dumps({"sections": all_sections}, ensure_ascii=False, separators=(",", ":"))
    data = data.replace("</", "<\\/")  # keep the </script> parser safe
    new, n = re.subn(
        r'(<script id="kb-data" type="application/json">).*?(</script>)',
        lambda m: m.group(1) + data + m.group(2),
        src, count=1, flags=re.S)
    if n:
        open(p, "w", encoding="utf-8").write(new)
        print(f"Injected {len(all_sections)} KB sections into OSCP-Copilot.html ({len(new)//1024} KB)")
    else:
        print("(warn) kb-data marker not found in OSCP-Copilot.html")


def main():
    sections_html = []
    nav_html = []
    all_sections = []
    for vi, (fname, label) in enumerate(VOLS):
        path = os.path.join(HERE, fname)
        if not os.path.exists(path):
            print("MISSING", fname); continue
        md = open(path, encoding='utf-8').read()
        vlabel = "Vol " + (re.search(r'VOL-(\d)', fname).group(1) if re.search(r'VOL-(\d)', fname) else "?")
        all_sections.extend(parse_sections(md, vlabel))
        body, toc = convert(md, vi)
        sections_html.append(f'<section class="vol" id="vol-{vi}" data-vol="{vi}">{body}</section>')
        # nav: top item = volume; show only jump-points = all H1 dividers + TAGGED H2s
        # (drops prose sub-headings like "What the whole process looks like" that cluttered the nav)
        _navtag = re.compile(r'\[[A-Z0-9][A-Z0-9\-\+\*/ ]*\]')
        items = []
        for level, hid, text in toc:
            if level == 1 or (level == 2 and _navtag.search(text)):
                cls = 'lvl1' if level == 1 else 'lvl2'
                items.append(f'<a class="navlink {cls}" href="#{hid}">{html.escape(re.sub(r"`","",text))}</a>')
        collapsed = '' if vi == 0 else ' collapsed'
        nav_html.append(
            f'<div class="navgroup{collapsed}" data-vol="{vi}">'
            f'<button class="navvol" onclick="toggleVol({vi})"><span class="tw">▾</span><span class="navvol-t">{html.escape(label)}</span></button>'
            f'<div class="navitems" id="navitems-{vi}">{"".join(items)}</div></div>')

    content = "\n".join(sections_html)
    nav = "\n".join(nav_html)

    tpl = TEMPLATE.replace("{{NAV}}", nav).replace("{{CONTENT}}", content)
    outp = os.path.join(HERE, "OSCP-KB.html")
    open(outp, "w", encoding="utf-8").write(tpl)
    print("Wrote", outp, f"({len(tpl)//1024} KB)")

    # keep the merged markdown in the same reading order
    merged = []
    for fname, _ in VOLS:
        p = os.path.join(HERE, fname)
        if os.path.exists(p):
            merged.append(open(p, encoding="utf-8").read())
    open(os.path.join(HERE, "OSCP-KB-COMPLETE.md"), "w", encoding="utf-8").write("\n\n".join(merged))
    print("Wrote OSCP-KB-COMPLETE.md (reading order)")

    # bake the whole KB into the Copilot so it can search real KB text offline
    inject_copilot(all_sections)


TEMPLATE = r"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OSCP+ Knowledge Base</title>
<style>
:root{
  --bg:#0d1117; --bg2:#0a0d12; --panel:#11161d; --panel2:#161c24; --hover:#1b2531;
  --text:#c9d3de; --head:#e8eef5; --muted:#7d8794; --faint:#5a6472;
  --accent:#4f9cf9; --accent-soft:#1a2942; --accent2:#e3a008;
  --border:#20262e; --border2:#2a323c;
  --code-bg:#0a0e13; --code-text:#c9d3de;
  --tag-bg:#0f2a1c; --tag-text:#56d364; --tag-bd:#1c3f2a;
  --hl:#7a5c00; --hl-cur:#e3a008;
  --shadow:0 1px 3px rgba(0,0,0,.4);
}
html[data-theme="light"]{
  --bg:#ffffff; --bg2:#f6f8fa; --panel:#f6f8fa; --panel2:#eef1f4; --hover:#e7ecf1;
  --text:#24292f; --head:#0f1419; --muted:#57606a; --faint:#8b949e;
  --accent:#0969da; --accent-soft:#ddf0ff; --accent2:#9a6700;
  --border:#d8dee4; --border2:#cdd5dd;
  --code-bg:#f2f4f7; --code-text:#24292f;
  --tag-bg:#e6f7ec; --tag-text:#1a7f37; --tag-bd:#c3ead0;
  --hl:#fff3b0; --hl-cur:#e3a008;
  --shadow:0 1px 3px rgba(140,149,159,.25);
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:var(--bg);color:var(--text);
  font:15.5px/1.68 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  -webkit-font-smoothing:antialiased;}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
::selection{background:var(--accent-soft)}

#layout{display:flex;min-height:100vh}

/* ---------- Sidebar ---------- */
#sidebar{width:300px;flex:0 0 300px;background:var(--panel);border-right:1px solid var(--border);
  height:100vh;position:sticky;top:0;display:flex;flex-direction:column}
#brand{padding:18px 18px 12px}
#brand .logo{font-size:15px;font-weight:700;color:var(--head);letter-spacing:.2px;display:flex;align-items:center;gap:8px}
#brand .tagline{color:var(--faint);font-size:11.5px;margin-top:3px;letter-spacing:.3px}
#navfilterwrap{padding:0 14px 12px;border-bottom:1px solid var(--border)}
#navfilter{width:100%;padding:9px 12px;background:var(--bg2);border:1px solid var(--border2);
  color:var(--text);border-radius:9px;font-size:13px;outline:none}
#navfilter:focus{border-color:var(--accent)}
#navtools{display:flex;gap:6px;padding:10px 14px 4px}
#navtools button{flex:1;background:none;border:1px solid var(--border2);color:var(--muted);
  border-radius:7px;padding:5px 6px;cursor:pointer;font-size:11px}
#navtools button:hover{color:var(--text);border-color:var(--accent)}
#nav{overflow-y:auto;padding:6px 8px 60px;flex:1}
#nav::-webkit-scrollbar{width:9px}#nav::-webkit-scrollbar-thumb{background:var(--border2);border-radius:6px}
.navgroup{margin-bottom:1px}
.navvol{width:100%;text-align:left;background:none;border:none;color:var(--head);
  font-weight:600;font-size:12.5px;padding:8px 8px;cursor:pointer;border-radius:7px;
  display:flex;gap:7px;align-items:center;line-height:1.35}
.navvol:hover{background:var(--hover)}
.navvol .tw{color:var(--faint);font-size:10px;transition:transform .15s;flex:0 0 10px}
.navgroup.collapsed .tw{transform:rotate(-90deg)}
.navgroup.collapsed .navitems{display:none}
.navitems{display:flex;flex-direction:column;padding:1px 0 8px 3px;margin-left:8px;
  border-left:1px solid var(--border)}
.navlink{color:var(--muted);font-size:12px;padding:4px 10px;border-radius:6px;white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis;border-left:2px solid transparent;margin-left:-1px}
.navlink:hover{background:var(--hover);color:var(--text);text-decoration:none}
.navlink.lvl1{color:var(--head);font-weight:700;margin-top:11px;font-size:12.5px}
.navlink.lvl1:first-child{margin-top:2px}
.navlink.lvl2{padding-left:22px;font-size:11.5px;color:var(--muted);border-left:1px solid var(--border)}
.navlink.lvl2:hover,.navlink.lvl2.active{border-left-color:var(--accent)}
.navlink.active{background:var(--accent-soft);color:var(--accent);border-left-color:var(--accent)}

/* ---------- Main ---------- */
#main{flex:1;min-width:0;display:flex;flex-direction:column;background:var(--bg)}
#topbar{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--bg) 88%,transparent);
  backdrop-filter:saturate(1.4) blur(8px);border-bottom:1px solid var(--border);
  padding:11px 26px;display:flex;gap:12px;align-items:center}
#searchwrap{position:relative;flex:1;max-width:620px}
#searchwrap .ic{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--faint);font-size:14px}
#search{width:100%;padding:9px 12px 9px 34px;background:var(--panel2);border:1px solid var(--border2);
  color:var(--text);border-radius:9px;font-size:14px;outline:none}
#search:focus{border-color:var(--accent);background:var(--bg2)}
#count{color:var(--muted);font-size:12px;min-width:64px;text-align:right;font-variant-numeric:tabular-nums}
.iconbtn{background:var(--panel2);color:var(--muted);border:1px solid var(--border2);
  border-radius:9px;width:38px;height:38px;cursor:pointer;font-size:15px;display:inline-flex;
  align-items:center;justify-content:center}
.iconbtn:hover{color:var(--text);border-color:var(--accent)}

#content{padding:34px 44px 140px;max-width:860px;margin:0 auto;width:100%}
#content h1{font-size:23px;font-weight:700;color:var(--head);letter-spacing:-.2px;
  margin:8px 0 18px;padding-bottom:12px;border-bottom:1px solid var(--border);line-height:1.3}
.vol + .vol h1, #content h1.volstart{margin-top:56px}
.volkicker{font-size:10.5px;font-weight:700;letter-spacing:1.4px;color:var(--faint);text-transform:uppercase;
  margin:58px 0 4px;padding-top:22px;border-top:1px solid var(--border)}
.vol:first-child .volkicker{margin-top:4px;border-top:none;padding-top:0}
#content h2{font-size:18px;font-weight:650;color:var(--head);margin:34px 0 10px;
  padding-left:11px;border-left:3px solid var(--accent);line-height:1.35}
#content h3{font-size:15px;font-weight:650;color:var(--accent2);margin:24px 0 8px}
#content h4{font-size:13.5px;font-weight:650;color:var(--head);margin:16px 0 6px;
  text-transform:uppercase;letter-spacing:.4px}
.vol{scroll-margin-top:66px}
#content h1,#content h2,#content h3,#content h4{scroll-margin-top:70px;position:relative}
.anchor{opacity:0;margin-left:8px;color:var(--faint);font-weight:400;font-size:.75em}
h1:hover .anchor,h2:hover .anchor,h3:hover .anchor{opacity:1}
#content p{margin:9px 0}
#content ul,#content ol{margin:9px 0;padding-left:24px}
#content li{margin:4px 0}
#content li::marker{color:var(--faint)}

/* inline code + tag pills */
code{background:var(--code-bg);color:var(--code-text);padding:1px 5px;border-radius:5px;
  font:12.5px/1.45 "SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;
  border:1px solid var(--border);white-space:nowrap}
code.tag{background:var(--tag-bg);color:var(--tag-text);border:1px solid var(--tag-bd);
  font-weight:600;letter-spacing:.2px;cursor:pointer}
code.tag:hover{filter:brightness(1.15)}

pre{background:var(--code-bg);border:1px solid var(--border);border-radius:11px;padding:14px 16px;
  overflow:auto;margin:14px 0;box-shadow:var(--shadow)}
pre code{background:none;border:none;padding:0;color:var(--code-text);white-space:pre;
  font-size:12.5px;line-height:1.55}
pre::-webkit-scrollbar{height:9px}pre::-webkit-scrollbar-thumb{background:var(--border2);border-radius:6px}

blockquote{border-left:3px solid var(--accent2);background:var(--panel);margin:14px 0;
  padding:11px 16px;border-radius:0 9px 9px 0;color:var(--muted);font-size:14.5px}
blockquote strong{color:var(--head)}

.tablewrap{overflow-x:auto;margin:14px 0;border:1px solid var(--border);border-radius:10px;box-shadow:var(--shadow)}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border-bottom:1px solid var(--border);border-right:1px solid var(--border);padding:8px 12px;text-align:left;vertical-align:top}
tr td:last-child,tr th:last-child{border-right:none}
tbody tr:last-child td{border-bottom:none}
th{background:var(--panel2);font-weight:650;color:var(--head)}
tbody tr:nth-child(even){background:var(--bg2)}
tbody tr:hover{background:var(--hover)}

hr{border:none;border-top:1px solid var(--border);margin:30px 0}
mark{background:var(--hl);color:var(--head);padding:0 1px;border-radius:2px}
mark.current{background:var(--hl-cur);color:#111;box-shadow:0 0 0 2px var(--hl-cur)}

#totop{position:fixed;right:26px;bottom:26px;z-index:30;background:var(--accent);color:#fff;border:none;
  width:42px;height:42px;border-radius:11px;font-size:17px;cursor:pointer;display:none;box-shadow:0 6px 18px rgba(0,0,0,.45)}
#menuBtn{display:none}

@media(max-width:900px){
  #sidebar{position:fixed;z-index:50;left:-320px;transition:left .2s;box-shadow:6px 0 24px rgba(0,0,0,.5)}
  #sidebar.open{left:0}
  #menuBtn{display:inline-flex}
  #content{padding:20px 18px 120px}
  #topbar{padding:10px 14px}
}
</style>
</head>
<body>
<div id="layout">
  <aside id="sidebar">
    <div id="brand">
      <div class="logo">🎯 OSCP+ Knowledge Base</div>
      <div class="tagline">Offline · self-contained · press / to search</div>
    </div>
    <div id="navfilterwrap">
      <input id="navfilter" placeholder="Filter sections…">
      <div id="navtools">
        <button onclick="expandAll(true)">Expand all</button>
        <button onclick="expandAll(false)">Collapse all</button>
      </div>
    </div>
    <nav id="nav">{{NAV}}</nav>
  </aside>
  <div id="main">
    <div id="topbar">
      <button id="menuBtn" class="iconbtn" onclick="document.getElementById('sidebar').classList.toggle('open')">☰</button>
      <div id="searchwrap">
        <span class="ic">🔎</span>
        <input id="search" placeholder="Search everything…   Enter ↵ next · Shift+Enter prev">
      </div>
      <span id="count"></span>
      <button class="iconbtn" onclick="clearSearch()" title="Clear search">✕</button>
      <button class="iconbtn" id="themeBtn" onclick="toggleTheme()" title="Toggle light/dark">◐</button>
    </div>
    <main id="content">{{CONTENT}}</main>
  </div>
</div>
<button id="totop" onclick="window.scrollTo({top:0,behavior:'smooth'})" title="Back to top">↑</button>

<script>
function toggleVol(i){document.querySelector('.navgroup[data-vol="'+i+'"]').classList.toggle('collapsed');}
function expandAll(open){document.querySelectorAll('.navgroup').forEach(g=>g.classList.toggle('collapsed',!open));}

const navfilter=document.getElementById('navfilter');
navfilter.addEventListener('input',()=>{
  const q=navfilter.value.toLowerCase().trim();
  document.querySelectorAll('.navgroup').forEach(g=>{
    let any=false;
    g.querySelectorAll('.navlink').forEach(a=>{
      const hit=!q||a.textContent.toLowerCase().includes(q);
      a.style.display=hit?'':'none'; if(hit)any=true;
    });
    g.style.display=(!q||any)?'':'none';
    if(q)g.classList.remove('collapsed');
  });
});

const links=[...document.querySelectorAll('.navlink')];
const map={};links.forEach(a=>{map[a.getAttribute('href').slice(1)]=a;});
const heads=[...document.querySelectorAll('#content h1,#content h2')];
const obs=new IntersectionObserver(es=>{
  es.forEach(e=>{if(e.isIntersecting){const id=e.target.id;
    links.forEach(l=>l.classList.remove('active'));
    if(map[id]){map[id].classList.add('active');
      const grp=map[id].closest('.navgroup'); if(grp)grp.classList.remove('collapsed');
      map[id].scrollIntoView({block:'nearest'});}}});
},{rootMargin:'-64px 0px -78% 0px'});
heads.forEach(h=>obs.observe(h));

const content=document.getElementById('content');
const searchBox=document.getElementById('search');
const countEl=document.getElementById('count');
let marks=[],cur=-1;
function clearMarks(){marks.forEach(m=>{const p=m.parentNode;p.replaceChild(document.createTextNode(m.textContent),m);p.normalize();});marks=[];cur=-1;countEl.textContent='';}
function clearSearch(){searchBox.value='';clearMarks();searchBox.focus();}
function doSearch(){
  clearMarks();
  const q=searchBox.value.trim();
  if(q.length<2)return;
  const rx=new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'),'gi');
  const walker=document.createTreeWalker(content,NodeFilter.SHOW_TEXT,{acceptNode:n=>{
    if(!n.nodeValue.trim())return NodeFilter.FILTER_REJECT;
    const t=n.parentNode.tagName; if(t==='SCRIPT'||t==='STYLE')return NodeFilter.FILTER_REJECT;
    return rx.test(n.nodeValue)?NodeFilter.FILTER_ACCEPT:NodeFilter.FILTER_REJECT;}});
  const targets=[];let node; while(node=walker.nextNode())targets.push(node);
  targets.forEach(n=>{
    rx.lastIndex=0; const frag=document.createDocumentFragment(); let last=0,s=n.nodeValue,m;
    while(m=rx.exec(s)){
      if(m.index>last)frag.appendChild(document.createTextNode(s.slice(last,m.index)));
      const mk=document.createElement('mark');mk.textContent=m[0];frag.appendChild(mk);marks.push(mk);
      last=m.index+m[0].length; if(m.index===rx.lastIndex)rx.lastIndex++;}
    if(last<s.length)frag.appendChild(document.createTextNode(s.slice(last)));
    n.parentNode.replaceChild(frag,n);});
  countEl.textContent=marks.length?('0/'+marks.length):'0 hits';
  if(marks.length){cur=-1;jump(1);}
}
function jump(dir){
  if(!marks.length)return;
  if(cur>=0)marks[cur].classList.remove('current');
  cur=(cur+dir+marks.length)%marks.length;
  const m=marks[cur];m.classList.add('current');
  m.scrollIntoView({behavior:'smooth',block:'center'});
  countEl.textContent=(cur+1)+'/'+marks.length;
}
let deb;
searchBox.addEventListener('input',()=>{clearTimeout(deb);deb=setTimeout(doSearch,180);});
searchBox.addEventListener('keydown',e=>{
  if(e.key==='Enter'){e.preventDefault();jump(e.shiftKey?-1:1);}
  if(e.key==='Escape'){clearSearch();}});

// click a tag pill -> search for that tag everywhere
content.addEventListener('click',e=>{
  if(e.target.classList.contains('tag')){
    searchBox.value=e.target.textContent;doSearch();}
});

document.addEventListener('keydown',e=>{
  if(e.key==='/'&&document.activeElement!==searchBox&&document.activeElement!==navfilter){e.preventDefault();searchBox.focus();}});

const totop=document.getElementById('totop');
window.addEventListener('scroll',()=>{totop.style.display=window.scrollY>500?'block':'none';});

function toggleTheme(){const h=document.documentElement;const t=h.getAttribute('data-theme')==='dark'?'light':'dark';
  h.setAttribute('data-theme',t);try{localStorage.setItem('oscpkb-theme',t);}catch(e){}}
try{const s=localStorage.getItem('oscpkb-theme');if(s)document.documentElement.setAttribute('data-theme',s);}catch(e){}

document.getElementById('nav').addEventListener('click',e=>{
  if(e.target.classList.contains('navlink')&&window.innerWidth<=900)document.getElementById('sidebar').classList.remove('open');});
</script>
</body>
</html>"""


if __name__ == "__main__":
    main()
