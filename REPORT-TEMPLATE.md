# OSCP Exam Report — <YOUR NAME>

> **How to use:** fill this in AS YOU GO (not after). Copy the "PER-HOST" block for every machine.
> Export to PDF, put the PDF inside a **no-password `.7z`** named `OSCP-OS-XXXXX-Exam-Report.7z`,
> upload to https://upload.offsec.com within 24h, verify the MD5. Reference: `[REPORTING]` / `[REPORTING-SUBMISSION]`.
> ⚠️ **A report is required to pass even if you have 70 pts of flags.** Every scored host needs reproducible steps + a proof screenshot.

- **OSID:** OS-XXXXX
- **Exam date:** ____
- **Email:** ____

---

## 1. High-Level Summary
I was tasked with the OSCP exam: 3 standalone hosts (20 pts each) + 1 Active Directory set (40 pts). Below are the hosts compromised, the vulnerabilities used, and step-by-step reproduction.

**Results overview:**

| Host | IP | Type | local.txt | proof.txt | Points |
|---|---|---|---|---|---|
| ST-A | | standalone | ✅/❌ | ✅/❌ | /20 |
| ST-B | | standalone | ✅/❌ | ✅/❌ | /20 |
| ST-C | | standalone | ✅/❌ | ✅/❌ | /20 |
| AD - Workstation | | AD set | — | ✅/❌ | (part of 40) |
| AD - Member/Server | | AD set | — | ✅/❌ | (part of 40) |
| AD - Domain Controller | | AD set | — | ✅/❌ | (part of 40) |

**Total: ___ / 100  (pass = 70)**

---

## 2. Methodology (brief)
For each target: full TCP port scan → service enumeration → identify a vulnerability → gain initial access → stabilize a shell → capture `local.txt` → local enumeration → privilege escalation → capture `proof.txt`. For the AD set: foothold → collect BloodHound → Kerberoast/AS-REP + credential spray → lateral movement → compromise the Domain Controller.

---

# ==================== PER-HOST BLOCK (copy per machine) ====================

## Host: <NAME>  —  <IP>
- **Hostname:** ____   **OS:** ____   (AD set? which role: ____)

### 2.x Service Enumeration
```
# nmap output (paste the -sCV result)
```
Notable: <open ports / versions / findings that mattered>.

### 2.x Initial Access (Vulnerability + Exploitation)
**Vulnerability:** <what it was — e.g. Tiny File Manager default creds → PHP upload>.
**Steps to reproduce:**
```
# every command you ran, in order
```
> 📸 **Screenshot:** exploit working / shell obtained.

### 2.x Proof of Low-Priv Access (local.txt)
```
cat local.txt ; id ; ip a        # Linux
type local.txt & whoami & ipconfig   # Windows
```
> 📸 **Screenshot:** `local.txt` contents + `whoami`/`id` + `ip` in ONE frame.
**local.txt value:** `________________________`

### 2.x Privilege Escalation
**Vector:** <sudo / SUID / SeImpersonate / service / kernel / ACL / etc.>.
**Steps to reproduce:**
```
# commands
```
> 📸 **Screenshot:** privesc working.

### 2.x Proof of Root/SYSTEM (proof.txt)
```
cat /root/proof.txt ; id ; ip a
type C:\Users\Administrator\Desktop\proof.txt & whoami & ipconfig
```
> 📸 **Screenshot:** `proof.txt` + `whoami`/`id` + `ip` in ONE frame.
**proof.txt value:** `________________________`

### 2.x Post-Exploitation / Looted Credentials (for AD lateral movement)
<hashes/passwords/keys found here, and which host they unlocked next>.

# ==================== END PER-HOST BLOCK ====================

---

## 3. Active Directory — Attack Chain
Show how you moved through the domain (this is what earns the 40 pts):
1. **Foothold:** <how you got onto the first AD host>.
2. **First domain credential:** <how obtained — roast/spray/loot>.
3. **Lateral movement:** <cred/hash → which host → what you found>.
4. **Privilege escalation to Domain Admin:** <ACL edge / DCSync / etc.>.
5. **DC compromise:** `secretsdump` / PtH Administrator → read proof on DC + member + workstation.
> 📸 Screenshots at each hop showing the credential flow.

---

## Appendix A — Modified Exploits
If you edited any public exploit, paste the original source + your changes + why.

## Appendix B — Submission Checklist
```
[ ] Every scored host: repro steps + command evidence + proof screenshot (flag + whoami/id + ip, one frame)
[ ] Proof screenshots from an INTERACTIVE shell; target IP visible
[ ] Flag strings entered in the control panel AND shown here
[ ] AD: full chain + credential flow documented
[ ] Methodology explained (the "why"), not just pasted commands
[ ] Exported to a single PDF
[ ] PDF placed inside a NO-PASSWORD .7z named OSCP-OS-XXXXX-Exam-Report.7z
[ ] Uploaded to upload.offsec.com before the 24h deadline; MD5 verified
```
