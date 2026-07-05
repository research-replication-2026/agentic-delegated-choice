# Cost estimation

Token estimates use the existing pilot file `data/processed/pilot_results.csv`. Prices are read from `config/pricing.yaml` and are placeholders that must be manually verified before any real launch.

| Metric | Value |
| --- | --- |
| Mean input tokens | 1317.9 |
| Mean output tokens | 152.6 |
| Standard cost per observation | 0.003173 |
| Standard cost for 2,000 observations | 6.35 |
| Batch API cost for 2,000 observations | 3.17 |
| Standard cost with 20% margin | 7.62 |
| Batch cost with 20% margin | 3.81 |

No API call is used to obtain tariffs.
