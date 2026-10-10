# HTB RAG – Evaluation Results (Dual-Track Evaluation)

> **Dual-Track Methodology:**
> - **Chunk Precision & Recall:** Computed strictly on authentic retrieved chunks (top-k = 5–8) to evaluate procedure accuracy without context bloat.
> - **Graph Corpus Recall:** Evaluates overall catalogue coverage provided by the Knowledge Graph Manifest table for broad queries.

| Q# | Question (short) | Chunk P | Chunk R | Graph R | Chunks | Sources Found |
|----|-----------------|---------|---------|---------|--------|---------------|
| 1  | Web application injection vuln | 0.88    | 0.70    | 1.00    | 8      | htb-chemistry, htb-doctor, htb-goodgames, htb-overgraph, htb-oz, htb-perspective (+2 more) |
| 2  | Active Directory lateral movem | 1.00    | 0.80    | 0.90    | 8      | htb-active, htb-flight, htb-jab, htb-pivotapi, htb-redelegate, htb-retrotwo (+2 more) |
| 3  | Linux credential harvesting ch | 0.88    | 0.70    | 0.90    | 8      | htb-beep, htb-caption, htb-hawk, htb-player, htb-pterodactyl, htb-shibboleth (+2 more) |
| 4  | Network service enumeration an | 0.88    | 0.70    | 0.80    | 8      | htb-abducted, htb-conceal, htb-devarea, htb-lustroustwo, htb-reel, htb-remote (+2 more) |
| 5  | Docker and container escape ch | 0.88    | 0.70    | 1.00    | 8      | htb-carpediem, htb-cybermonday, htb-extension, htb-monitors, htb-runner, htb-shoppy (+2 more) |
| 6  | AS-REP Roasting in Active Dire | 1.00    | 0.71    | 0.71    | 5      | htb-blackfield, htb-forest, htb-pivotapi, htb-rebound, htb-sauna |
| 7  | Server-Side Template Injection | 0.75    | 0.43    | 0.43    | 4      | htb-doctor, htb-iclean, htb-oz, htb-sandworm |
| 8  | MSSQL xp_cmdshell command exec | 0.80    | 0.50    | 0.50    | 5      | htb-darkzero, htb-escape, htb-ghost, htb-redelegate, htb-signed |
| 9  | Redis remote code execution    | 0.20    | 0.14    | 0.14    | 5      | htb-blue, htb-buff, htb-editor, htb-interpreter, htb-shared |
| 10 | Sudo LD_PRELOAD privilege esca | 0.62    | 1.00    | 1.00    | 8      | htb-broker, htb-clicker, htb-dab, htb-expressway, htb-joker, htb-openkeys (+2 more) |
| 11 | BloodHound Active Directory at | 0.88    | 0.88    | 1.00    | 8      | htb-administrator, htb-eighteen, htb-forest, htb-infiltrator, htb-multimaster, htb-pivotapi (+2 more) |
| 12 | Linux kernel privilege escalat | 1.00    | 0.71    | 0.71    | 5      | htb-antique, htb-paper, htb-popcorn, htb-routerspace, htb-valentine |
| 13 | Server-Side Request Forgery (S | 1.00    | 0.62    | 0.62    | 5      | htb-backfire, htb-editorial, htb-forge, htb-lantern, htb-love |
| 14 | Pass-the-Hash with Impacket ps | 0.80    | 0.50    | 0.50    | 5      | htb-anubis, htb-hathor, htb-redelegate, htb-retrotwo, htb-sizzle |
| 15 | Anonymous FTP access and explo | 0.60    | 0.38    | 0.38    | 5      | htb-devarea, htb-lame, htb-oouch, htb-sightless, htb-sorcery |

**Chunk Precision: 0.81** | **Chunk Recall: 0.63** | **Corpus Graph Recall: 0.71** | **Average F1: 0.70**
