# HTB RAG – Answer Key (Benchmark V2)

> Calibrated canonical gold-standard benchmark representing core techniques and primary HTB machines.
> Raw uncurated grep backup is safely preserved in `eval/answer_key_v2_raw_grep.md`.

---

## Broad Questions

---
**Q1** | Web application injection vulnerabilities cheatsheet
Machines: htb-goodgames, htb-doctor, htb-sandworm, htb-chemistry, htb-oz, htb-jarvis, htb-poison, htb-shocker, htb-perspective, htb-pollution
Answer: Web injection techniques include SQL Injection (union-based, blind, stacked queries via sqlmap), Server-Side Template Injection (Jinja2/Twig SSTI to achieve RCE), OS Command Injection via unvalidated inputs, and Local File Inclusion (LFI) to read /etc/passwd or achieve RCE via log poisoning or php wrappers.

---

---
**Q2** | Active Directory lateral movement cheatsheet
Machines: htb-active, htb-sauna, htb-flight, htb-sizzle, htb-redelegate, htb-retrotwo, htb-pivotapi, htb-administrator, htb-forest, htb-jab
Answer: AD lateral movement techniques include Pass-the-Hash (PtH) using NTLM hashes via impacket psexec.py, wmiexec.py, smbexec.py, WinRM access via evil-winrm with plaintext credentials or hashes, Overpass-the-Hash / Pass-the-Key using mimikatz or Rubeus, and SMB relay attacks.

---

---
**Q3** | Linux credential harvesting cheatsheet
Machines: htb-shibboleth, htb-hawk, htb-beep, htb-caption, htb-player, htb-skyfall, htb-tentacle, htb-traverxec, htb-ellingson, htb-sorcery
Answer: Linux credential harvesting techniques include inspecting bash history (.bash_history), searching for unencrypted SSH private keys (id_rsa), extracting password hashes from /etc/shadow or KeePass databases (.kdbx) using keepass2john, checking web application configuration files (wp-config.php, .env, config.php), and inspecting memory or process credentials.

---

---
**Q4** | Network service enumeration and reconnaissance cheatsheet
Machines: htb-devarea, htb-conceal, htb-remote, htb-servmon, htb-abducted, htb-lustroustwo, htb-reel, htb-devel, htb-squashed, htb-active
Answer: Reconnaissance techniques include checking anonymous FTP access for sensitive files or uploads, SNMP community string enumeration using snmpwalk or onesixtyone to reveal processes and network interfaces, RPCClient null session enumeration for users and groups, and NFS export discovery using showmount -e for no_root_squash misconfigurations.

---

---
**Q5** | Docker and container escape cheatsheet
Machines: htb-carpediem, htb-runner, htb-extension, htb-monitors, htb-talkative, htb-cybermonday, htb-shoppy, htb-feline, htb-pikatwoo, htb-laboratory
Answer: Container breakout techniques include mounting host filesystems via the Docker socket (/var/run/docker.sock), abusing --privileged containers via cgroups release_agent or raw disk mounts, abusing local docker or lxd group membership, and container runtime vulnerabilities such as runc (CVE-2024-21626 / CVE-2019-5736).

---

## Specific Questions

---
**Q6** | AS-REP Roasting in Active Directory
Machines: htb-sauna, htb-forest, htb-blackfield, htb-rebound, htb-pivotapi, htb-active, htb-infiltrator
Answer: AS-REP Roasting targets Active Directory user accounts that have the DONT_REQ_PREAUTH flag set (Kerberos pre-authentication disabled). An attacker can request an AS-REP message containing an encrypted ticket without credentials, extract the encrypted ticket offline, and crack the password hash using hashcat (mode 18200) or john. Executed using Impacket GetNPUsers.py.

---

---
**Q7** | Server-Side Template Injection (SSTI) in Jinja2
Machines: htb-doctor, htb-oz, htb-sandworm, htb-trickster, htb-late, htb-chemistry, htb-flustered
Answer: SSTI in Jinja2 occurs when user input is concatenated directly into a template string rather than passed as a context variable. Attackers inject Jinja expressions like {{ config.items() }} or access Python class hierarchies to locate subprocess.Popen and execute arbitrary OS commands.

---

