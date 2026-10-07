# HTB RAG – Answer Key (Benchmark V2)

> Built independently by grepping raw/*.md — NOT from the RAG system.

---

## Broad Questions

---
**Q1** | Web application injection vulnerabilities cheatsheet
Machines: htb-abducted, htb-academy, htb-admirer, htb-admirertoo, htb-ai, htb-alert, htb-altered, htb-ambassador, htb-anubis, htb-appsanity, htb-ariekei, htb-armageddon, htb-artificial, htb-atom, htb-attended, htb-awkward, htb-backdoor, htb-backendtwo, htb-backfire, htb-bagel, htb-bank, htb-bankrobber, htb-bart, htb-bastard, htb-beep, htb-bigbang, htb-blazorized, htb-boardlight, htb-bolt, htb-book, htb-bookworm, htb-brainfuck, htb-breadcrumbs, htb-broscience, htb-bruno, htb-buff, htb-cache, htb-calamity, htb-cap, htb-caption, htb-carpediem, htb-carrier, htb-cascade, htb-cat, htb-catch, htb-cerberus, htb-cereal, htb-chainsaw, htb-charon, htb-checker, htb-chemistry, htb-clicker, htb-code, htb-codetwo, htb-codify, htb-compiled, htb-compromised, htb-control, htb-conversor, htb-corporate, htb-cozyhosting, htb-crimestoppers, htb-cronos, htb-crossfit, htb-crossfittwo, htb-ctf, htb-curling, htb-cybermonday, htb-cypher, htb-darkcorp, htb-data, htb-derailed, htb-devarea, htb-devzat, htb-doctor, htb-down, htb-drive, htb-dump, htb-dynstr, htb-dyplesher, htb-earlyaccess, htb-encoding, htb-enterprise, htb-environment, htb-epsilon, htb-era, htb-ethereal, htb-eureka, htb-europa, htb-evilcups, htb-extension, htb-faculty, htb-falafel, htb-fatty, htb-fighter, htb-fingerprint, htb-flujab, htb-flustered, htb-fluxcapacitor, htb-forgot, htb-format, htb-formulax, htb-fortune, htb-forwardslash, htb-friendzone, htb-gavel, htb-ghost, htb-giddy, htb-giveback, htb-gobox, htb-goodgames, htb-guardian, htb-hackback, htb-hacknet, htb-haircut, htb-hancliffe, htb-hawk, htb-haystack, htb-headless, htb-heal, htb-health, htb-help, htb-helpline, htb-holiday, htb-horizontall, htb-hospital, htb-iclean, htb-imagery, htb-inception, htb-infiltrator, htb-instant, htb-intense, htb-intentions, htb-interpreter, htb-intuition, htb-investigation, htb-irked, htb-jarvis, htb-jupiter, htb-kotarak, htb-kryptos, htb-lacasadepapel, htb-lantern, htb-late, htb-love, htb-luanne, htb-luke, htb-magic, htb-magicgardens, htb-mailing, htb-mailroom, htb-mango, htb-mentor, htb-meta, htb-metatwo, htb-mischief, htb-monitored, htb-monitors, htb-monitorsfour, htb-monitorsthree, htb-monitorstwo, htb-multimaster, htb-netmon, htb-networked, htb-nineveh, htb-nocturnal, htb-node, htb-nodeblog, htb-noter, htb-nunchucks, htb-onlyforyou, htb-oouch, htb-openadmin, htb-openkeys, htb-ouija, htb-outbound, htb-overflow, htb-overgraph, htb-overwatch, htb-oz, htb-pandora, htb-paper, htb-patents, htb-pc, htb-perfection, htb-perspective, htb-phoenix, htb-photobomb, htb-pikaboo, htb-pikatwoo, htb-pilgrimage, htb-planning, htb-player, htb-poison, htb-pollution, htb-popcorn, htb-precious, htb-previse, htb-proper, htb-pterodactyl, htb-querier, htb-quick, htb-rabbit, htb-race, htb-rainyday, htb-ransom, htb-redcross, htb-redpanda, htb-registry, htb-reset, htb-resource, htb-response, htb-retired, htb-routerspace, htb-safe, htb-sandworm, htb-sau, htb-scanned, htb-scavenger, htb-schooled, htb-scriptkiddie, htb-sea, htb-secnotes, htb-secret, htb-sekhmet, htb-sense, htb-seventeen, htb-shared, htb-shoppy, htb-shrek, htb-sightless, htb-snapped, htb-sneaky, htb-sniper, htb-snoopy, htb-soccer, htb-socket, htb-solarlab, htb-soulmate, htb-spider, htb-spooktrol, htb-stacked, htb-static, htb-stocker, htb-store, htb-streamio, htb-surveillance, htb-swagshop, htb-tabby, htb-talkative, htb-tartarsauce, htb-ten, htb-tentacle, htb-thefrizz, htb-thenotebook, htb-timing, htb-titanic, htb-toby, htb-toolbox, htb-travel, htb-trick, htb-trickster, htb-twomillion, htb-unattended, htb-unbalanced, htb-unicode, htb-union, htb-university, htb-unobtainium, htb-unrested, htb-updown, htb-usage, htb-valentine, htb-validation, htb-variatype, htb-vessel, htb-visual, htb-wall, htb-watcher, htb-whiterabbit, htb-wifinetictwo, htb-writer, htb-writeup, htb-yummy, htb-zero, htb-zetta, htb-zipping
Answer: Web injection techniques include SQL Injection (union-based, blind, stacked queries via sqlmap), Server-Side Template Injection (Jinja2/Twig SSTI to achieve RCE), OS Command Injection via unvalidated inputs, and Local File Inclusion (LFI) to read /etc/passwd or achieve RCE via log poisoning or php wrappers.

---

---
**Q2** | Active Directory lateral movement cheatsheet
Machines: htb-absolute, htb-active, htb-administrator, htb-analysis, htb-anubis, htb-appsanity, htb-apt, htb-arkham, htb-atom, htb-authority, htb-axlle, htb-baby, htb-babytwo, htb-blackfield, htb-blazorized, htb-blurry, htb-bruno, htb-cascade, htb-cerberus, htb-certificate, htb-certified, htb-cicada, htb-coder, htb-compiled, htb-conversor, htb-darkcorp, htb-darkzero, htb-delegate, htb-driver, htb-eighteen, htb-escape, htb-escapetwo, htb-flight, htb-fluffy, htb-forest, htb-freelancer, htb-fulcrum, htb-fuse, htb-ghost, htb-hancliffe, htb-hathor, htb-haze, htb-heist, htb-hospital, htb-infiltrator, htb-intelligence, htb-jab, htb-jeeves, htb-jobtwo, htb-json, htb-mailing, htb-manager, htb-mirage, htb-mist, htb-monteverde, htb-multimaster, htb-nanocorp, htb-nest, htb-netmon, htb-object, htb-office, htb-outdated, htb-overwatch, htb-phantom, htb-pivotapi, htb-pov, htb-puppy, htb-querier, htb-re, htb-rebound, htb-redelegate, htb-reel2, htb-remote, htb-resolute, htb-retro, htb-retrotwo, htb-return, htb-rustykey, htb-sauna, htb-scepter, htb-search, htb-secnotes, htb-sekhmet, htb-sendai, htb-shibuya, htb-signed, htb-silo, htb-sizzle, htb-solarlab, htb-streamio, htb-support, htb-timelapse, htb-tombwatcher, htb-university, htb-vintage, htb-voleur, htb-vulncicada, htb-worker, htb-ypuffy
Answer: AD lateral movement techniques include Pass-the-Hash (PtH) using NTLM hashes via impacket psexec.py, wmiexec.py, smbexec.py, WinRM access via evil-winrm with plaintext credentials or hashes, Overpass-the-Hash / Pass-the-Key using mimikatz or Rubeus, and SMB relay attacks.

---

---
**Q3** | Linux credential harvesting cheatsheet
Machines: htb-abducted, htb-admirer, htb-airtouch, htb-alert, htb-analytics, htb-antique, htb-aragog, htb-ariekei, htb-artificial, htb-awkward, htb-backdoor, htb-bagel, htb-bamboo, htb-bank, htb-barrier, htb-bigbang, htb-bighead, htb-blockblock, htb-bolt, htb-book, htb-bookworm, htb-brainfuck, htb-broker, htb-browsed, htb-bucket, htb-build, htb-builder, htb-busqueda, htb-cap, htb-caption, htb-carrier, htb-chainsaw, htb-chaos, htb-charon, htb-checker, htb-chemistry, htb-clicker, htb-code, htb-coder, htb-codetwo, htb-codify, htb-compiled, htb-corporate, htb-craft, htb-crossfittwo, htb-cybermonday, htb-cypher, htb-darkcorp, htb-derailed, htb-devarea, htb-devoops, htb-devvortex, htb-devzat, htb-download, htb-drive, htb-dump, htb-dynstr, htb-earlyaccess, htb-editor, htb-editorial, htb-ellingson, htb-encoding, htb-enterprise, htb-epsilon, htb-era, htb-eureka, htb-expressway, htb-extension, htb-facts, htb-faculty, htb-falafel, htb-fatty, htb-feline, htb-fingerprint, htb-fluffy, htb-flujab, htb-flustered, htb-forge, htb-formulax, htb-fortune, htb-forwardslash, htb-frolic, htb-ghost, htb-ghoul, htb-giveback, htb-goodgames, htb-greenhorn, htb-guardian, htb-hacknet, htb-hawk, htb-headless, htb-health, htb-hospital, htb-iclean, htb-imagery, htb-inception, htb-intentions, htb-interface, htb-intuition, htb-jeeves, htb-jewel, htb-joker, htb-jupiter, htb-keeper, htb-kotarak, htb-kryptos, htb-lacasadepapel, htb-lantern, htb-laser, htb-late, htb-lazy, htb-lightweight, htb-linkvortex, htb-logforge, htb-luanne, htb-magicgardens, htb-mailroom, htb-manage, htb-mango, htb-mentor, htb-meta, htb-metatwo, htb-mischief, htb-mist, htb-moderators, htb-monitored, htb-monitors, htb-monitorsthree, htb-nest, htb-nineveh, htb-nocturnal, htb-node, htb-nunchucks, htb-obscurity, htb-oouch, htb-openadmin, htb-openkeys, htb-opensource, htb-ophiuchi, htb-ouija, htb-outbound, htb-overflow, htb-overgraph, htb-oz, htb-pandora, htb-passage, htb-pc, htb-permx, htb-perspective, htb-pikatwoo, htb-pivotapi, htb-player, htb-playertwo, htb-pollution, htb-popcorn, htb-postman, htb-precious, htb-pressed, htb-previous, htb-previse, htb-principal, htb-pterodactyl, htb-puppy, htb-quick, htb-race, htb-rainyday, htb-ransom, htb-redcross, htb-redelegate, htb-redpanda, htb-registry, htb-registrytwo, htb-reset, htb-resource, htb-response, htb-retired, htb-rope, htb-routerspace, htb-runner, htb-safe, htb-sandworm, htb-scanned, htb-scavenger, htb-sea, htb-seal, htb-secnotes, htb-secret, htb-seventeen, htb-shrek, htb-sightless, htb-skyfall, htb-slonik, htb-smasher2, htb-snapped, htb-snoopy, htb-soccer, htb-socket, htb-sorcery, htb-soulmate, htb-spectra, htb-spider, htb-squashed, htb-strutted, htb-sunday, htb-surveillance, htb-talkative, htb-tally, htb-teacher, htb-ten, htb-tenet, htb-tentacle, htb-tenten, htb-thenotebook, htb-titanic, htb-toby, htb-toolbox, htb-topology, htb-traceback, htb-travel, htb-traverxec, htb-trick, htb-trickster, htb-underpass, htb-undetected, htb-unicode, htb-updown, htb-usage, htb-variatype, htb-vault, htb-vessel, htb-voleur, htb-waldo, htb-whiterabbit, htb-wifinetic, htb-wifinetictwo, htb-writer, htb-ypuffy, htb-yummy, htb-zetta, htb-zipper
Answer: Linux credential harvesting techniques include inspecting bash history (.bash_history), searching for unencrypted SSH private keys (id_rsa), extracting password hashes from /etc/shadow or KeePass databases (.kdbx) using keepass2john, checking web application configuration files (wp-config.php, .env, config.php), and inspecting memory or process credentials.

---

---
**Q4** | Network service enumeration and reconnaissance cheatsheet
Machines: htb-abducted, htb-access, htb-active, htb-airtouch, htb-antique, htb-apt, htb-aragog, htb-blackfield, htb-bruno, htb-cap, htb-carrier, htb-cascade, htb-chainsaw, htb-clicker, htb-conceal, htb-crossfit, htb-dab, htb-devarea, htb-devel, htb-ethereal, htb-fatty, htb-forest, htb-fortune, htb-fuse, htb-hawk, htb-heist, htb-intense, htb-jail, htb-jobtwo, htb-lame, htb-luke, htb-lustroustwo, htb-mantis, htb-mentor, htb-mischief, htb-monitored, htb-monteverde, htb-netmon, htb-omni, htb-oouch, htb-pandora, htb-pit, htb-pivotapi, htb-rainbow, htb-reaper, htb-redelegate, htb-reel, htb-remote, htb-resolute, htb-response, htb-scepter, htb-servmon, htb-sightless, htb-sizzle, htb-slonik, htb-sneaky, htb-squashed, htb-toolbox, htb-underpass, htb-vulncicada, htb-wifinetic, htb-wingdata
Answer: Reconnaissance techniques include checking anonymous FTP access for sensitive files or uploads, SNMP community string enumeration using snmpwalk or onesixtyone to reveal processes and network interfaces, RPCClient null session enumeration for users and groups, and NFS export discovery using showmount -e for no_root_squash misconfigurations.

---

---
**Q5** | Docker and container escape cheatsheet
Machines: htb-access, htb-agile, htb-airtouch, htb-backdoor, htb-bookworm, htb-brainfuck, htb-carpediem, htb-chainsaw, htb-corporate, htb-cybermonday, htb-data, htb-devarea, htb-earlyaccess, htb-editor, htb-escape, htb-extension, htb-feline, htb-gavel, htb-ghoul, htb-giveback, htb-imagery, htb-intense, htb-laboratory, htb-mischief, htb-monitors, htb-monitorsfour, htb-monitorstwo, htb-obscurity, htb-opensource, htb-outbound, htb-patents, htb-permx, htb-proper, htb-rainyday, htb-ready, htb-reddish, htb-response, htb-retired, htb-runner, htb-sandworm, htb-sau, htb-sharp, htb-sorcery, htb-stacked, htb-strutted, htb-tabby, htb-talkative, htb-underpass, htb-vessel
Answer: Container breakout techniques include mounting host filesystems via the Docker socket (/var/run/docker.sock), abusing --privileged containers via cgroups release_agent or raw disk mounts, abusing local docker or lxd group membership, and container runtime vulnerabilities such as runc (CVE-2024-21626 / CVE-2019-5736).

---


## Specific Questions

---
**Q6** | AS-REP Roasting in Active Directory
Machines: htb-absolute, htb-active, htb-blackfield, htb-forest, htb-infiltrator, htb-intelligence, htb-jab, htb-mantis, htb-multimaster, htb-pivotapi, htb-rebound, htb-sauna, htb-tentacle
Answer: AS-REP Roasting targets Active Directory user accounts that have the DONT_REQ_PREAUTH flag set (Kerberos pre-authentication disabled). An attacker can request an AS-REP message containing an encrypted ticket without credentials, extract the encrypted ticket offline, and crack the password hash using hashcat (mode 18200) or john. Executed using Impacket GetNPUsers.py.

---

---
**Q7** | Server-Side Template Injection (SSTI) in Jinja2
Machines: htb-bolt, htb-chemistry, htb-darkzero, htb-doctor, htb-epsilon, htb-flustered, htb-hacknet, htb-iclean, htb-late, htb-oz, htb-race, htb-sandworm, htb-spider, htb-trickster
Answer: SSTI in Jinja2 occurs when user input is concatenated directly into a template string rather than passed as a context variable. Attackers inject Jinja expressions like {{ config.items() }} or access Python class hierarchies to locate subprocess.Popen and execute arbitrary OS commands.

---

---
**Q8** | MSSQL xp_cmdshell command execution
Machines: htb-blazorized, htb-breach, htb-darkzero, htb-eighteen, htb-escape, htb-escapetwo, htb-fighter, htb-freelancer, htb-ghost, htb-manager, htb-monteverde, htb-pivotapi, htb-querier, htb-redelegate, htb-sendai, htb-signed, htb-tally
Answer: When an attacker acquires credentials to a Microsoft SQL Server with sysadmin privileges or impersonate permissions, they can reconfigure sp_configure to enable xp_cmdshell (sp_configure 'show advanced options', 1; RECONFIGURE; sp_configure 'xp_cmdshell', 1; RECONFIGURE;) and execute operating system shell commands as the SQL service account.

---

---
**Q9** | Redis remote code execution
Machines: htb-atom, htb-catch, htb-cybermonday, htb-format, htb-pollution, htb-postman, htb-reddish, htb-shared
Answer: Unauthenticated Redis servers exposed on port 6379 allow attackers to configure the database working directory (CONFIG SET dir) and database filename (CONFIG SET dbfilename). Attackers exploit this to write an SSH authorized_keys file into /root/.ssh/, write a webshell into a web directory, or write a malicious crontab file into /var/spool/cron/crontabs/ for immediate reverse shell execution.

---

---
**Q10** | Sudo LD_PRELOAD privilege escalation
Machines: htb-clicker, htb-dab, htb-surveillance
Answer: When sudo -l reveals that env_keep += LD_PRELOAD is configured, any user permitted to run a command via sudo can load an arbitrary shared library. The attacker compiles a malicious C shared library with an _init() constructor that calls setuid(0) and /bin/bash, then executes sudo LD_PRELOAD=/tmp/priv.so <allowed_binary> to spawn an immediate root shell.

---

---
**Q11** | BloodHound Active Directory attack path analysis
Machines: htb-absolute, htb-administrator, htb-axlle, htb-babytwo, htb-blackfield, htb-blazorized, htb-breach, htb-certificate, htb-certified, htb-coder, htb-cypher, htb-darkcorp, htb-darkzero, htb-delegate, htb-eighteen, htb-escape, htb-escapetwo, htb-fluffy, htb-forest, htb-freelancer, htb-ghost, htb-haze, htb-infiltrator, htb-intelligence, htb-jab, htb-lustroustwo, htb-manager, htb-mirage, htb-mist, htb-multimaster, htb-nanocorp, htb-object, htb-outdated, htb-phantom, htb-pivotapi, htb-puppy, htb-rebound, htb-redelegate, htb-reel, htb-retrotwo, htb-rustykey, htb-sauna, htb-scepter, htb-search, htb-sendai, htb-shibuya, htb-sizzle, htb-streamio, htb-support, htb-tombwatcher, htb-university, htb-vintage, htb-voleur
Answer: BloodHound and its ingestors (SharpHound.exe, bloodhound-python) enumerate Active Directory domain objects, group memberships, trust relationships, sessions, and Access Control Lists (ACLs). Attackers visualize graph paths to identify privilege escalation routes (e.g. GenericAll, WriteDacl, ForceChangePassword, or Shortest Paths to Domain Admins).

---

---
**Q12** | Linux kernel privilege escalation (Dirty Cow / PwnKit)
Machines: htb-antique, htb-ouija, htb-paper, htb-popcorn, htb-pressed, htb-routerspace, htb-valentine
Answer: Dirty Cow (CVE-2016-5195) exploits a race condition in the Linux kernel copy-on-write (COW) memory mapping to write to read-only files like /etc/passwd. PwnKit (CVE-2021-4034) exploits an out-of-bounds read/write in Polkit pkexec to inject environment variables and execute arbitrary code as root without requiring credentials.

---

---
**Q13** | Server-Side Request Forgery (SSRF) exploitation
Machines: htb-admirertoo, htb-appsanity, htb-awkward, htb-backfire, htb-bigbang, htb-bountyhunter, htb-browsed, htb-catch, htb-cereal, htb-checker, htb-corporate, htb-cybermonday, htb-devarea, htb-down, htb-editorial, htb-encoding, htb-era, htb-forge, htb-fulcrum, htb-gofer, htb-heal, htb-health, htb-intentions, htb-intuition, htb-jarmis, htb-kotarak, htb-lantern, htb-love, htb-nocturnal, htb-overgraph, htb-perspective, htb-player, htb-quick, htb-ready, htb-response, htb-sau, htb-sea, htb-sightless, htb-sorcery, htb-travel, htb-updown, htb-writer
Answer: SSRF allows an attacker to induce the server-side application to make HTTP requests to an arbitrary domain or internal resource. On HTB, it is leveraged to access localhost-only administrative portals (e.g. 127.0.0.1:8080), cloud metadata endpoints (169.254.169.254), or interact with internal microservices and databases (e.g. via gopher:// or dict://).

---

---
**Q14** | Pass-the-Hash with Impacket psexec / wmiexec
Machines: htb-anubis, htb-bruno, htb-darkzero, htb-flight, htb-forest, htb-intelligence, htb-jeeves, htb-mist, htb-querier, htb-redelegate, htb-retrotwo, htb-sauna, htb-search, htb-silo, htb-sizzle, htb-solarlab, htb-voleur, htb-vulncicada
Answer: Pass-the-Hash allows an attacker to authenticate to remote Windows hosts over SMB/RPC using an NTLM password hash without needing the plaintext password. Impacket tools like psexec.py, wmiexec.py, and smbexec.py accept the hash format -hashes LM:NT or :NT to spawn remote command prompts or semi-interactive shells.

---

---
**Q15** | Anonymous FTP access and exploitation
Machines: htb-access, htb-aragog, htb-bruno, htb-cap, htb-chainsaw, htb-conceal, htb-crossfit, htb-dab, htb-devarea, htb-devel, htb-ethereal, htb-fatty, htb-hawk, htb-lame, htb-luke, htb-lustroustwo, htb-netmon, htb-oouch, htb-pivotapi, htb-rainbow, htb-reaper, htb-redelegate, htb-reel, htb-remote, htb-response, htb-servmon, htb-sightless, htb-sizzle, htb-toolbox, htb-wifinetic, htb-wingdata
Answer: Anonymous FTP allows unauthenticated users to log in with username anonymous and an arbitrary password. Attackers enumerate exposed directories to retrieve backup archives, configuration files, SSH keys, or passwords. In configurations with write permissions, attackers upload webshells or reverse shell scripts into web server document roots.

---
