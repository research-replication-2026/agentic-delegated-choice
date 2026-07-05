# Cost estimation

Token usage is estimated from `data/processed/pilot_results.csv`. Pricing is read from `config/pricing.yaml`; the prices are placeholders and must be manually verified before a real run. No API call is used to obtain tariffs.

| plan | observations | mean_input_tokens_from_pilot | mean_output_tokens_from_pilot | estimated_cost | estimated_cost_with_20pct_margin |
| --- | --- | --- | --- | --- | --- |
| economical | 1200 | 1317.9 | 152.6 | 3.81 | 4.57 |
| recommended | 2880 | 1317.9 | 152.6 | 9.14 | 10.97 |
| extended | 3600 | 1317.9 | 152.6 | 11.42 | 13.71 |
