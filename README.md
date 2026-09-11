# 🎯 OSCP+ EXAM COPILOT — Read Me First

A complete, offline toolkit for solving OSCP+ machines: a searchable knowledge base + visual flowcharts + a command generator + automation scripts + a study tracker + a report template. Everything is **self-contained and works offline** (built for the exam VM).

---

## 📦 What's in this folder

### Open these in a browser (offline, no internet needed)
| File | What it is | When you use it |
|---|---|---|
| **OSCP-KB.html** | The knowledge base — 10 volumes, ~370 tagged sections. Sidebar nav + full-text search + tag pills. | The reference: *what do I run, and why?* |
| **OSCP-Flowcharts.html** | 9 visual attack-flow diagrams (methodology, enum, web, Linux/Win privesc, AD, pivoting, exam-day, stuck). | *Where do I go next?* |
| **OSCP-CommandGen.html** | Click-to-generate: set your IP → pick a category → **Copy** the ready-to-run command (reverse shells, transfer, enum, msfvenom, privesc downloads). | *Give me the exact command, IP already filled in.* |
| **OSCP-Study-Tracker.html** | Log each practice box → auto-charts your weakest stage. | Prep: *what should I drill next?* |

### Run these on Kali (exam-safe automation — enumeration/setup only, NOT exploitation)
| File | What it is |
|---|---|
| **oscp.sh** | Bash helper. `source ~/oscp.sh` once → tiny commands: `ws · enum · spray · hosts · flags · shell · transfer · serve · listen · tun`. |
| **oscp.py** | Python port of the same helper. `./oscp.py enum <ip>`, `./oscp.py shell bash`, etc. (use whichever you prefer). |

### Fill these in
| File | What it is |
|---|---|
| **REPORT-TEMPLATE.md** | Fillable exam-report skeleton — fill it AS YOU GO (per-host blocks, proof screenshots, .7z submission checklist). |

### Source & build (edit → rebuild)
- `VOL-0` … `VOL-9` `.md` — the knowledge base source, ordered for use (each title's "Volume N" is a stable ID for cross-references).
- `OSCP-KB-COMPLETE.md` — all volumes merged into one searchable Markdown file.
- `build_html.py` — regenerates `OSCP-KB.html` + `OSCP-KB-COMPLETE.md`. Run after editing any `VOL-*.md`:
  ```
  cd ~/Downloads/OSCP-KB && python3 build_html.py
  ```

---

## 🗺️ The volumes (reading order)
`①` ⭐ **Exam War Room** (open first on exam day — scoreboard, playbooks, checkpoints, `[EXAM-SCRIPTS]`) ·
`②` 👶 **Foundations** (Kali setup, glossary, `[CONCEPTS]`, walkthroughs) ·
`③` 🧭 **Mindset & Methodology** (golden rules, master methodology, time, reporting) ·
`④` 🔎 **Enumeration & Nmap** ·
`⑤` 🌐 **Web & SQLi** ·
`⑥` 💥 **Access · Shells · Transfer · Creds** ·
`⑦` ⬆️ **Privilege Escalation** ·
`⑧` 🏰 **Active Directory & Pivoting** ·
`⑨` 🧰 **Found-X · Troubleshooting · Toolbox · Reference** ·
`⑩` 📚 **Syllabus Extras & Exam-Day Flow**.

---

## 🚀 How to use it (the loop)
1. **New box** → glance at **OSCP-Flowcharts.html** for the phase, and open **OSCP-KB.html**.
2. **Need a command** → search its `[TAG]` in the KB, or click it in **OSCP-CommandGen.html** and Copy.
3. **On Kali** → `source ~/oscp.sh` (or use `oscp.py`) → `enum $T`, `spray`, `shell`, `transfer`.
4. **Found something** → jump to its `[FOUND-*]` entry. **Stuck 15–30 min** → `[STUCK-PROTOCOL]`. **Broken** → `[TROUBLESHOOTING-QUICK]`.
5. **Log every command** for the report; **screenshot proof** (flag + `whoami`/`id` + `ip`) the instant you get it.
6. **Fill REPORT-TEMPLATE.md as you go.**

**Exam day:** open `[EXAM-WAR-ROOM]` first (scoreboard + 3 machine playbooks + hour-by-hour checkpoints). Keep `[FINAL-DAY-QUICK-REFERENCE]` handy.

---

## ⚠️ Honest notes
- **Verify exact tool flags** (netexec/impacket/ligolo/hashcat modes) against your installed Kali versions before exam day — syntax drifts.
- **This is a copilot, not autopilot.** The commands are here; the skill is in the reps. Do **~40–60 practice boxes (AD-weighted)** with this open, logging them in the Study Tracker — that's what turns the guide into a pass.
- **Exam rules (verify on the current official guide):** 100 pts / 70 to pass · 40-pt AD set + 3×20 standalones · no bonus · Metasploit ONE target · sqlmap/Responder-poisoning/AI **banned** · your own enumeration scripts **allowed** · report required in a no-password `.7z` within 24h.

Now go break things. 🎯
