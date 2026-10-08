# 🗂️ OSCP Box Journal

A per-box log of every machine worked — the attack chain, exact commands, learnings, and the mistakes to not repeat. Building this is how writeups turn into *methodology* (and it's report-writing practice for exam day).

> **How to use:** after rooting a box, add an entry here. One file per box (`<BoxName>.md`), using the template at the bottom. Keep it honest — record the rabbit holes too; that's where the learning is.

## Boxes completed

| Box | Platform | OS | Key technique | Difficulty | Date |
|---|---|---|---|---|---|
| [Twiggy](Twiggy.md) | Proving Grounds | Linux | SaltStack CVE-2020-11651 (unauth RCE as root) | Easy | 2026-10-08 |

*(Also fully owned earlier, pre-journal: **Secura** — full AD domain compromise; **MedTech / WEB02** — SQLi→xp_cmdshell→PrintSpoofer→SYSTEM.)*

---

## 📝 Template for a new box (copy this into `<BoxName>.md`)

```markdown
# <BoxName>  (<Platform> · <OS> · <Difficulty>)

- **IP:** <target>   **Date:** <YYYY-MM-DD>   **Time to root:** <mins>
- **One-line:** <the core path in a sentence>

## 1. Enumeration
- Ports (nmap): <list>
- Key finding: <what stood out>

## 2. Foothold (user)
- Vector: <vuln/service>
- Steps + commands:
  ```bash
  <commands>
  ```
- local.txt: <captured>

## 3. Privilege Escalation (root/SYSTEM)
- Vector: <what>
- Steps + commands:
  ```bash
  <commands>
  ```
- proof.txt: <captured>

## 4. Learnings & tips
- <what this box taught me>

## 5. Rabbit holes / mistakes
- <what wasted time, so I don't repeat it>

## 6. KB tags used
- <[TAG], [TAG] …>
```
