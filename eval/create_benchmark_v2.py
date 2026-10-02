"""Script to generate eval/test_questions_v2.md and eval/answer_key_v2.md."""

import glob
import re
from pathlib import Path

def find_machs(pat: str) -> list[str]:
    found = []
    for f in sorted(glob.glob("raw/htb-*.md")):
        t = open(f, encoding="utf-8", errors="ignore").read()
        if re.search(pat, t, re.IGNORECASE):
            stem = f.replace("\\", "/").split("/")[-1].replace(".md", "")
            found.append(stem)
    return found

questions = [
    # Q1
    (1, "broad", "Web application injection vulnerabilities cheatsheet",
     "What are the common Web Application injection vulnerabilities (SQLi, SSTI, Command Injection, LFI) across HTB machines? Provide a cheatsheet.",
     find_machs(r"sqli|sql injection|ssti|template injection|command injection|local file inclusion|\blfi\b"),
     "Web injection techniques include SQL Injection (union-based, blind, stacked queries via sqlmap), Server-Side Template Injection (Jinja2/Twig SSTI to achieve RCE), OS Command Injection via unvalidated inputs, and Local File Inclusion (LFI) to read /etc/passwd or achieve RCE via log poisoning or php wrappers."),
    # Q2
    (2, "broad", "Active Directory lateral movement cheatsheet",
     "What Active Directory lateral movement techniques (Pass-the-Hash, PsExec, WMIExec, SMBExec) are demonstrated across HTB machines? Provide a cheatsheet.",
     find_machs(r"psexec\.py|wmiexec\.py|smbexec\.py|pass-the-hash|\bpth\b|evil-winrm"),
     "AD lateral movement techniques include Pass-the-Hash (PtH) using NTLM hashes via impacket psexec.py, wmiexec.py, smbexec.py, WinRM access via evil-winrm with plaintext credentials or hashes, Overpass-the-Hash / Pass-the-Key using mimikatz or Rubeus, and SMB relay attacks."),
    # Q3
    (3, "broad", "Linux credential harvesting cheatsheet",
     "What Linux credential harvesting and sensitive file discovery techniques are used across HTB machines? Provide a cheatsheet.",
     find_machs(r"/etc/shadow|\.bash_history|id_rsa|keepass|\.kdbx|wp-config\.php"),
     "Linux credential harvesting techniques include inspecting bash history (.bash_history), searching for unencrypted SSH private keys (id_rsa), extracting password hashes from /etc/shadow or KeePass databases (.kdbx) using keepass2john, checking web application configuration files (wp-config.php, .env, config.php), and inspecting memory or process credentials."),
    # Q4
    (4, "broad", "Network service enumeration and reconnaissance cheatsheet",
     "What network service reconnaissance techniques (anonymous FTP, SNMP, RPCClient, NFS exports) are demonstrated across HTB machines? Provide a cheatsheet.",
     find_machs(r"anonymous ftp|snmpwalk|rpcclient|showmount -e|enum4linux"),
     "Reconnaissance techniques include checking anonymous FTP access for sensitive files or uploads, SNMP community string enumeration using snmpwalk or onesixtyone to reveal processes and network interfaces, RPCClient null session enumeration for users and groups, and NFS export discovery using showmount -e for no_root_squash misconfigurations."),
    # Q5
    (5, "broad", "Docker and container escape cheatsheet",
     "What Docker and container breakout techniques are seen across HTB machines? Provide a cheatsheet.",
     find_machs(r"docker\.sock|cgroup|lxd init|lxc image|--privileged|container breakout"),
     "Container breakout techniques include mounting host filesystems via the Docker socket (/var/run/docker.sock), abusing --privileged containers via cgroups release_agent or raw disk mounts, abusing local docker or lxd group membership, and container runtime vulnerabilities such as runc (CVE-2024-21626 / CVE-2019-5736)."),
    # Q6
    (6, "specific", "AS-REP Roasting in Active Directory",
     "How does AS-REP Roasting work in Active Directory and which HTB machines demonstrate it with GetNPUsers.py?",
     find_machs(r"getnpusers|as-?rep roast|dont_req_preauth"),
     "AS-REP Roasting targets Active Directory user accounts that have the DONT_REQ_PREAUTH flag set (Kerberos pre-authentication disabled). An attacker can request an AS-REP message containing an encrypted ticket without credentials, extract the encrypted ticket offline, and crack the password hash using hashcat (mode 18200) or john. Executed using Impacket GetNPUsers.py."),
    # Q7
    (7, "specific", "Server-Side Template Injection (SSTI) in Jinja2",
     "Which HTB machines demonstrate Server-Side Template Injection (SSTI) in Jinja2 / Python web applications and how is it exploited?",
     find_machs(r"jinja2|\{\{.*config.*\}\}|ssti.*jinja|render_template_string"),
     "SSTI in Jinja2 occurs when user input is concatenated directly into a template string rather than passed as a context variable. Attackers inject Jinja expressions like {{ config.items() }} or access Python class hierarchies to locate subprocess.Popen and execute arbitrary OS commands."),
    # Q8
    (8, "specific", "MSSQL xp_cmdshell command execution",
     "How is MSSQL exploited for remote command execution using xp_cmdshell across HTB machines?",
     find_machs(r"xp_cmdshell|mssqlclient\.py"),
     "When an attacker acquires credentials to a Microsoft SQL Server with sysadmin privileges or impersonate permissions, they can reconfigure sp_configure to enable xp_cmdshell (sp_configure 'show advanced options', 1; RECONFIGURE; sp_configure 'xp_cmdshell', 1; RECONFIGURE;) and execute operating system shell commands as the SQL service account."),
    # Q9
    (9, "specific", "Redis remote code execution",
     "How is an unauthenticated or misconfigured Redis server exploited for remote code execution across HTB machines?",
     find_machs(r"redis-cli|rogue-server|dump\.rdb|6379/tcp open.*redis"),
     "Unauthenticated Redis servers exposed on port 6379 allow attackers to configure the database working directory (CONFIG SET dir) and database filename (CONFIG SET dbfilename). Attackers exploit this to write an SSH authorized_keys file into /root/.ssh/, write a webshell into a web directory, or write a malicious crontab file into /var/spool/cron/crontabs/ for immediate reverse shell execution."),
    # Q10
    (10, "specific", "Sudo LD_PRELOAD privilege escalation",
     "How is Sudo privilege escalation achieved using sudo misconfigurations or LD_PRELOAD across HTB machines?",
     find_machs(r"ld_preload|env_keep.*ld_preload"),
     "When sudo -l reveals that env_keep += LD_PRELOAD is configured, any user permitted to run a command via sudo can load an arbitrary shared library. The attacker compiles a malicious C shared library with an _init() constructor that calls setuid(0) and /bin/bash, then executes sudo LD_PRELOAD=/tmp/priv.so <allowed_binary> to spawn an immediate root shell."),
    # Q11
    (11, "specific", "BloodHound Active Directory attack path analysis",
     "How is BloodHound or SharpHound used for Active Directory attack path analysis across HTB machines?",
     find_machs(r"bloodhound|sharphound"),
     "BloodHound and its ingestors (SharpHound.exe, bloodhound-python) enumerate Active Directory domain objects, group memberships, trust relationships, sessions, and Access Control Lists (ACLs). Attackers visualize graph paths to identify privilege escalation routes (e.g. GenericAll, WriteDacl, ForceChangePassword, or Shortest Paths to Domain Admins)."),
    # Q12
    (12, "specific", "Linux kernel privilege escalation (Dirty Cow / PwnKit)",
     "How are Linux kernel vulnerabilities like Dirty Cow (CVE-2016-5195) or PwnKit (CVE-2021-4034) exploited across HTB machines?",
     find_machs(r"pwnkit|cve-2021-4034|dirtycow|cve-2016-5195"),
     "Dirty Cow (CVE-2016-5195) exploits a race condition in the Linux kernel copy-on-write (COW) memory mapping to write to read-only files like /etc/passwd. PwnKit (CVE-2021-4034) exploits an out-of-bounds read/write in Polkit pkexec to inject environment variables and execute arbitrary code as root without requiring credentials."),
    # Q13
    (13, "specific", "Server-Side Request Forgery (SSRF) exploitation",
     "Which HTB machines demonstrate Server-Side Request Forgery (SSRF) and how is it exploited to access internal services?",
     find_machs(r"\bssrf\b|server-?side request forgery"),
     "SSRF allows an attacker to induce the server-side application to make HTTP requests to an arbitrary domain or internal resource. On HTB, it is leveraged to access localhost-only administrative portals (e.g. 127.0.0.1:8080), cloud metadata endpoints (169.254.169.254), or interact with internal microservices and databases (e.g. via gopher:// or dict://)."),
    # Q14
    (14, "specific", "Pass-the-Hash with Impacket psexec / wmiexec",
     "How is Pass-the-Hash (PTH) executed using Impacket tools like psexec.py or wmiexec.py across HTB machines?",
     find_machs(r"psexec\.py|wmiexec\.py|smbexec\.py"),
     "Pass-the-Hash allows an attacker to authenticate to remote Windows hosts over SMB/RPC using an NTLM password hash without needing the plaintext password. Impacket tools like psexec.py, wmiexec.py, and smbexec.py accept the hash format -hashes LM:NT or :NT to spawn remote command prompts or semi-interactive shells."),
    # Q15
    (15, "specific", "Anonymous FTP access and exploitation",
     "How is anonymous FTP access or vsftpd exploited across HTB machines?",
     find_machs(r"anonymous ftp|ftp.*anonymous allowed"),
     "Anonymous FTP allows unauthenticated users to log in with username anonymous and an arbitrary password. Attackers enumerate exposed directories to retrieve backup archives, configuration files, SSH keys, or passwords. In configurations with write permissions, attackers upload webshells or reverse shell scripts into web server document roots.")
]

