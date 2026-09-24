# HTB RAG – Answer Key

> Built manually by grepping `raw/*.md` — NOT from the RAG system.

---

## Broad Questions

---
**Q1** | Windows privilege escalation cheatsheet
Machines: htb-access, htb-arctic, htb-arkham, htb-bastard, htb-bastion, htb-bounty, htb-cascade, htb-conceal, htb-devel, htb-driver, htb-escape, htb-fighter, htb-forest, htb-fulcrum, htb-ghost, htb-giddy, htb-grandpa, htb-granny, htb-helpline, htb-office, htb-optimum, htb-querier, htb-re, htb-reel, htb-return, htb-sauna, htb-servmon, htb-silo, htb-sizzle, htb-tally, htb-vulncicada, htb-worker
Answer: Windows privesc techniques include token impersonation (Potato family), SeImpersonatePrivilege abuse, SAM/SYSTEM hive dumps, unquoted service paths, DLL hijacking, AlwaysInstallElevated, PrintSpoofer, NTLM relay to ADCS, WCF service injection, NSClient++ exploits, and AD-integrated DNS abuse.

---

---
**Q2** | Linux privilege escalation cheatsheet
Machines: htb-admirer, htb-bashed, htb-brainfuck, htb-cache, htb-calamity, htb-celestial, htb-cronos, htb-curling, htb-doctor, htb-ellingson, htb-falafel, htb-irked, htb-lacasadepapel, htb-lightweight, htb-nineveh, htb-obscurity, htb-photobomb, htb-popcorn, htb-redcross, htb-routerspace, htb-scriptkiddie, htb-sneakymailer, htb-tartarsauce, htb-teacher, htb-traceback, htb-valentine, htb-waldo, htb-zipper
Answer: Linux privesc techniques include sudo misconfiguration, SUID binary abuse, cron job hijacking, kernel exploits (DirtyCow CVE-2016-5195), capability abuse, NFS misconfiguration, writable /etc/passwd, PATH hijacking, Docker/LXD group escape, PAM cache symlink attacks, and snapd vulnerabilities.

---

---
**Q3** | Active Directory attack techniques cheatsheet
Machines: htb-absolute, htb-active, htb-administrator, htb-anubis, htb-apt, htb-authority, htb-babytwo, htb-blackfield, htb-blazorized, htb-breach, htb-cascade, htb-certified, htb-coder, htb-darkcorp, htb-darkzero, htb-delegate, htb-escape, htb-escapetwo, htb-fluffy, htb-forest, htb-freelancer, htb-ghost, htb-haze, htb-infiltrator, htb-intelligence, htb-jab, htb-manager, htb-mirage, htb-mist, htb-multimaster, htb-object, htb-outdated, htb-pivotapi, htb-rebound, htb-reel, htb-retrotwo, htb-sauna, htb-scepter, htb-search, htb-sendai, htb-shibuya, htb-sizzle, htb-streamio, htb-support, htb-tombwatcher, htb-university, htb-vintage, htb-voleur
Answer: AD techniques include AS-REP Roasting, Kerberoasting, DCSync, BloodHound enumeration, NTLM relay, constrained/unconstrained delegation abuse, RBCD, Shadow Credentials, ACL abuse (GenericAll, WriteDACL, WriteOwner), Golden/Silver ticket, Pass-the-Hash, GMSA password extraction, and ADCS certificate abuse (ESC1-ESC9).

---

---
**Q4** | ADCS certificate abuse techniques
Machines: htb-absolute, htb-authority, htb-certified, htb-coder, htb-darkcorp, htb-darkzero, htb-escape, htb-escapetwo, htb-fluffy, htb-haze, htb-infiltrator, htb-manager, htb-mirage, htb-mist, htb-rebound, htb-retro, htb-scepter, htb-sendai, htb-shibuya, htb-tombwatcher, htb-vulncicada
Answer: ADCS abuse techniques include ESC1 (misconfigured certificate templates), ESC4 (template ACL abuse), ESC7 (CA officer approval bypass), ESC8 (NTLM relay to HTTP enrollment), ESC9 (GenericWrite on certificate template), Shadow Credentials via certipy, and certificate-based authentication for privilege escalation.

---

---
**Q5** | Password cracking and hash dumping techniques
Machines: htb-absolute, htb-active, htb-anubis, htb-apt, htb-authority, htb-bastion, htb-blackfield, htb-cascade, htb-cerberus, htb-certified, htb-coder, htb-darkcorp, htb-darkzero, htb-escape, htb-escapetwo, htb-fluffy, htb-forest, htb-freelancer, htb-fuse, htb-haze, htb-heist, htb-infiltrator, htb-jab, htb-mailing, htb-manager, htb-mirage, htb-mist, htb-monteverde, htb-multimaster, htb-object, htb-office, htb-outdated, htb-pivotapi, htb-querier, htb-rebound, htb-remote, htb-resolute, htb-retro, htb-return, htb-sauna, htb-scepter, htb-sendai, htb-servmon, htb-shibuya, htb-sizzle, htb-streamio, htb-support, htb-timelapse, htb-tombwatcher, htb-university, htb-vintage, htb-voleur, htb-vulncicada
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
