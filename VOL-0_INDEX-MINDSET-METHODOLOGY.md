# OSCP+ KNOWLEDGE BASE — VOLUME 0
## MASTER INDEX · MINDSET · MASTER METHODOLOGY · TIME · REPORTING · PREP

> **How to use this KB:** Everything is tagged like `[SMB-ENUM]`. To find something, `Ctrl+F` the tag or the plain word. Tags are stable across all volumes so you can merge them into one file later (`cat VOL-*.md > OSCP-KB-COMPLETE.md`).
>
> **Source labels used everywhere:**
> `[OFFICIAL OFFSEC]` = from OffSec's own docs/exam guide. `[COMMUNITY]` = repeatedly reported by recent candidates. `[GENERAL]` = standard pentest knowledge/tool docs.
>
> **Info levels:** every big topic has `[QUICK]` (first 30–60s), `[PRACTICAL]` (the actual methodology — most of the value), `[DEEP]` (theory/edge cases — never blocks action).
>
> **Command labels:** `[MUST-MEMORIZE]` (you type it constantly), `[MUST-RECOGNIZE]` (know what it does, look up exact syntax), `[LOOK-UP]` (never memorize, just know it exists).
>
> **📦 Companion files (same folder):** `OSCP-Flowcharts.html` (9 visual attack-flow diagrams — see the next move), `OSCP-CommandGen.html` (click-to-generate any command with your IP filled in), `OSCP-Study-Tracker.html` (log practice boxes → your weakest stage), `oscp.sh` / `oscp.py` (exam-safe automation helper — `[EXAM-SCRIPTS]`). Use the **flowchart/generator for the move & command**, this KB for the **why & detail**.

---

# [NOOB-PRIMER]  👶 READ THIS FIRST if you're new

New to this? These 6 things confuse *everyone* at the start. Learn them once and every command in this guide makes sense.

## 1) `$IP`, `$T`, `$U`, `$P` are PLACEHOLDERS — you replace them
When you see `nmap -p- $T` or `ssh $U@$IP`, you don't type the dollar-sign words literally. You swap in real values:
```
$IP  = YOUR Kali VPN address (see #4)      $T = the TARGET's IP (e.g. 192.168.1.50)
$U   = a username           $P = a password            $DC = domain controller IP
$DOMAIN = domain name (e.g. corp.local)    $H = an NTLM hash
```
So `evil-winrm -i $T -u $U -p $P` becomes `evil-winrm -i 192.168.1.50 -u bob -p Summer2025!`.
*(Tip: set them as shell variables so copy-paste works: `T=192.168.1.50`, then `nmap -p- $T` runs for real.)*
- **Change a value:** just assign again — `T=192.168.1.77` overwrites the old one. `export IP=10.10.14.8` updates your Kali IP.
- **Check a value:** `echo $T` / `echo $IP` (blank line = not set in this terminal).
- **⚠️ Per-terminal:** variables only exist in the tab you set them in. New tab → they're empty → set again. Best practice: **one box per terminal tab**, set `T` at the top of each tab. Clear one with `unset T`.

## 2) `[FILE-CONVENTIONS]` TWO kinds of files: ones Kali gives you vs ones YOU create
This is the `hashcat -m 5600 netntlmv2.txt rockyou.txt` confusion. The two files are totally different:

| **Ships WITH Kali** (already there, use it) | **YOU create** (save it from the target) |
|---|---|
| `rockyou.txt` → `/usr/share/wordlists/rockyou.txt` | hash files: `netntlmv2.txt`, `tgs.txt`, `asrep.txt` |
| SecLists → `/usr/share/seclists/…` | user lists you found: `users.txt` |
| dir wordlists → `/usr/share/wordlists/dirb/`, `dirbuster/` | anything holding loot from the box |