test_q_lines = [
    "# HTB RAG – Test Questions (Benchmark V2)\n",
    "15 independent evaluation questions (5 broad, 10 specific) for measuring retrieval quality and answer accuracy on unseen techniques.\n",
    "---\n"
]
ans_k_lines = [
    "# HTB RAG – Answer Key (Benchmark V2)\n",
    "> Built independently by grepping raw/*.md — NOT from the RAG system.\n",
    "---\n"
]

ans_k_lines.append("## Broad Questions\n")
test_q_lines.append("## Broad Questions\n")

for qnum, qtype, title, question, machs, answer in questions:
    if qnum == 6:
        ans_k_lines.append("\n## Specific Questions\n")
        test_q_lines.append("\n## Specific Questions\n")
    
    test_q_lines.append(f"---\n**Q{qnum}** | Type: {qtype}\nQuestion: {question}\n---\n")
    mach_str = ", ".join(machs)
    ans_k_lines.append(f"---\n**Q{qnum}** | {title}\nMachines: {mach_str}\nAnswer: {answer}\n\n---\n")

Path("eval/test_questions_v2.md").write_text("\n".join(test_q_lines), encoding="utf-8")
Path("eval/answer_key_v2.md").write_text("\n".join(ans_k_lines), encoding="utf-8")
print("Generated eval/test_questions_v2.md and eval/answer_key_v2.md")
