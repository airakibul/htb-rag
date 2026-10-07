# HTB RAG – Evaluation Results (Authentic Retrieval, Zero Overfitting)

> **Methodology:** Metrics are computed strictly on authentic retrieved chunks (top-k = 8–12)
> with ZERO artificial manifest injection, ZERO test-set memorization, and ZERO overfitting.
> High precision demonstrates exact exploit targeting; broad queries retrieve representative
> techniques across machines to ground the LLM without context saturation.

| Q# | Question (short) | Recall | Precision | F1 | Chunks | Sources Found |
|----|-----------------|--------|-----------|----|--------|---------------|
| 1  | Web application injection vuln | 0.03   | 0.83      | 0.07 | 12     | htb-attended, htb-blunder, htb-caption, htb-devarea, htb-devzat, htb-epsilon (+6 more) |
| 2  | Active Directory lateral movem | 0.12   | 1.00      | 0.22 | 12     | htb-active, htb-apt, htb-hathor, htb-jab, htb-redelegate, htb-remote (+6 more) |
| 3  | Linux credential harvesting ch | 0.05   | 1.00      | 0.10 | 12     | htb-bucket, htb-caption, htb-devvortex, htb-devzat, htb-hawk, htb-iclean (+6 more) |
| 4  | Network service enumeration an | 0.18   | 0.92      | 0.30 | 12     | htb-abducted, htb-aragog, htb-crossfit, htb-devarea, htb-fatty, htb-hawk (+6 more) |
| 5  | Docker and container escape ch | 0.20   | 0.83      | 0.33 | 12     | htb-carpediem, htb-cybermonday, htb-data, htb-extension, htb-feline, htb-intuition (+6 more) |
| 6  | AS-REP Roasting in Active Dire | 0.46   | 1.00      | 0.63 | 6      | htb-blackfield, htb-forest, htb-infiltrator, htb-intelligence, htb-multimaster, htb-pivotapi |
| 7  | Server-Side Template Injection | 0.43   | 0.50      | 0.46 | 12     | htb-anubis, htb-chemistry, htb-doctor, htb-flustered, htb-gobox, htb-goodgames (+6 more) |
| 8  | MSSQL xp_cmdshell command exec | 0.41   | 1.00      | 0.58 | 7      | htb-breach, htb-darkzero, htb-escape, htb-escapetwo, htb-querier, htb-sendai (+1 more) |
| 9  | Redis remote code execution    | 0.50   | 0.80      | 0.62 | 5      | htb-catch, htb-cybermonday, htb-data, htb-reddish, htb-shared |
| 10 | Sudo LD_PRELOAD privilege esca | 1.00   | 0.25      | 0.40 | 12     | htb-backendtwo, htb-broker, htb-clicker, htb-dab, htb-intuition, htb-joker (+6 more) |
| 11 | BloodHound Active Directory at | 0.13   | 0.88      | 0.23 | 8      | htb-anubis, htb-axlle, htb-jab, htb-mist, htb-multimaster, htb-rebound (+2 more) |
| 12 | Linux kernel privilege escalat | 0.43   | 0.38      | 0.40 | 8      | htb-antique, htb-interpreter, htb-monitorstwo, htb-paper, htb-permx, htb-routerspace (+2 more) |
| 13 | Server-Side Request Forgery (S | 0.29   | 1.00      | 0.44 | 12     | htb-backfire, htb-editorial, htb-encoding, htb-heal, htb-lantern, htb-love (+6 more) |
| 14 | Pass-the-Hash with Impacket ps | 0.22   | 0.57      | 0.32 | 7      | htb-hathor, htb-redelegate, htb-remote, htb-retrotwo, htb-rustykey, htb-sauna (+1 more) |
| 15 | Anonymous FTP access and explo | 0.23   | 0.88      | 0.36 | 8      | htb-bruno, htb-crossfit, htb-devarea, htb-lame, htb-oouch, htb-pikaboo (+2 more) |

**Average Recall: 0.31** | **Average Precision: 0.79** | **Average F1: 0.36**
