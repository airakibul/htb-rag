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
**Q6** | AS-REP Roasting
Machines: htb-absolute, htb-active, htb-anubis, htb-blackfield, htb-bruno, htb-forest, htb-infiltrator, htb-intelligence, htb-jab, htb-mantis, htb-multimaster, htb-office, htb-outdated, htb-pivotapi, htb-rebound, htb-sauna, htb-support, htb-tentacle
Answer: AS-REP Roasting targets accounts with Kerberos pre-authentication disabled (DONT_REQ_PREAUTH). An attacker requests an AS-REP without credentials, receives a response encrypted with the user's password hash, then cracks it offline with hashcat (mode 18200) or john. Tools: GetNPUsers.py (Impacket), kerbrute, Rubeus.

---

---
**Q7** | certipy usage
Machines: htb-absolute, htb-authority, htb-certified, htb-coder, htb-darkcorp, htb-darkzero, htb-escape, htb-escapetwo, htb-fluffy, htb-haze, htb-infiltrator, htb-manager, htb-mirage, htb-mist, htb-rebound, htb-retro, htb-scepter, htb-sendai, htb-shibuya, htb-tombwatcher, htb-vulncicada
Answer: Certipy is used for: enumerating vulnerable ADCS templates (certipy find), requesting certificates for privilege escalation (certipy req), authenticating with obtained certificates (certipy auth), creating Shadow Credentials (certipy shadow auto), and exploiting ESC1/ESC4/ESC7/ESC8/ESC9 vulnerabilities.

---

---
**Q8** | CVE-2026-4480
Machines: htb-abducted
Answer: CVE-2026-4480 is demonstrated on the Abducted machine. Specific exploitation details should be found in the htb-abducted.md writeup.

---

---
**Q9** | WriteOwner abuse
Machines: htb-anubis, htb-babytwo, htb-certified, htb-darkzero, htb-escape, htb-escapetwo, htb-haze, htb-mist, htb-object, htb-querier, htb-reel, htb-signed, htb-streamio, htb-tombwatcher
Answer: WriteOwner allows an attacker to change the owner of an AD object to themselves, then modify the DACL to grant full control (GenericAll/WriteDACL). This enables password resets, adding users to groups, or extracting credentials. Tools: PowerView (Set-DomainObjectOwner, Add-DomainObjectAcl), bloodyAD, Impacket owneredit/dacledit.

---

---
**Q10** | ESC9 ADCS attack
Machines: htb-certified, htb-scepter
Answer: ESC9 exploits GenericWrite on a user to modify their userPrincipalName (UPN) to match a privileged account. The attacker then requests a certificate with the spoofed UPN and authenticates as the target. Steps: 1) Modify target's UPN to administrator, 2) Request certificate via certipy req, 3) Revert UPN, 4) Authenticate with certipy auth using the certificate. Certipy is the primary tool.

---

---
**Q11** | BloodHound attack paths
Machines: htb-absolute, htb-administrator, htb-axlle, htb-babytwo, htb-blackfield, htb-blazorized, htb-breach, htb-certified, htb-coder, htb-cypher, htb-darkcorp, htb-darkzero, htb-delegate, htb-eighteen, htb-escape, htb-escapetwo, htb-fluffy, htb-forest, htb-freelancer, htb-ghost, htb-haze, htb-infiltrator, htb-intelligence, htb-jab, htb-lustroustwo, htb-manager, htb-mirage, htb-mist, htb-multimaster, htb-nanocorp, htb-object, htb-outdated, htb-phantom, htb-pivotapi, htb-puppy, htb-rebound, htb-redelegate, htb-reel, htb-retrotwo, htb-rustykey, htb-sauna, htb-scepter, htb-search, htb-sendai, htb-shibuya, htb-sizzle, htb-streamio, htb-support, htb-tombwatcher, htb-university, htb-vintage, htb-voleur
Answer: BloodHound identifies shortest paths to Domain Admin, dangerous ACL permissions (GenericAll, WriteDACL, WriteOwner, ForceChangePassword), Kerberoastable/AS-REP Roastable accounts, constrained/unconstrained delegation, group membership chains, and ADCS attack paths. Data collected via SharpHound/bloodhound-python.