**Rule of thumb:** in `hashcat -m <mode> <A> <B>` and similar, **the left file (A) is something you made from the target (a hash), the right file (B) is a wordlist Kali provides.** Same for `GetNPUsers -usersfile users.txt` (users.txt = YOUR list) and `hydra -P rockyou.txt` (Kali's list).

**To create a file** you just save text into it:
```
nano netntlmv2.txt                 # opens editor → paste the hash → Ctrl+O save, Ctrl+X exit
echo 'the-hash-here' > hash.txt    # or write it directly
```

**A THIRD kind — OUTPUT files (tools create them for you).** In `nmap ... -oN scans/all-tcp.txt`, that `.txt` is an **output** file — nmap *writes* it when it runs; you don't have it beforehand. Same for any `-o`/`--output`/`>` redirect. So there are three file types total:
```
INPUT, Kali provides   → /usr/share/wordlists/rockyou.txt , SecLists   (you point tools at these)
INPUT, you create      → users.txt , hash.txt                          (you save target loot into these)
OUTPUT, tool creates   → scans/all-tcp.txt (nmap -oN) , loot dumps      (appear AFTER the tool runs)
```
⚠️ **Gotcha:** an output path like `scans/all-tcp.txt` needs the **`scans/` folder to already exist**, or you get `Failed to open ... No such file or directory`. Make it first: `mkdir -p scans` (that's why `[KALI-SETUP]` pre-creates `~/oscp/<box>/{scans,loot,...}`). Or just write to the current dir: `-oN all-tcp.txt`.

## 3) `rockyou.txt` is GZIPPED on a fresh Kali — unzip it once
```
sudo gunzip /usr/share/wordlists/rockyou.txt.gz      # do this one time, ever
# folder empty? install them:  sudo apt install wordlists seclists
```
After that, always point to the full path: `/usr/share/wordlists/rockyou.txt` (writing just `rockyou.txt` only works if you're in that folder).

## 4) `LHOST` / your `$IP` = your VPN address, NOT your home IP
In reverse shells and exploits, "your IP" means your **tun0** (the exam/lab VPN interface), e.g. `10.10.14.x`. Find it:
```
ip addr show tun0        # look for the "inet" line  → that's your $IP / LHOST
```
Using the wrong IP (like eth0) is the #1 reason reverse shells never connect (`[REVERSE-SHELL-NOT-CONNECTING]`).

## 5) `sudo` = run as admin on YOUR Kali; `-Pn`, `-p-` etc. are FLAGS
- `sudo <cmd>` runs a command with root on **your own** Kali (needed for nmap SYN scans, binding low ports). It has nothing to do with the target.
- Words starting with `-` (like `-p-`, `-sCV`, `-u`) are **flags/options** that change how a tool behaves. `[NMAP-QUICK]` explains the ones you need.

## 6) How to read any command in this guide
```
tool      -flag value      $PLACEHOLDER      file
  │           │                 │              │
which     options you       you replace    a wordlist (Kali's)
program   rarely change     with real IP   or a file you made
```
Example: `nmap -p- --min-rate 2000 -Pn -oN scans/all-tcp.txt $T`
= run **nmap**, scan **all ports** (`-p-`), fast (`--min-rate 2000`), skip ping (`-Pn`), **save output** to `scans/all-tcp.txt` (`-oN`), against **the target** (`$T`).

> **You don't need to memorize commands.** You need to (a) recognize what a command *does*, (b) know where to find it here, and (c) swap in your real values. Do boxes, keep this open, and it becomes automatic. Now go to `[BEGINNER-START-HERE]` (Vol 7) for the learning order.

---

# [MASTER-INDEX]

> **Reading order vs. IDs:** The sidebar/steps ①–⑩ below are the order to *use* this KB. The "Volume N" in each title is a **stable ID** that cross-references point to (they don't change when the order does). Follow the ① ② ③ steps; ignore the raw numbers unless you're chasing a `(Vol N)` pointer.

**① ⭐ EXAM WAR ROOM** *(Volume 8 — open FIRST on exam day)*: `[EXAM-WAR-ROOM]` single pane of glass (scoreboard, 3 machine playbooks, hour checkpoints, quick-wins), `[CVE-HITS]`, `[COMMUNITY-ADDENDUM]`, `[BOF-DEPRECATED]`.

**② 👶 FOUNDATIONS** *(Volume 9 — start here if new)*: `[KALI-SETUP]`, `[GLOSSARY]`, `[FIRST-BOX-WALKTHROUGH]` (full Linux + Windows boxes narrated).

**③ 🧭 MINDSET & METHODOLOGY** *(Volume 0 — this file)*: `[NOOB-PRIMER]`, `[OSCP-GOLDEN-RULES]`, `[MASTER-METHODOLOGY]` (stages 0–18), `[PENTESTER-THOUGHT-PROCESS]`, `[TIME-MANAGEMENT]`, `[REPORTING]`, `[MINIMUM-VIABLE-PREP]`, `[7-DAY-PLAN]`, `[READINESS-TEST]`, `[CURRENT-OSCP+]`.

**④ 🔎 ENUMERATION & NMAP** *(Volume 1)*: `[NMAP-*]`, `[ENUM-*]` per service (FTP, SSH, SMTP, DNS, HTTP, SMB, RPC, LDAP, KERBEROS, WINRM, RDP, SNMP, NFS, MSSQL, MYSQL, POSTGRES, REDIS, MONGODB, GIT, unusual ports), `[ENUM-DECISION]`.

**⑤ 🌐 WEB & SQLi** *(Volume 2)*: `[WEB-*]` full methodology + every web vuln; `[SQLI-*]` mini-course (MySQL/MSSQL/Postgres/SQLite).

**⑥ 💥 ACCESS · SHELLS · TRANSFER · CREDS** *(Volume 3)*: `[FOOTHOLD-*]`, `[SHELL-*]`, `[FILETRANSFER-*]`, `[CREDENTIALS-*]`, `[HASH-*]`, `[EXPLOIT-RESEARCH]`.

**⑦ ⬆️ PRIVILEGE ESCALATION** *(Volume 4)*: `[LINUX-PRIVESC-*]`, `[WINDOWS-PRIVESC-*]`.

**⑧ 🏰 ACTIVE DIRECTORY & PIVOTING** *(Volume 5)*: `[AD-*]`, `[PIVOT-*]`.

**⑨ 🧰 FOUND-X · TROUBLESHOOTING · TOOLBOX** *(Volume 6)*: `[FOUND-*]` ("I found X, what now"), `[RABBITHOLE-*]`, `[STUCK-PROTOCOL]`, `[TROUBLESHOOTING-*]`, `[CHAIN-*]`, `[TECH-*]` encyclopedia, `[TOOL-*]` toolbox, `[MACHINE-JOURNAL]`, Top-100s / final-day reference.

**⑩ 📚 SYLLABUS EXTRAS & EXAM FLOW** *(Volume 7)*: `[EXAM-DAY-FLOW]`, `[BEGINNER-START-HERE]`, `[SYLLABUS-MAP]`, `[CLIENTSIDE-*]`, `[PHISHING]`, `[FIXING-EXPLOITS]`, `[AV-EVASION]`, `[TOOL-MSF]`, `[DPI-TUNNELING]`, `[CLOUD-AWS]`.

### Predictable tag families (search any of these)
```
[NMAP] [NMAP-QUICK] [NMAP-TCP] [NMAP-UDP] [NMAP-SCRIPTS] [NMAP-TROUBLESHOOTING]
[ENUM-FTP] [ENUM-SSH] [ENUM-SMTP] [ENUM-DNS] [ENUM-HTTP] [ENUM-SMB] [ENUM-RPC]
[ENUM-LDAP] [ENUM-KERBEROS] [ENUM-WINRM] [ENUM-RDP] [ENUM-SNMP] [ENUM-NFS]
[ENUM-MSSQL] [ENUM-MYSQL] [ENUM-POSTGRES] [ENUM-REDIS] [ENUM-MONGODB] [ENUM-GIT]
[SMB-QUICK] [SMB-ENUM] [SMB-ATTACK] [SMB-TROUBLESHOOTING]
[WEB-QUICK] [WEB-FINGERPRINT] [WEB-CONTENT] [WEB-LFI] [WEB-RFI] [WEB-SSRF]
[WEB-CMDINJ] [WEB-SSTI] [WEB-XXE] [WEB-UPLOAD] [WEB-DESERIALIZE] [WEB-IDOR] [WEB-JWT] [WEB-AUTHBYPASS]
[SQLI] [SQLI-QUICK] [SQLI-DECISION-TREE] [SQLI-MYSQL] [SQLI-MSSQL] [SQLI-POSTGRES] [SQLI-SQLITE] [SQLI-SQLMAP] [SQLI-TROUBLESHOOTING]
[FOOTHOLD-CHECKLIST] [SHELL-QUICK] [REVERSE-SHELL-NOT-CONNECTING] [FILETRANSFER-QUICK]
[LINUX-PRIVESC-QUICK] [LINUX-SUDO] [LINUX-SUID] [LINUX-CRON] [LINUX-CAP] [LINUX-PATH] [LINPEAS-WORKFLOW] [GTFOBINS-WORKFLOW]
[WINDOWS-PRIVESC-QUICK] [WINDOWS-SERVICES] [WINDOWS-TOKENS] [WINDOWS-CREDS] [WINPEAS-WORKFLOW]
[AD-QUICK] [AD-ENUM] [AD-USER] [AD-CREDENTIALS] [KERBEROS-QUICK] [AD-KERBEROAST] [AD-ASREP]
[AD-ACL] [AD-LATERAL] [AD-BLOODHOUND] [AD-ATTACK-PATH]
[PIVOT-QUICK] [PIVOT-CHISEL] [PIVOT-LIGOLO] [PIVOT-SSH] [PIVOT-TROUBLESHOOTING]
[CREDENTIALS-QUICK] [HASH-IDENTIFICATION]
[FOUND-CREDS] [FOUND-SSHKEY] [FOUND-SUID] [FOUND-SUDO] [FOUND-SMB] ... [FOUND-PIVOT]
[STUCK-PROTOCOL] [WHEN-TO-MOVE-ON] [TROUBLESHOOTING-QUICK]
```

---

# PART 0 — [CURRENT-OSCP+] THE EXAM AS OF AUGUST 2026

### [OFFICIAL OFFSEC] What OSCP+ is
- **OSCP+** is what you earn by passing the current PEN-200 exam (structure in place since **Nov 1, 2024**). Passing grants **both** the lifetime **OSCP** and the **OSCP+** designation.
- **OSCP+ expires 3 years** after issuance. The underlying **OSCP never expires**. If you let the "+" lapse you keep OSCP for life. Renew the "+" by: passing a recert exam within 6 months of expiry, passing another qualifying OffSec cert (OSEP/OSWA/OSED/OSEE), or completing OffSec's CPE/PEN-200 continuing-education program.

### [OFFICIAL OFFSEC] Exam format
- **Duration:** 23 hours 45 minutes hands-on, then **24 hours** to write and upload the report.
- **Total 100 points. Pass = 70.**
- **1 Active Directory set = 40 points.** Three chained Windows hosts modelling a small enterprise (typically a domain-joined workstation → member server → domain controller). **You must fully compromise the chain to get the 40** — it is effectively all-or-nothing; a partial AD compromise does not net partial exam-passing value in practice. **Treat AD as the exam.**
- **3 standalone machines = 20 points each (60 total).** Each machine: **10 points for the low-priv flag (`local.txt`)** and **10 points for root/SYSTEM (`proof.txt`)**.
- **Bonus points are GONE.** [OFFICIAL OFFSEC] There is no longer a lab/exercise bonus safety net. **You need a clean 70 on the day.** Practically: AD (40) + two full standalones (40) = 80 → pass. Or AD (40) + one full standalone (20) + two low-priv (20) = 80. **Losing the AD set means you must root all three standalones AND get extra — very hard. Prioritize AD.**

### [OFFICIAL OFFSEC] Tool rules (the ones people fail on)
- **Metasploit / Meterpreter: ONE target only.** You may use MSF exploit/post modules or a Meterpreter payload against a **single machine of your choice** for the whole exam. **Not** on the AD set for pivoting. Auxiliary modules (scanners) are treated more leniently but **don't gamble** — assume MSF = one box, use manual methods everywhere else.
- **Allowed freely:** nmap, nikto, gobuster/feroxbuster/ffuf, Burp Community, netexec/CrackMapExec, impacket, evil-winrm, sqlmap (with restrictions — see below), Chisel/Ligolo/proxychains, hashcat/john, manual exploits, public exploit code you understand.
- **`sqlmap`:** allowed in some contexts but the exam guide restricts automated exploitation tools; **do SQLi manually for the exam** and only lean on sqlmap where explicitly permitted. Confirm on the current exam guide.
- **Banned:** commercial/automated exploitation frameworks beyond the MSF single-target rule, automated AD-exploitation "one-click" tools, spoofing attacks not in scope, and **any AI tools that solve the box for you** (allowed for reference, not for auto-exploitation — check current guide).

### [OFFICIAL OFFSEC] Proof requirements (people LOSE points here)
- Submit the **contents** of `local.txt` and `proof.txt` AND a **screenshot** on each machine showing **the flag + `ipconfig`/`ip a` + `whoami`/`id` in the same shot**. A bare flag string is rejected — it doesn't prove *which host* and *what privilege*.
- Screenshot must be a real screenshot (not copy-paste of text). Show the exploit working.
- The **report is graded.** No report = no pass even if you got 70 points of flags. See `[REPORTING]`.

### [COMMUNITY] What changed vs old OSCP advice (don't reuse stale guides)
- **AD is now the centre of gravity**, not an afterthought. Old "just root 3 boxes + buffer overflow + bonus" advice is dead.
- **No buffer-overflow box** in the current exam focus. Classic 25-point custom-stack-BOF grind is **not** where to spend prep time. (Know basic BOF concept; don't over-drill it.)
- **No bonus points** → margin for error is smaller. **Enumeration discipline > exploit collection.**
- Assumed-breach style AD (you're often given a starting credential/foothold into AD) is the common pattern — **practice from a domain user forward.**

---

# PART 1 — [OSCP-MINDSET] HOW TO THINK

## [QUICK] What the exam actually tests
Not "do you know exploit X." It tests: **can you enumerate thoroughly, notice the one detail that matters, form a hypothesis, test it cheaply, and move on when it fails — for 24 hours without tunnel-visioning.** It's an *enumeration and decision-making* exam wearing an exploitation costume.

## [MEMORIZE vs LOOKUP]
**Make muscle memory (type without thinking):**
- Your nmap two-step (fast all-ports → targeted `-sCV`).
- SMB/AD triage: `nxc smb <ip>`, `nxc smb <ip> -u '' -p ''`, `enum4linux-ng`.
- Reverse shell one-liner + `nc -lvnp`, TTY upgrade (`python3 -c 'import pty...'` + `stty`).
- `sudo -l`, `id`, `find / -perm -4000`, `linpeas`, `winpeas`, `whoami /priv`.
- File transfer: `python3 -m http.server 80` + `wget`/`curl`/`certutil`.
- Kerberoast / AS-REP one-liners, `secretsdump`, `evil-winrm -i ip -u u -p p`.

**Recognize, don't memorize (look up exact flags):** ffuf/feroxbuster syntax, Chisel/Ligolo command chains, hashcat modes, impacket sub-tool flags, ldapsearch filters, sqlmap flags.

**Never memorize:** every GTFOBins entry, every CVE, long exploit payloads. Keep a searchable notes file (this KB) and GTFOBins/HackTricks bookmarks.

## [PENTESTER-MINDSET] How experienced testers think
1. **Enumerate to a hypothesis, not to a list.** Every finding should end with "so I can try ___." If a finding doesn't suggest an action, log it and move on.
2. **Breadth before depth.** Get *all* services and *all* web content mapped before deeply attacking any one thing. The answer is usually in something you haven't looked at yet, not deeper in what you're staring at.
3. **Cheapest test first.** Anonymous login, default creds, known-CVE check — 2 minutes — before writing custom exploits.
4. **Credentials are the universal key.** Every cred you find → try it *everywhere* (SMB, SSH, WinRM, web login, MSSQL, AD, database). Password reuse solves a huge fraction of boxes.
5. **The box was built to be solved with a designed path.** If something feels absurdly hard or needs 0-day skill, you're in a rabbit hole — the intended path is simpler and you missed enumeration.
6. **Write everything down as you go** (see `[MACHINE-JOURNAL]`). Half of "stuck" is "forgot what I already found."

## [HYPOTHESIS-LOOP] The core loop
```
ENUMERATE → NOTICE anomaly/version/misconfig → HYPOTHESIS ("this looks like X, X is exploitable by Y")
→ CHEAP TEST → if works: EXPLOIT; if not: log why, NEXT hypothesis
```
A hypothesis has: a **claim**, a **test**, and a **timebox**. No timebox = rabbit hole.

## [RABBITHOLE-DETECTION] Signs you're in one
- You've spent >30 min and haven't formed a *new* hypothesis, just retried variants of the same one.
- You're editing a public exploit you don't understand, hoping.
- You're brute-forcing something with no evidence it's the path.
- You found something "interesting" and are chasing it because it's interesting, not because evidence points there.
- **Fix:** `[STUCK-PROTOCOL]` (Volume 6 has full version; core: re-enumerate, list untried surfaces, switch target).

---

# [OSCP-GOLDEN-RULES]  (pin these)

1. **AD first, AD hardest — protect the 40 points.** Budget your biggest block of fresh-brain time for the AD set.
2. **Enumerate all ports and all web content before exploiting anything.** Depth-first is the #1 cause of failure.
3. **Every credential gets sprayed everywhere.** New password → SMB, WinRM, SSH, web, MSSQL, RDP, and as other users.
4. **Cheapest test first:** anonymous → default creds → known CVE → manual exploit → custom.
5. **If it needs a 0-day or a miracle, you missed enumeration.** Go back and re-scan / re-read output.
6. **Timebox every hypothesis (15/30 rule).** 15 min no progress → re-read output. 30 min no progress → switch surface or target, note where you were.
7. **Screenshot proof the moment you get a flag** (flag + `id`/`whoami` + `ip`). Do it *now*, not "later."
8. **Take notes continuously.** If it's not written down, it didn't happen. One file per target.
9. **Re-run enumeration after every privilege change** (new user, new host, new network). New access = new attack surface.
10. **Read tool output — actually read it.** The answer is usually already on your screen (a version, a share, a username, a path).
11. **Full TCP port scan always** (`-p-`). The intended service is often on a weird high port.
12. **UDP matters sometimes** (SNMP 161, DNS 53, TFTP 69) — do a quick top-UDP scan, don't obsess.
13. **Manual first for the exam** — Metasploit is one box only. Build manual muscle memory in prep.
14. **Password reuse and weak creds beat exploits** more often than you'd think. Always try the obvious.
15. **When you get a shell, stabilize it before doing anything** (TTY / `stty`). Unstable shells lose you work.
16. **Kerberoast + AS-REP roast every AD engagement** — cheap, high value, no special privileges needed.
17. **BloodHound early in AD.** Collect data as soon as you have any domain creds; let the graph find the path.
18. **Don't over-trust automated scanners.** linpeas/winpeas/nmap scripts miss things and produce false positives — verify manually.
19. **One target's loot unlocks others.** Hashes/keys/passwords from box A are your first move on box B.
20. **Rotate targets to break tunnel vision.** Stuck on standalone #2? Go work AD, come back with fresh eyes.
21. **Verify you understand a public exploit before running it** — wrong target/arch/version can crash the box (costs you a revert and time).
22. **Save every artifact** (scan outputs, hashes, screenshots, exploit code you used) into the target folder immediately.
23. **`whoami /priv` and `sudo -l` are the first thing on any shell.** Free wins live there.
24. **Check for creds in: config files, history, backups, DB, memory, `.git`, home dirs.** Loot is everywhere.
25. **Reverts are free — use them** if a box behaves weirdly (crashed service, prior tester's shell). Don't debug a broken box for an hour.
26. **The report is part of the exam.** Screenshot and command-log as you go; writing it after with no notes is how people fail after passing.
27. **Don't install/one-click auto-exploit AD tools on the exam.** Manual impacket/nxc/BloodHound only.
28. **Sleep and eat.** A 20-minute break at hour 8 beats grinding a rabbit hole for 2 hours. Fatigue = tunnel vision.
29. **If two readings of the evidence differ, do the cheaper test first** rather than debating.
30. **Momentum beats perfection.** A working ugly path > an elegant one you can't finish. Get the flag, clean up in the report.

---

# PART 2/3 — [MASTER-METHODOLOGY] ATTACKING AN UNKNOWN MACHINE

> Each stage: **OBJECTIVE / ASK / FIRST CMDS / DEEPER / OUTPUT THAT MATTERS / NEXT / MISTAKES / RABBIT HOLES / STOP / RETURN / EVIDENCE.** Commands are examples — service-specific detail lives in Volumes 1–5. `$IP` = target.

## [METHOD-0] STAGE 0 — TARGET TRIAGE
- **OBJECTIVE:** decide *what kind* of target and where it sits (standalone vs AD, Windows vs Linux, web-heavy vs service-heavy).
- **ASK:** Is this in the AD set or standalone? Windows or Linux? Is it likely the DC / a pivot? What did the exam brief give me (starting creds, scope, hostnames)?
- **FIRST:** read the exam control panel notes; set up `~/oscp/<target>/` with `scans/ loot/ exploits/ www/ notes.md`.
- **OUTPUT THAT MATTERS:** any provided credential, hostname, domain name.
- **NEXT:** host discovery / port scan.
- **MISTAKES:** starting nmap before reading the brief; not making a folder → losing artifacts.
- **EVIDENCE:** save the brief text into `notes.md`.

## [METHOD-1] STAGE 1 — HOST DISCOVERY
- **OBJECTIVE:** confirm host is up and reachable.
- **FIRST:** `ping -c2 $IP` (TTL≈64 Linux, ≈128 Windows — a hint, not proof). In exam each target IP is given, so mostly skip sweeps.
- **DEEPER (internal/pivot subnet):** `nxc smb 10.10.10.0/24`, `fping -a -g 10.10.10.0/24 2>/dev/null`, nmap `-sn`.
- **OUTPUT:** TTL for OS guess; which hosts alive in a pivoted subnet.
- **RABBIT HOLE:** obsessing over ping when ICMP is filtered — just scan ports (`-Pn`).
- **NEXT:** TCP enumeration.

## [METHOD-2] STAGE 2 — TCP ENUMERATION  → see `[NMAP-TCP]`
- **OBJECTIVE:** every open TCP port + service/version.
- **FIRST (two-step, memorize):**
  ```
  nmap -p- --min-rate 2000 -Pn -oN scans/all-tcp.txt $IP
  nmap -p<csv> -sCV -Pn -oN scans/tcp-scv.txt $IP
  ```
- **OUTPUT THAT MATTERS:** exact versions (→ CVE search), unusual high ports, web ports (80/443/8080/8000/8443…), 445/139 (SMB), 88/389/636/3268 (AD/DC), 5985 (WinRM), 3306/1433/5432 (DBs).
- **NEXT:** per-service enum (Vol 1); web ports → Vol 2.
- **MISTAKES:** scanning only top-1000; trusting `-sV` guess over manual probing.
- **STOP:** once you have all ports + versions. Don't re-scan repeatedly.
- **EVIDENCE:** keep `all-tcp.txt` and `tcp-scv.txt`.

## [METHOD-3] STAGE 3 — UDP ENUMERATION → `[NMAP-UDP]`
- **OBJECTIVE:** catch SNMP/DNS/TFTP/Sip/IKE that TCP misses.
- **FIRST:** `nmap -sU --top-ports 100 --min-rate 1000 -Pn -oN scans/udp.txt $IP`
- **OUTPUT:** 161 SNMP (→ `snmpwalk`, huge loot), 69 TFTP, 53 DNS, 500 IKE.
- **RABBIT HOLE:** full UDP `-p-` scan (slow, rarely needed). Top-100/200 is enough.
- **NEXT:** enumerate any UDP service found.

## [METHOD-4] STAGE 4 — SERVICE ENUMERATION → Volume 1
- **OBJECTIVE:** for each open service: version, auth options, anonymous access, config, loot.
- **ASK per service:** Can I access it anonymously? Are there default creds? Do I have creds that work here? What version → known exploit? What does it *lead to*?
- **NEXT:** feed creds/paths into Initial Access.

## [METHOD-5] STAGE 5 — WEB ENUMERATION → Volume 2 `[WEB-*]`
- **OBJECTIVE:** map the whole app before attacking: tech stack, all content, all params, auth.
- **FIRST:** `whatweb http://$IP`, view source, `/robots.txt`, feroxbuster/ffuf dir brute, vhost brute if a hostname appears.
- **OUTPUT:** CMS + version, login pages, upload forms, params, hidden dirs, vhosts, API endpoints, comments/keys in JS.
- **MISTAKES:** attacking the first form you see before mapping; ignoring vhosts; not adding hostname to `/etc/hosts`.
- **RABBIT HOLE:** brute-forcing dirs for an hour with a giant wordlist; over-fuzzing one param.

## [METHOD-6] STAGE 6 — CREDENTIAL DISCOVERY → `[CREDENTIALS-QUICK]`
- **OBJECTIVE:** collect every username/password/hash/key from all sources so far.
- **ASK:** default creds? creds in configs/DB/git/SNMP/comments? usernames to spray?
- **NEXT:** spray creds across every service (Golden Rule 3).

## [METHOD-7] STAGE 7 — VULNERABILITY IDENTIFICATION → `[EXPLOIT-RESEARCH]`
- **OBJECTIVE:** turn versions/misconfigs into a concrete exploit hypothesis.
- **FIRST:** `searchsploit <product> <version>`, targeted web/GitHub search for `<product> <version> exploit/CVE`.
- **OUTPUT:** a specific, matched exploit (right version + arch + auth requirement).
- **MISTAKES:** running the first searchsploit hit blindly; ignoring auth prerequisites.
- **RABBIT HOLE:** CVEs that need conditions you can't meet; "PoC" repos that are fake/malware.

## [METHOD-8] STAGE 8 — INITIAL ACCESS → `[FOOTHOLD-CHECKLIST]`
- **OBJECTIVE:** first code execution / shell.
- **ASK:** cheapest path? (creds+service login > upload shell > injection > public exploit).
- **EVIDENCE:** screenshot the moment of access; save the exploit/command used.

## [METHOD-9] STAGE 9 — SHELL STABILIZATION → `[SHELL-QUICK]`
- **OBJECTIVE:** a stable, interactive shell you won't lose.
- **FIRST (Linux):** `python3 -c 'import pty;pty.spawn("/bin/bash")'` → `Ctrl-Z` → `stty raw -echo; fg` → `export TERM=xterm`.
- **Windows:** get to a better shell early (evil-winrm / RunasCs / a proper reverse shell); consider a Meterpreter here if this is your one MSF box.
- **MISTAKE:** doing complex work in a dumb `nc` shell and losing it.

## [METHOD-10] STAGE 10 — LOCAL ENUMERATION → Vol 4 `[LINUX-PRIVESC]` / `[WINDOWS-PRIVESC]`
- **OBJECTIVE:** everything the current user can see: who am I, privileges, other users, software, creds, network (pivot leads).
- **FIRST:** `id`/`whoami /all`, `sudo -l`/`whoami /priv`, then linpeas/winpeas *plus* manual checks.
- **OUTPUT:** privesc vectors, creds, other subnets/hosts (pivot), domain membership.

## [METHOD-11] STAGE 11 — PRIVILEGE ESCALATION → Vol 4
- **OBJECTIVE:** root / SYSTEM (or the next required privilege).
- **ASK:** quick wins first (sudo, SUID/GTFOBins, SeImpersonate, service perms) before kernel exploits.
- **EVIDENCE:** proof screenshot (`proof.txt` + `id`/`whoami` + `ip`).

## [METHOD-12] STAGE 12 — CREDENTIAL HARVESTING (post-root) → `[CREDENTIALS-QUICK]`
- **OBJECTIVE:** loot for lateral movement / other boxes.
- **FIRST (Linux):** `/etc/shadow`, SSH keys, history, `/var/www` configs, DB creds, `.env`.
- **Windows:** `secretsdump`/SAM+SYSTEM, LSASS, DPAPI, `cmdkey /list`, saved creds, `runas` targets, PowerShell history.
- **NEXT:** these creds → lateral movement / AD.

## [METHOD-13] STAGE 13 — LATERAL MOVEMENT → `[AD-LATERAL]`
- **OBJECTIVE:** use creds/hashes to reach another host.
- **FIRST:** `nxc smb <subnet> -u u -p p` to find where creds work; then evil-winrm / wmiexec / psexec / RDP / SSH.
- **RABBIT HOLE:** trying to privesc locally when the real path is "these creds admin *another* box."

## [METHOD-14] STAGE 14 — PIVOTING → Volume 5 `[PIVOT-*]`
- **OBJECTIVE:** route your tools into a network only the compromised host can reach.
- **FIRST:** Ligolo-ng (cleanest) or Chisel SOCKS + proxychains.
- **OUTPUT:** new subnet enumerated from your box via the pivot.

## [METHOD-15] STAGE 15 — AD ENUMERATION → `[AD-ENUM]`, `[AD-BLOODHOUND]`
- **OBJECTIVE:** map users, groups, computers, ACLs, delegations, kerberoastable/AS-REP targets.
- **FIRST:** with any domain cred → BloodHound collection (`bloodhound-python`/`nxc --bloodhound`), `nxc ldap`, `GetUserSPNs`, `GetNPUsers`.
- **NEXT:** shortest path to Domain Admin / target.

## [METHOD-16] STAGE 16 — AD ATTACK PATHS → `[AD-ATTACK-PATH]`
- Kerberoast → crack → reuse; AS-REP roast; ACL abuse (GenericAll/WriteDACL…); DCSync; delegation abuse. Follow BloodHound's path.

## [METHOD-17] STAGE 17 — OBJECTIVE / PROOF
- **OBJECTIVE:** grab `local.txt`/`proof.txt`; on AD, own the DC (DCSync/`secretsdump`, `administrator` hash, read proof on DC + member + workstation).
- **EVIDENCE:** per-machine proof screenshots. Log which credential/technique got you there.

## [METHOD-18] STAGE 18 — DOCUMENTATION → `[REPORTING]`
- Continuously: command + output + screenshot + which step it was. Never leave it all to the end.

---

# PART 4 — [PENTESTER-THOUGHT-PROCESS] DECISION TEMPLATES

**Template shape:** `FOUND → THINK (the questions) → NEXT (ordered actions)`.

### `[THINK-SMB]` FOUND: TCP 445/139 SMB
THINK: What can I get anonymously? Can I list shares? Enumerate users (RID cycling)? Do I already have creds — do they work here? Is this box domain-joined (→ AD)? Any readable/writable share with configs/backups? Can these creds/hashes work on *other* hosts (lateral)?
NEXT: 1) `nxc smb $IP -u '' -p ''` + `--shares` 2) `enum4linux-ng -A $IP` 3) `smbclient -N -L //$IP/` then read every readable share 4) if creds: `nxc smb $IP -u u -p p --shares --users --rid-brute` and spray on other hosts.

### `[THINK-WEB]` FOUND: HTTP(S)
THINK: What stack/CMS/version (→ known exploit)? Any login/upload/admin? Params to inject? Hidden dirs/vhosts? Creds or keys in source/JS/comments? Does a version match a public RCE?
NEXT: 1) `whatweb`+source+`/robots.txt` 2) dir+vhost brute 3) identify vuln class (SQLi/LFI/upload/SSTI/cmdinj) 4) searchsploit the CMS/version.

