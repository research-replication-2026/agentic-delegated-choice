# AVAILABILITY_SCAFFOLD_CHECK.md

Checked file: confirmatory_2x2/batch/confirmatory_2000_requests_corrected_v2.jsonl
API-secret pattern (`sk-[A-Za-z0-9]{20,}`) found: False
Real-transaction-endpoint pattern (`booking_endpoint|purchase_endpoint|checkout|stripe|paypal|transaction_url`) found: False

Both False: no API credentials and no real-transaction endpoints are present in the submitted batch file, consistent with the claim in manuscript/AVAILABILITY.md that the materials contain no secrets requiring redaction before release.
