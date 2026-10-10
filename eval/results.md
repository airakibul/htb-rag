# HTB RAG – Evaluation Results (Dual-Track Evaluation)

> **Dual-Track Methodology:**
> - **Chunk Precision & Recall:** Computed strictly on authentic retrieved chunks (top-k = 5–8) to evaluate procedure accuracy without context bloat.
> - **Graph Corpus Recall:** Evaluates overall catalogue coverage provided by the Knowledge Graph Manifest table for broad queries.

| Q# | Question (short) | Chunk P | Chunk R | Graph R | Chunks | Sources Found |
|----|-----------------|---------|---------|---------|--------|---------------|
| 1  | Windows privilege escalation c | 0.75    | 0.60    | 1.00    | 8      | htb-acute, htb-analysis, htb-bruno, htb-devel, htb-media, htb-nanocorp (+2 more) |
| 2  | Linux privilege escalation che | 0.38    | 0.30    | 1.00    | 8      | htb-bamboo, htb-bank, htb-cache, htb-devvortex, htb-expressway, htb-pterodactyl (+2 more) |
| 3  | Active Directory attack techni | 0.88    | 0.70    | 1.00    | 8      | htb-active, htb-administrator, htb-bruno, htb-delegate, htb-escape, htb-intelligence (+2 more) |
| 4  | ADCS certificate abuse techniq | 0.88    | 0.88    | 1.00    | 8      | htb-certificate, htb-certified, htb-coder, htb-darkzero, htb-escape, htb-manager (+2 more) |
| 5  | Password cracking and hash dum | 0.62    | 0.56    | 0.89    | 8      | htb-absolute, htb-darkcorp, htb-interpreter, htb-jab, htb-sauna, htb-shibboleth (+2 more) |
| 6  | Kerberoasting in Active Direct | 1.00    | 0.57    | 0.57    | 4      | htb-active, htb-administrator, htb-rebound, htb-sizzle |
| 7  | MS17-010 EternalBlue exploitat | 0.67    | 1.00    | 1.00    | 3      | htb-blue, htb-legacy, htb-mantis |
| 8  | CVE-2021-44228 Log4Shell RCE   | 0.25    | 0.50    | 0.50    | 4      | htb-anubis, htb-crafty, htb-devvortex, htb-shibboleth |
| 9  | SQL injection with sqlmap      | 0.38    | 0.38    | 1.00    | 8      | htb-charon, htb-crossfittwo, htb-enterprise, htb-health, htb-intentions, htb-jarvis (+2 more) |
| 10 | Docker container breakout      | 1.00    | 0.57    | 0.57    | 4      | htb-carpediem, htb-extension, htb-monitors, htb-runner |
| 11 | Token impersonation via JuicyP | 1.00    | 0.43    | 0.43    | 3      | htb-cereal, htb-tally, htb-worker |
| 12 | DCSync attack                  | 1.00    | 0.62    | 0.62    | 5      | htb-delegate, htb-forest, htb-sauna, htb-sizzle, htb-vintage |
| 13 | SUID binaries and GTFOBins Lin | 0.38    | 0.38    | 1.00    | 8      | htb-forwardslash, htb-mango, htb-pandora, htb-photobomb, htb-pterodactyl, htb-retired (+2 more) |
| 14 | WinRM / evil-winrm shell acces | 0.38    | 0.30    | 0.90    | 8      | htb-absolute, htb-administrator, htb-anubis, htb-apt, htb-blazorized, htb-infiltrator (+2 more) |
| 15 | Samba RCE                      | 0.40    | 1.00    | 1.00    | 5      | htb-abducted, htb-interpreter, htb-lame, htb-mailing, htb-teacher |

**Chunk Precision: 0.66** | **Chunk Recall: 0.59** | **Corpus Graph Recall: 0.83** | **Average F1: 0.59**
