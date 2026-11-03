# Publication review and exclusions

The new release was reviewed as a whitelist, not copied wholesale from the research workspace. Raw requests/responses concern synthetic scenarios, artificial option IDs and experimental configurations, not real participants. Assignment files formerly named `PRIVATE` contain synthetic randomization/scoring mappings needed for replication; their public role and hashes are recorded without publishing an operator identity.

## Published

- Exact archived request and response bytes, losslessly compressed. The GPT `billing` object contains only the nonidentifying `payer` enum. Account-related `user`, `safety_identifier` and `prompt_cache_key` fields were inspected for populated identifying content; no populated values were found in the released GPT outputs.
- Synthetic scenarios, benchmark and referent/assignment mappings.
- Existing coding labels exported without XLSX document properties or free-text comments.
- Frozen scientific code and source-to-release hashes; scientific comparison targets and reproducible outputs.
- Exact numeric table text from the final manuscript, excluding title/author forms and the full manuscript document.

## Excluded or transformed

| Material | Treatment and reason |
|---|---|
| Original human coding XLSX and metadata/comments | Original files retained and hashed locally; verified labels exported to deidentified CSV. Creator/editor fields and comments are excluded for anonymity. |
| Internal SQLite operational ledger, authorizations and account/cost evidence | Not published. Only verified request-hash/state summaries are released. |
| Full manuscripts, response letters and correspondence | Not published; final manuscript hash and numeric table projections support confrontation. |
| Local absolute source_path column in NLP registry | Excluded from the 8,000-row public projection; original source hash retained. Other scientific values are unchanged. |
| One hard-coded personal path in archival prepare_freeze.py | Replaced by `<LOCAL_ARCHIVED_MANUSCRIPT_PATH>` in a manuscript-protection guard. No experimental instruction or model parameter is changed. Original/public hashes and transformation are recorded. |
| Credentials, environment files, service tokens and provider submission clients | Not included. Reproduction does not read credentials or call providers. |
| Historical diagnostics unrelated to the revised sample, pilot fixtures and operational logs | Not included in revised data; historical study files already in the repository keep their identities. |

`source_to_release_manifest.csv` records byte-identical, lossless compression and projection/redaction transformations. `RELEASE_SHA256.json` pins all immutable new inputs, scripts and reference outputs. A local complete inventory retains original absolute paths and hashes without publishing them. `executed_request_seals.json` verifies the GPT dated freeze and Claude submitted canonical-payload digests without copying the ledger.

`CONFIDENTIALITY_SCAN.json` records the actual final scan of new public files, including decompressed archives, for high-confidence credential signatures, private-key blocks, personal local paths and email addresses. A clean automated scan is a bounded check, not a universal proof that arbitrary confidential content is absent. The explicit source review and exclusions above are retained alongside it.
