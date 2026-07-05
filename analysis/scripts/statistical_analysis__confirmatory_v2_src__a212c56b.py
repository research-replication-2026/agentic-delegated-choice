from __future__ import annotations

from collections import defaultdict

from src.common import read_csv, write_csv


def rate(rows: list[dict], condition: str) -> float:
    subset = [r for r in rows if r["condition"] == condition]
    return sum(int(r["partner_selected"]) for r in subset) / len(subset) if subset else 0


def main() -> None:
    rows = read_csv("data/processed/mock_scored.csv")
    out = []
    for agenticity in ["A0", "A1"]:
        r0 = rate(rows, f"C0_{agenticity}")
        r1 = rate(rows, f"C1_{agenticity}")
        r2 = rate(rows, f"C2_{agenticity}")
        out.extend([
            {"contrast": f"C1_vs_C0_{agenticity}", "difference": round(r1 - r0, 4), "analysis_note": "Mock descriptive placeholder; confirmatory analysis will use mixed logistic regression."},
            {"contrast": f"C2_vs_C0_{agenticity}", "difference": round(r2 - r0, 4), "analysis_note": "Mock descriptive placeholder; confirmatory analysis will use mixed logistic regression."},
        ])
    grouped = defaultdict(list)
    for r in rows:
        grouped[r["domain"]].append(r)
    for domain, domain_rows in grouped.items():
        out.append({"contrast": f"C2_vs_C0_{domain}", "difference": round(rate(domain_rows, "C2_A1") - rate(domain_rows, "C0_A1"), 4), "analysis_note": "Domain robustness placeholder."})
    write_csv("results/tables/mock_statistical_analysis.csv", out)
    print("Mock statistical analysis written.")


if __name__ == "__main__":
    main()
