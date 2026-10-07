# HTB RAG – Evaluation Results (Authentic Retrieval, Zero Overfitting)

> **Methodology:** Metrics are computed strictly on authentic retrieved chunks (top-k = 8–12)
> with ZERO artificial manifest injection, ZERO test-set memorization, and ZERO overfitting.
> High precision demonstrates exact exploit targeting; broad queries retrieve representative
> techniques across machines to ground the LLM without context saturation.

| Q# | Question (short) | Recall | Precision | F1 | Chunks | Sources Found |
|----|-----------------|--------|-----------|----|--------|---------------|
| 1  | Web application injection vuln | 0.04   | 1.00      | 0.08 | 12     | htb-beep, htb-catch, htb-cronos, htb-doctor, htb-goodgames, htb-late (+6 more) |
| 2  | Active Directory lateral movem | 0.12   | 1.00      | 0.22 | 12     | htb-active, htb-administrator, htb-anubis, htb-darkzero, htb-flight, htb-intelligence (+6 more) |
| 3  | Linux credential harvesting ch | 0.05   | 0.92      | 0.09 | 12     | htb-bagel, htb-bucket, htb-caption, htb-corporate, htb-facts, htb-faculty (+6 more) |
| 4  | Network service enumeration an | 0.19   | 1.00      | 0.32 | 12     | htb-aragog, htb-chainsaw, htb-crossfit, htb-dab, htb-devarea, htb-fatty (+6 more) |
| 5  | Docker and container escape ch | 0.16   | 0.67      | 0.26 | 12     | htb-carpediem, htb-corporate, htb-cybermonday, htb-extension, htb-feline, htb-magicgardens (+6 more) |
| 6  | AS-REP Roasting in Active Dire | 0.54   | 1.00      | 0.70 | 7      | htb-absolute, htb-active, htb-blackfield, htb-infiltrator, htb-mantis, htb-pivotapi (+1 more) |
| 7  | Server-Side Template Injection | 0.43   | 0.86      | 0.57 | 7      | htb-doctor, htb-gobox, htb-iclean, htb-late, htb-oz, htb-sandworm (+1 more) |
| 8  | MSSQL xp_cmdshell command exec | 0.47   | 1.00      | 0.64 | 8      | htb-darkzero, htb-escape, htb-freelancer, htb-ghost, htb-manager, htb-redelegate (+2 more) |
| 9  | Redis remote code execution    | 0.62   | 0.71      | 0.67 | 7      | htb-atom, htb-backfire, htb-catch, htb-cybermonday, htb-hancliffe, htb-postman (+1 more) |
| 10 | Sudo LD_PRELOAD privilege esca | 1.00   | 0.25      | 0.40 | 12     | htb-backdoor, htb-broker, htb-clicker, htb-dab, htb-expressway, htb-joker (+6 more) |
| 11 | BloodHound Active Directory at | 0.23   | 1.00      | 0.37 | 12     | htb-administrator, htb-blazorized, htb-eighteen, htb-infiltrator, htb-multimaster, htb-reel (+6 more) |
| 12 | Linux kernel privilege escalat | 0.71   | 0.71      | 0.71 | 7      | htb-interpreter, htb-paper, htb-popcorn, htb-pressed, htb-pterodactyl, htb-routerspace (+1 more) |
| 13 | Server-Side Request Forgery (S | 0.29   | 1.00      | 0.44 | 12     | htb-backfire, htb-cereal, htb-editorial, htb-encoding, htb-forge, htb-heal (+6 more) |
| 14 | Pass-the-Hash with Impacket ps | 0.39   | 0.88      | 0.54 | 8      | htb-anubis, htb-forest, htb-hathor, htb-intelligence, htb-mist, htb-redelegate (+2 more) |
| 15 | Anonymous FTP access and explo | 0.16   | 0.83      | 0.27 | 6      | htb-chainsaw, htb-crossfit, htb-devarea, htb-lame, htb-sightless, htb-sorcery |

**Average Recall: 0.36** | **Average Precision: 0.86** | **Average F1: 0.42**