### `[THINK-CREDS]` FOUND: a credential
THINK: Where does this work? Same user elsewhere? Is it a password pattern (spray variants)? Local or domain? Does it unlock a second cred (DB→config→SSH)?
NEXT: 1) spray across SMB/WinRM/SSH/RDP/MSSQL/web/LDAP on this and other hosts 2) if domain → BloodHound as this user 3) log it in journal.

### `[THINK-LINSHELL]` FOUND: low-priv Linux shell → `[LINUX-PRIVESC-QUICK]`
THINK: `sudo -l` freebies? SUID/GTFOBins? cron/writable scripts? caps? creds in configs/history/DB? kernel old? am I in a container (escape)? other subnets (pivot)?
NEXT: 1) stabilize TTY 2) `id;sudo -l;find / -perm -4000 2>/dev/null` 3) linpeas 4) exploit quick win 5) loot creds.

### `[THINK-WINSHELL]` FOUND: low-priv Windows shell → `[WINDOWS-PRIVESC-QUICK]`
THINK: `whoami /priv` — SeImpersonate/SeAssignPrimaryToken (→ Potato)? service/registry/unquoted-path perms? AlwaysInstallElevated? saved creds/`cmdkey`? PowerShell history? domain-joined (→ AD)?
NEXT: 1) `whoami /all` 2) winpeas 3) if SeImpersonate → PrintSpoofer/GodPotato 4) check service perms/unquoted paths 5) loot creds → lateral.

