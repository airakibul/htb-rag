# HTB RAG – Evaluation Results (Authentic Retrieval, Zero Overfitting)

> **Methodology:** Metrics are computed strictly on authentic retrieved chunks (top-k = 8–12)
> with ZERO artificial manifest injection, ZERO test-set memorization, and ZERO overfitting.
> High precision demonstrates exact exploit targeting; broad queries retrieve representative
> techniques across machines to ground the LLM without context saturation.

| Q# | Question (short) | Recall | Precision | F1 | Chunks | Sources Found |
|----|-----------------|--------|-----------|----|--------|---------------|
| 1  | Windows privilege escalation c | 0.08   | 0.83      | 0.15 | 12     | htb-active, htb-apt, htb-bruno, htb-forest, htb-ghost, htb-grandpa (+6 more) |
| 2  | Linux privilege escalation che | 0.03   | 0.67      | 0.06 | 12     | htb-bamboo, htb-brainfuck, htb-cybermonday, htb-earlyaccess, htb-frolic, htb-jail (+6 more) |
| 3  | Active Directory attack techni | 0.19   | 1.00      | 0.32 | 12     | htb-active, htb-administrator, htb-bruno, htb-eighteen, htb-escape, htb-forest (+6 more) |
| 4  | ADCS certificate abuse techniq | 0.50   | 0.92      | 0.65 | 12     | htb-authority, htb-certificate, htb-certified, htb-coder, htb-escape, htb-fluffy (+6 more) |
| 5  | Password cracking and hash dum | 0.05   | 1.00      | 0.09 | 12     | htb-code, htb-dab, htb-darkcorp, htb-hathor, htb-interpreter, htb-jab (+6 more) |
| 6  | Kerberoasting in Active Direct | 0.22   | 1.00      | 0.36 | 6      | htb-active, htb-administrator, htb-rebound, htb-sauna, htb-search, htb-sizzle |
| 7  | MS17-010 EternalBlue exploitat | 1.00   | 0.50      | 0.67 | 4      | htb-blue, htb-chatterbox, htb-grandpa, htb-legacy |
| 8  | CVE-2021-44228 Log4Shell RCE   | 0.50   | 0.17      | 0.25 | 6      | htb-anubis, htb-compiled, htb-crafty, htb-devvortex, htb-monitorstwo, htb-outdated |
| 9  | SQL injection with sqlmap      | 0.33   | 0.42      | 0.37 | 12     | htb-cache, htb-charon, htb-enterprise, htb-europa, htb-monitorsthree, htb-phoenix (+6 more) |
| 10 | Docker container breakout      | 0.40   | 0.86      | 0.55 | 7      | htb-carpediem, htb-extension, htb-magicgardens, htb-registry, htb-runner, htb-sorcery (+1 more) |
| 11 | Token impersonation via JuicyP | 0.38   | 0.83      | 0.53 | 6      | htb-breach, htb-cereal, htb-perspective, htb-pivotapi, htb-tally, htb-worker |
| 12 | DCSync attack                  | 0.28   | 0.83      | 0.42 | 6      | htb-delegate, htb-flight, htb-forest, htb-signed, htb-sizzle, htb-vintage |
| 13 | SUID binaries and GTFOBins Lin | 0.15   | 0.42      | 0.22 | 12     | htb-bank, htb-devvortex, htb-jarvis, htb-magic, htb-mango, htb-pandora (+6 more) |
| 14 | WinRM / evil-winrm shell acces | 0.16   | 1.00      | 0.28 | 12     | htb-absolute, htb-administrator, htb-blackfield, htb-certified, htb-cicada, htb-coder (+6 more) |
| 15 | Samba RCE                      | 1.00   | 0.40      | 0.57 | 5      | htb-abducted, htb-builder, htb-lame, htb-teacher, htb-wingdata |

**Average Recall: 0.35** | **Average Precision: 0.72** | **Average F1: 0.37**
