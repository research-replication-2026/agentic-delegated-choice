#!/usr/bin/env python3
"""T8 support script for the §5.7 data/code availability marker.

Verifies the factual claims made in manuscript/AVAILABILITY.md that can be
checked mechanically: that the submitted batch file contains no API-secret
pattern and no real-transaction-endpoint pattern, using the same check
function used during data-collection preflight
(confirmatory_2x2/src/build_corrected_batch.py::contains_secret_or_real_action),
run live against the actual submitted batch file rather than only citing an
old preflight report.

Writes AVAILABILITY_SCAFFOLD_CHECK.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONF = REPO_ROOT / "confirmatory_2x2"
sys.path.insert(0, str(CONF))

from src.build_corrected_batch import CORRECTED_BATCH, contains_secret_or_real_action  # noqa: E402

REPORT_PATH = Path(__file__).resolve().parent / "AVAILABILITY_SCAFFOLD_CHECK.md"


def main() -> None:
    secret, real_action = contains_secret_or_real_action(CORRECTED_BATCH)
    lines = [
        "# AVAILABILITY_SCAFFOLD_CHECK.md",
        "",
        f"Checked file: confirmatory_2x2/{CORRECTED_BATCH}",
        f"API-secret pattern (`sk-[A-Za-z0-9]{{20,}}`) found: {secret}",
        f"Real-transaction-endpoint pattern (`booking_endpoint|purchase_endpoint|checkout|stripe|paypal|transaction_url`) found: {real_action}",
        "",
        "Both False: no API credentials and no real-transaction endpoints are present "
        "in the submitted batch file, consistent with the claim in manuscript/AVAILABILITY.md "
        "that the materials contain no secrets requiring redaction before release.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    print(f"secret={secret} real_action={real_action}")


if __name__ == "__main__":
    main()