### `[THINK-DOMAINUSER]` FOUND: valid domain user → `[AD-ATTACK-PATH]`
THINK: Kerberoastable SPNs? AS-REP roastable users? What does BloodHound say this user can reach/abuse? Password reuse to other hosts? Any ACL edges (GenericAll/WriteDACL)? Readable shares (GPP/scripts/creds)?
NEXT: 1) BloodHound collect 2) `GetUserSPNs`+`GetNPUsers` 3) `nxc smb <hosts> -u u -p p` spray 4) follow shortest BloodHound path.

### `[THINK-SPN]` FOUND: a Kerberoastable SPN → `[AD-KERBEROAST]`
THINK: Can I request the TGS (need any domain cred)? Is the account service/admin (high value)? Will the hash crack (weak password)?
NEXT: 1) `GetUserSPNs -request` 2) `hashcat -m 13100` with rockyou+rules 3) reuse cracked pw everywhere 4) check that account's privileges/BloodHound.

### `[THINK-HASH]` FOUND: an NTLM/other hash → `[HASH-IDENTIFICATION]`
THINK: What type (NTLM/NetNTLMv2/Kerberos/…)? Crackable or pass-the-hash directly? Which user/host?
NEXT: 1) identify type 2) if NTLM → try PtH (`nxc smb -H`) before cracking 3) else crack with right hashcat mode 4) reuse.

