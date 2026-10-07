# HTB RAG – Evaluation Results (Authentic Retrieval, Zero Overfitting)

> **Methodology:** Metrics are computed strictly on authentic retrieved chunks (top-k = 8–12)
> with ZERO artificial manifest injection, ZERO test-set memorization, and ZERO overfitting.
> High precision demonstrates exact exploit targeting; broad queries retrieve representative
> techniques across machines to ground the LLM without context saturation.

| Q# | Question (short) | Recall | Precision | F1 | Chunks | Sources Found |
|----|-----------------|--------|-----------|----|--------|---------------|
| 1  | Windows privilege escalation c | 0.09   | 0.92      | 0.17 | 12     | htb-apt, htb-axlle, htb-bruno, htb-certificate, htb-control, htb-devel (+6 more) |
| 2  | Linux privilege escalation che | 0.04   | 0.92      | 0.08 | 12     | htb-alert, htb-craft, htb-download, htb-drive, htb-encoding, htb-forgot (+6 more) |
| 3  | Active Directory attack techni | 0.16   | 0.83      | 0.27 | 12     | htb-active, htb-anubis, htb-darkzero, htb-delegate, htb-intelligence, htb-mantis (+6 more) |
| 4  | ADCS certificate abuse techniq | 0.50   | 0.92      | 0.65 | 12     | htb-certificate, htb-certified, htb-coder, htb-darkcorp, htb-darkzero, htb-escape (+6 more) |
| 5  | Password cracking and hash dum | 0.04   | 0.92      | 0.08 | 12     | htb-awkward, htb-brainfuck, htb-dab, htb-extension, htb-flujab, htb-giddy (+6 more) |
| 6  | Kerberoasting in Active Direct | 0.15   | 1.00      | 0.26 | 4      | htb-active, htb-intelligence, htb-pivotapi, htb-sizzle |
| 7  | MS17-010 EternalBlue exploitat | 1.00   | 0.50      | 0.67 | 4      | htb-blue, htb-gofer, htb-legacy, htb-scrambled |
| 8  | CVE-2021-44228 Log4Shell RCE   | 1.00   | 0.50      | 0.67 | 4      | htb-crafty, htb-devvortex, htb-logforge, htb-monitorstwo |
| 9  | SQL injection with sqlmap      | 0.27   | 0.33      | 0.30 | 12     | htb-cache, htb-charon, htb-crossfittwo, htb-enterprise, htb-intentions, htb-monitorsthree (+6 more) |
| 10 | Docker container breakout      | 0.33   | 0.71      | 0.45 | 7      | htb-cybermonday, htb-extension, htb-feline, htb-runner, htb-sink, htb-stacked (+1 more) |
| 11 | Token impersonation via JuicyP | 0.31   | 0.57      | 0.40 | 7      | htb-cereal, htb-darkzero, htb-ghost, htb-hackback, htb-pivotapi, htb-tally (+1 more) |
| 12 | DCSync attack                  | 0.61   | 0.92      | 0.73 | 12     | htb-administrator, htb-blazorized, htb-delegate, htb-flight, htb-forest, htb-hathor (+6 more) |
| 13 | SUID binaries and GTFOBins Lin | 0.21   | 0.58      | 0.30 | 12     | htb-chainsaw, htb-earlyaccess, htb-flujab, htb-forwardslash, htb-lazy, htb-magic (+6 more) |
| 14 | WinRM / evil-winrm shell acces | 0.15   | 0.92      | 0.26 | 12     | htb-absolute, htb-apt, htb-blazorized, htb-coder, htb-compiled, htb-escapetwo (+6 more) |
| 15 | Samba RCE                      | 1.00   | 0.40      | 0.57 | 5      | htb-abducted, htb-inject, htb-lame, htb-nibbles, htb-wingdata |

**Average Recall: 0.39** | **Average Precision: 0.73** | **Average F1: 0.39**