---
**Q8** | MSSQL xp_cmdshell command execution
Machines: htb-darkzero, htb-escape, htb-ghost, htb-pivotapi, htb-redelegate, htb-querier, htb-monteverde, htb-freelancer
Answer: When an attacker acquires credentials to a Microsoft SQL Server with sysadmin privileges or impersonate permissions, they can reconfigure sp_configure to enable xp_cmdshell (sp_configure 'show advanced options', 1; RECONFIGURE; sp_configure 'xp_cmdshell', 1; RECONFIGURE;) and execute operating system shell commands as the SQL service account.

---

---
**Q9** | Redis remote code execution
Machines: htb-shared, htb-catch, htb-postman, htb-reddish, htb-atom, htb-cybermonday, htb-pollution
Answer: Unauthenticated Redis servers exposed on port 6379 allow attackers to configure the database working directory (CONFIG SET dir) and database filename (CONFIG SET dbfilename). Attackers exploit this to write an SSH authorized_keys file into /root/.ssh/, write a webshell into a web directory, or write a malicious crontab file into /var/spool/cron/crontabs/ for immediate reverse shell execution.

---

---
**Q10** | Sudo LD_PRELOAD privilege escalation
Machines: htb-clicker, htb-dab, htb-surveillance, htb-expressway, htb-broker
Answer: When sudo -l reveals that env_keep += LD_PRELOAD is configured, any user permitted to run a command via sudo can load an arbitrary shared library. The attacker compiles a malicious C shared library with an _init() constructor that calls setuid(0) and /bin/bash, then executes sudo LD_PRELOAD=/tmp/priv.so <allowed_binary> to spawn an immediate root shell.

---

---
**Q11** | BloodHound Active Directory attack path analysis
Machines: htb-forest, htb-sauna, htb-blackfield, htb-administrator, htb-infiltrator, htb-eighteen, htb-multimaster, htb-pivotapi
Answer: BloodHound and its ingestors (SharpHound.exe, bloodhound-python) enumerate Active Directory domain objects, group memberships, trust relationships, sessions, and Access Control Lists (ACLs). Attackers visualize graph paths to identify privilege escalation routes (e.g. GenericAll, WriteDacl, ForceChangePassword, or Shortest Paths to Domain Admins).

---

---
**Q12** | Linux kernel privilege escalation (Dirty Cow / PwnKit)
Machines: htb-valentine, htb-routerspace, htb-paper, htb-popcorn, htb-antique, htb-pressed, htb-ouija
Answer: Dirty Cow (CVE-2016-5195) exploits a race condition in the Linux kernel copy-on-write (COW) memory mapping to write to read-only files like /etc/passwd. PwnKit (CVE-2021-4034) exploits an out-of-bounds read/write in Polkit pkexec to inject environment variables and execute arbitrary code as root without requiring credentials.

---

---
**Q13** | Server-Side Request Forgery (SSRF) exploitation
Machines: htb-forge, htb-editorial, htb-backfire, htb-love, htb-lantern, htb-sau, htb-travel, htb-bountyhunter
Answer: SSRF allows an attacker to induce the server-side application to make HTTP requests to an arbitrary domain or internal resource. On HTB, it is leveraged to access localhost-only administrative portals (e.g. 127.0.0.1:8080), cloud metadata endpoints (169.254.169.254), or interact with internal microservices and databases (e.g. via gopher:// or dict://).

---

---
**Q14** | Pass-the-Hash with Impacket psexec / wmiexec
Machines: htb-sauna, htb-forest, htb-sizzle, htb-redelegate, htb-retrotwo, htb-anubis, htb-darkzero, htb-flight
Answer: Pass-the-Hash allows an attacker to authenticate to remote Windows hosts over SMB/RPC using an NTLM password hash without needing the plaintext password. Impacket tools like psexec.py, wmiexec.py, and smbexec.py accept the hash format -hashes LM:NT or :NT to spawn remote command prompts or semi-interactive shells.

---

---
**Q15** | Anonymous FTP access and exploitation
Machines: htb-lame, htb-devel, htb-devarea, htb-crossfit, htb-netmon, htb-servmon, htb-oouch, htb-access
Answer: Anonymous FTP allows unauthenticated users to log in with username anonymous and an arbitrary password. Attackers enumerate exposed directories to retrieve backup archives, configuration files, SSH keys, or passwords. In configurations with write permissions, attackers upload webshells or reverse shell scripts into web server document roots.

---