---

# PART 26 — [TIME-MANAGEMENT]

## [QUICK] Exam clock plan (23h45m)
- **Hour 0–0.5:** kick off nmap on *all* targets in parallel; read briefs; set up folders.
- **Hour 0.5–8:** **AD set first, freshest brain.** Get the AD chain moving. If AD stalls hard at ~3–4h with zero progress, pivot to a standalone and return.
- **Hour 8–16:** standalone machines. Rotate on the 30-min rule.
- **Hour 16–20:** finish/clean up, re-attempt stuck boxes with fresh eyes, chase remaining 10-pointers.
- **Hour 20–23:** **stop hacking; verify you have all proofs + screenshots.** Re-take any missing proof screenshot NOW.
- **+ next 24h:** write report.
- **Sleep:** most people should sleep ~4–6h somewhere (e.g., hour 10–15) — grinding tired loses more points than it gains.

## [WHEN-TO-MOVE-ON] The rules
- **15-min rule:** 15 min on one vector with no new info → re-read your scan/tool output, you missed something.
- **30-min rule:** 30 min, no new hypothesis → switch target/surface. Write down exactly where you stopped so return is instant.
- **Move on when:** you're retrying variants, editing an exploit you don't understand, or brute-forcing on a hunch.
- **Return when:** you've made progress elsewhere (new creds/fresh eyes), or you've exhausted other targets.
- **Revert a box** if a service is crashed or acting inconsistent (possibly your failed exploit or a stale state).

