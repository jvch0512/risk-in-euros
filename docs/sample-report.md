# Cyber risk in euros: Acme Logistics (sample)

Monte Carlo, 10000 iterations, seed 1. Inputs are estimates; the output is only as good as they are.

- Expected annual loss: **€642.339**
- Typical year (median): €392.997
- Bad year (1 in 10): €1.572.766
- Very bad year (1 in 20): €2.215.517

| Scenario | Expected annual loss | 1 in 10 year | Years with no loss |
|---|---|---|---|
| Business email compromise | €187.714 | €409.581 | 14% |
| Ransomware on core systems | €163.633 | €318.353 | 90% |
| Personal data breach (GDPR) | €162.433 | €677.880 | 79% |
| Cloud outage at key supplier | €128.559 | €335.117 | 34% |

## Control ROI (paired simulation)

| Control | Scenario | Cost | Annual saving | Net | ROI |
|---|---|---|---|---|---|
| Payment call-back control | Business email compromise | €8.000 | €112.628 | €104.628 | 13.1x |
| Phishing-resistant MFA | Business email compromise | €25.000 | €72.925 | €47.925 | 1.9x |
| Immutable offline backups | Ransomware on core systems | €40.000 | €73.635 | €33.635 | 0.8x |
| EDR with 24x7 response | Ransomware on core systems | €90.000 | €97.263 | €7.263 | 0.1x |
| Data minimisation programme | Personal data breach (GDPR) | €60.000 | €56.851 | €-3.149 | -0.1x |