---

---
**Q12** | Shadow Credentials attack
Machines: htb-absolute, htb-certified, htb-darkcorp, htb-delegate, htb-escapetwo, htb-fluffy, htb-haze, htb-infiltrator, htb-mist, htb-outdated, htb-puppy, htb-rebound, htb-tombwatcher
Answer: Shadow Credentials attack adds a Key Credential to a target's msDS-KeyCredentialLink attribute. The attacker generates a certificate pair, writes the public key to the attribute, then uses the private key to request a TGT via PKINIT. Tools: certipy shadow auto, pywhisker, whisker. Requires GenericWrite/GenericAll on the target object.

---

---
**Q13** | Samba RCE
Machines: htb-lame, htb-frolic, htb-node, htb-kotarak, htb-brainfuck, htb-falafel, htb-lazy, htb-sneaky, htb-zipper, htb-writer, htb-ypuffy, htb-gofer, htb-overgraph, htb-bamboo, htb-calamity, htb-jail, htb-ropetwo, htb-sekhmet, htb-smasher2, htb-traceback, htb-zetta, htb-tenten, htb-sniper, htb-puppy, htb-abducted
Answer: Samba RCE exploits include CVE-2007-2447 (Samba 3.0.20 username map script command injection, exploited on Lame via Metasploit), CVE-2017-7494 (SambaCry - writable share to load malicious shared library), and misconfigured SMB shares allowing credential theft or file upload for code execution.

---

---
**Q14** | WinRM / evil-winrm shell access
Machines: htb-absolute, htb-administrator, htb-anubis, htb-apt, htb-arkham, htb-atom, htb-authority, htb-axlle, htb-baby, htb-babytwo, htb-blackfield, htb-blazorized, htb-cascade, htb-cerberus, htb-certified, htb-cicada, htb-coder, htb-compiled, htb-darkcorp, htb-darkzero, htb-delegate, htb-driver, htb-eighteen, htb-escape, htb-escapetwo, htb-fluffy, htb-forest, htb-freelancer, htb-fuse, htb-ghost, htb-hancliffe, htb-hathor, htb-haze, htb-heist, htb-infiltrator, htb-jab, htb-jobtwo, htb-mailing, htb-manager, htb-mirage, htb-mist, htb-monteverde, htb-multimaster, htb-nanocorp, htb-object, htb-office, htb-outdated, htb-overwatch, htb-phantom, htb-pivotapi, htb-puppy, htb-re, htb-rebound, htb-redelegate, htb-reel2, htb-remote, htb-resolute, htb-retro, htb-return, htb-rustykey, htb-sauna, htb-scepter, htb-sekhmet, htb-sendai, htb-shibuya, htb-signed, htb-streamio, htb-support, htb-timelapse, htb-tombwatcher, htb-university, htb-vintage, htb-voleur, htb-worker
Answer: Evil-WinRM is used for remote PowerShell shell access over WinRM (port 5985/5986). Used with plaintext passwords, NTLM hashes (pass-the-hash), or certificates. Requires target user to be in Remote Management Users group. Common contexts: post-exploitation lateral movement, using recovered credentials, or after ADCS certificate abuse.

---

---
**Q15** | GenericAll abuse
Machines: htb-administrator, htb-babytwo, htb-certified, htb-darkzero, htb-escapetwo, htb-fluffy, htb-forest, htb-haze, htb-infiltrator, htb-puppy, htb-rebound, htb-redelegate, htb-scepter, htb-search, htb-sendai, htb-signed, htb-support, htb-tombwatcher, htb-university, htb-vintage
Answer: GenericAll grants full control over an AD object. Abuse methods: force password reset (net rpc password), add Shadow Credentials, modify group membership, set SPN for Kerberoasting, write to msDS-AllowedToActOnBehalfOfOtherIdentity for RBCD, or modify DACL. Tools: PowerView, bloodyAD, net rpc, certipy.

---