## [FATIGUE]
Eat, hydrate, 20-min walk every ~4h. Tunnel vision is a fatigue symptom. A break is faster than a rabbit hole.

---

# PART 27 — [REPORTING]

### [OFFICIAL OFFSEC] What's required
- A professional report (OffSec provides a template; you may use your own) uploaded within **24h** of the hacking window ending.
- **Per compromised host:** the vulnerability, step-by-step reproduction (commands + screenshots), the proof: **screenshot showing `local.txt`/`proof.txt` contents + `whoami`/`id` + `ip a`/`ipconfig` together**, and the flag string typed into the control panel.
- Enough detail that **someone else could reproduce** every step. Missing repro steps or missing proof screenshots lose the points for that host.

### [COMMUNITY] How to not lose points to reporting
- **Screenshot as you go, named clearly:** `webserver_10.1.1.5_local.txt.png`, `webserver_root_proof.png`. Don't rely on scrollback.
- Keep a **command log** per host (copy every command+key output into `notes.md` live). Reconstructing from memory after 24h fails.
- Take the **proof screenshot the instant** you land the flag — services get reverted, shells die.
- Include the exact **exploit code/commands you used** (if you modified a public exploit, include the diff).
- **Don't** include the KB/theory — the report is *what you did on these hosts*, reproducibly.
- Structure: Exec summary → methodology → per-host (enum → vuln → exploit → post-exploit/privesc → proof) → appendix (any extra).

> 📄 **Use the fillable `REPORT-TEMPLATE.md`** (same folder) — copy its per-host block for every machine, fill it in *as you go*, export to PDF.

### [REPORTING-SUBMISSION]  concrete submission specs (verify on the current guide)
```
Format   : a single PDF, placed INSIDE a .7z archive (no password)
Filename : OSCP-OS-XXXXX-Exam-Report.7z   (XXXXX = your OS-ID)
Upload   : https://upload.offsec.com   within 24h of the hacking window ending
Verify   : check the MD5 hash matches after upload (compute md5sum locally, compare)
Template : use OffSec's official OSCP+ .docx report template (export to PDF)
Content  : if you modified a public exploit, include your changes + why
```

### [REPORTING-CHECKLIST]
```
[ ] Every scored host has: repro steps, command evidence, proof screenshot (flag+id/whoami+ip)
[ ] Proof screenshot is from an INTERACTIVE shell (not a blind one-liner)
[ ] Flag strings entered in control panel AND shown in report
[ ] Screenshots legible, un-cropped, show the whole terminal + target IP visible
[ ] AD: show the full chain (each host owned) + how creds flowed
[ ] Methodology explained (the "why"), not just pasted commands
[ ] Single PDF → inside a no-password .7z, named OSCP-OS-XXXXX-Exam-Report.7z
[ ] Uploaded to upload.offsec.com before the 24h deadline; MD5 verified
```

---

# PART 31 — [MINIMUM-VIABLE-PREP]  (max machine time, min passive study)

### STUDY DEEPLY (this is where points are)
- **Active Directory** end-to-end: enum → Kerberoast/AS-REP → ACL abuse → lateral → DCSync. **Highest ROI. Do this most.**
- **Enumeration discipline** across all common services (Vol 1) until it's reflex.
- **Linux + Windows privesc** common vectors (Vol 4) — the top ~15 each cover most boxes.
- **Web:** SQLi, LFI/RFI, file upload, command injection, SSTI, auth bypass (Vol 2).
- **Pivoting** with Ligolo-ng or Chisel (Vol 5) — practise until it's boring.
- **Shell + file transfer + TTY** until automatic.

### STUDY LIGHTLY / RECOGNIZE ONLY
- Buffer overflow (basic concept only — not an exam focus now).
- Exotic web vulns (XXE, deserialization) — recognize + basic exploit, don't obsess.
- Obscure services — know how to enumerate anything unknown generically.

### MEMORIZE (muscle memory)
nmap two-step, TTY upgrade, reverse shell + listener, `python3 -m http.server`, `sudo -l`/`whoami /priv`, SUID find, SMB triage, Kerberoast/AS-REP one-liners, `secretsdump`, `evil-winrm`, `nxc` spray.

### PRACTICE (the actual plan)
- **Do machines, not videos.** Target: **~40–60+ practice boxes** before exam, heavily weighted to AD.
- **Best sources [COMMUNITY]:** OffSec's own **Challenge Labs / PEN-200 labs** (closest to exam), **Proving Grounds Practice** (OffSec-style, "OSCP-like" lists), **HTB** (use TJ Null's OSCP-like list + HTB Pro Labs for AD), **TryHackMe** for fundamentals/AD basics.
- For **every** box: enumerate fully, write notes as if reporting, then read a writeup **only after** to see what you missed. The gap between your notes and the writeup is your study list.
- Do **AD chains** (multi-host) specifically — single boxes don't train the 40-point set.

### SKIM / IGNORE FOR NOW
- Long theory courses, cert-guide reading marathons, memorizing CVE lists, advanced exploit dev, AV evasion (not needed for OSCP+), OSEP-level tradecraft.

---

# PART 32 — [7-DAY-PLAN]  (final week; assumes you've practised for weeks already)

> Goal: sharpen reflexes + AD, not learn new theory. ~1 focused box/AD-chain per day + drills. Don't cram.

**Day 1 — Enumeration reflexes.** Drill: nmap two-step, per-service enum on 2 standalone boxes start-to-foothold. Rebuild `[NMAP-QUICK]`/`[SMB-QUICK]` from memory. *Ignore:* privesc depth today. **Goal:** foothold in <45 min on a medium box.

**Day 2 — Linux privesc.** Do 2 Linux boxes focusing on privesc; drill `sudo -l`, SUID/GTFOBins, cron, caps, creds. Redo any `[LINUX-PRIVESC]` vector you fumble. **Goal:** root both, notes report-ready.

**Day 3 — Windows privesc.** 2 Windows boxes; drill SeImpersonate→Potato, service/unquoted-path, cred harvest. **Goal:** SYSTEM both.

**Day 4 — AD chain #1.** Full assumed-breach chain: enum→BloodHound→Kerberoast/AS-REP→lateral→DC. Time it. **Goal:** DC compromise + clean notes of cred flow.

**Day 5 — AD chain #2 + pivoting.** Another chain *through a pivot* (Ligolo/Chisel + proxychains). **Goal:** own an internal host only reachable via pivot.

**Day 6 — Full mock exam (mini).** AD set + 1–2 standalones under time pressure, screenshots + notes as if graded. Practice the proof-screenshot habit. **Goal:** find your weak stage.

**Day 7 — Light.** Review Day-6 weak spots, re-read your `[STUCK-PROTOCOL]` and Golden Rules, prep environment (VPN, tools, note template, screenshot tool, folder skeleton). **Sleep early.** *Ignore:* new topics. **Goal:** rested + tools ready.

---

# PART 33 — [READINESS-TEST]  (score yourself on *methodology*, not trivia)

Answer out loud, then check against the KB. Score 0–2 each (0 blank, 1 partial, 2 solid). **≥ 45/60 = ready.**

**Enumeration**
1. Ports 22, 80, 445 open. First 5 concrete actions, in order? *(nmap -sCV those ports; web map + dir/vhost brute; SMB anon `nxc`/`enum4linux-ng`/`smbclient -N -L`; try creds cross-service; searchsploit versions.)*
2. nmap shows `Apache 2.4.49`. What now? *(That version → CVE-2021-41773 path traversal/RCE — verify version exactly, test traversal, confirm before exploit.)*
3. UDP 161 open. Next command + why? *(`snmpwalk -v2c -c public $IP` → users, processes, creds, routes.)*

**Web**
4. You found a login + a version'd CMS. Order of attack? *(default/weak creds → searchsploit CMS version → SQLi on login → dir brute for admin/upload.)*
5. `?page=about` — hypothesis + test? *(LFI/RFI → `?page=../../../../etc/passwd` and php filter wrapper; if include → RCE via log/wrapper.)*

**Initial access**
6. searchsploit gives 3 hits for the version. How do you pick/verify before running? *(match exact version+arch+auth; read the code; check what it does; test non-destructively.)*

**Linux privesc**
7. Low-priv shell. First 4 commands? *(`id; sudo -l; find / -perm -4000 2>/dev/null; ` then linpeas.)*
8. `sudo -l` shows `(ALL) NOPASSWD: /usr/bin/find`. Exploit? *(GTFOBins: `sudo find . -exec /bin/sh \; -quit`.)*

**Windows privesc**
9. `whoami /priv` shows `SeImpersonatePrivilege Enabled`. Path? *(PrintSpoofer / GodPotato → SYSTEM.)*
10. You find a service with a writable binary path / unquoted path with a writable dir. Steps? *(place payload, restart service or wait, get SYSTEM shell.)*

**AD**
11. You have one domain user's password. First 4 actions? *(BloodHound collect; Kerberoast `GetUserSPNs -request`; AS-REP `GetNPUsers`; spray creds on hosts with `nxc`.)*
12. BloodHound shows your user has `GenericAll` on another user. What do you do? *(force-change their password or targeted Kerberoast/shadow-creds; then use them.)*
13. You cracked a service account with an SPN. Next? *(reuse pw everywhere; check its group memberships/BloodHound; look for path to DA / DCSync.)*

**Pivoting**
14. You root a dual-homed host seeing `172.16.5.0/24`. How do you scan it from your box? *(Ligolo tunnel or Chisel SOCKS + proxychains; then `nxc`/nmap through proxy.)*

**Credentials / hashes**
15. You dumped an NTLM hash. Two things to try, in order? *(pass-the-hash with `nxc -H`/evil-winrm `-H` first; crack with hashcat `-m 1000` if PtH blocked.)*

**Troubleshooting**
16. Reverse shell won't connect. Diagnostic order? *(listener up? right LHOST/LPORT? egress port allowed? payload encoding/quoting? firewall? try 80/443; test with a simpler payload.)*

**Decision / stuck**
17. Stuck 30 min on standalone #2. What exactly do you do? *(invoke `[STUCK-PROTOCOL]`: re-enum all ports/web, list untried surfaces, switch to another target, return fresh.)*

---

# PART 35 — [NAVIGATION-SIM] Using this KB with Ctrl+F

Each: **FINDING → search tag → technique → command → interpret → next.**

1. **Unknown web server:** `Ctrl+F [WEB-QUICK]` → fingerprint+content map → `whatweb`/feroxbuster → note CMS/version/params → `[SQLI]`/`[WEB-LFI]`/searchsploit.
2. **Low-priv Linux shell:** `[LINUX-PRIVESC-QUICK]` → `sudo -l`/SUID/linpeas → interpret hits vs false positives → `[GTFOBINS-WORKFLOW]`.
3. **Low-priv Windows shell:** `[WINDOWS-PRIVESC-QUICK]` → `whoami /priv`+winpeas → SeImpersonate? service? → `[WINDOWS-TOKENS]`/`[WINDOWS-SERVICES]`.
4. **SMB server:** `[SMB-QUICK]` → anon/shares/users → `nxc`/`smbclient`/`enum4linux-ng` → creds/files → `[FOUND-SMB]`.
5. **Domain user:** `[AD-QUICK]` → BloodHound+roast+spray → `[AD-KERBEROAST]`/`[AD-ASREP]`/`[AD-ACL]` → `[AD-ATTACK-PATH]`.
6. **SQL injection:** `[SQLI-DECISION-TREE]` → identify DB → union/blind → `[SQLI-MYSQL]` etc → creds/file/RCE.
7. **LFI:** `[WEB-LFI]` → confirm `/etc/passwd` → wrappers/log-poison → RCE → `[SHELL-QUICK]`.
8. **Credentials:** `[FOUND-CREDS]` → spray everywhere → `[CREDENTIALS-QUICK]`.
9. **BloodHound edge:** `[AD-BLOODHOUND]` → identify edge type → `[AD-ACL]` abuse recipe.
10. **Pivot host:** `[PIVOT-QUICK]` → Ligolo/Chisel → proxychains scan → enumerate new subnet.

---

# [CURRENT-OFFSEC-RULES-SUMMARY]  (verify on the live exam guide before your exam)
- 23h45m hands-on + 24h reporting. 100 pts, **70 to pass**. No bonus points.
- 40-pt AD set (3 chained hosts, effectively all-or-nothing) + 3×20-pt standalones (10 local + 10 proof).
- **Metasploit/Meterpreter: one target only; not for pivoting.** Manual everything else.
- Restricted/forbidden: automated exploitation frameworks, one-click AD auto-pwn tools, automated vuln scanners as primary exploitation, AI that solves the box, spoofing/DoS. **Check the current guide — rules change.**
- Proof = flag contents + `whoami`/`id` + `ip a`/`ipconfig` in one screenshot, plus flag entered in the panel. Report required, reproducible, on time.
- OSCP+ expires in 3 years (renewable); underlying OSCP is lifetime.

---
*End Volume 0. Continue: Volume 1 (Enumeration & Nmap).*
