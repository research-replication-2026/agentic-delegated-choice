# Anonymity audit and standalone review distribution

**Scope:** author/coder/operator identities in the public replication files, nested archives, document/image metadata and reachable Git history. Scientific citations, model identifiers, artificial option IDs and synthetic response keys are retained; they are necessary for reproducibility and do not identify study participants. No real participants were included in the synthetic experiment.

## Results

The complete repository was inspected, rather than only `revised_8000/`: **464 previously published files**, plus the newly added checker, were reviewed. The initial full scan covered **23 Office containers, 21 PDFs, 30 PNGs, 72 gzip archives** and the six reachable commits present before this anonymity update. Nested XML/relationships, PDF text and author metadata, image properties and additional historical content were examined. The machine-readable final scan is under `revised_8000/provenance/ANONYMITY_FILE_AUDIT.json`; payload counts there include decompressed content and are distinguished from physical file counts.

- No author-specific personal name, institution, personal email address or personal local filesystem path was found using the locally supplied identity terms. These private search terms are not included in the public checker, logs or report.
- The Office identity properties found were empty or generic tool metadata; PDF author metadata contained no personal identity. Images contained generic software metadata and no EXIF requiring review.
- Historical unsanitized coding workbooks and free-text comments remain excluded. The supplied anonymized A/B Excel versions are now included, with all 800 labels verified against the retained A/B CSVs; the final CSV is also retained. No author/editor identity, comments, hidden content or external links were detected in these two public workbooks.
- The earlier scientific raw archives, assignments, frozen rules, labels and analytical results were not changed by this anonymity review. No classification, adjudication, experiment or model call was performed.
- The GitHub account's public profile did not display a public email, institution, location, biography or external website at the time checked. Private authenticated-account data are not copied into the release.

The audit found **no personal identifiers needing removal from the already released scientific files**. This update adds broader verification and a platform-independent review artifact; it does not claim to have deleted nonexistent identifiers or silently alter the scientific data.

## Anonymous standalone ZIP

`ANONYMOUS_REPLICATION_8000.zip` is intended for anonymous review. It contains the revised study's immutable inputs, exact request/response archives, deidentified coding labels, original rules, portable scripts and reference tables. It excludes:

- `.git`, commits, account/profile information, repository-state metadata and PR/workflow links;
- full manuscripts, title/author forms, correspondence and historical unsanitized source coding workbooks;
- personal identity dictionaries used for private verification;
- dependency caches, operating-system metadata and precomputed analytical-output dependencies.

The standalone README does not link to a hosting profile. ZIP entry timestamps and permissions are normalized, no ZIP comment is included, and no source username or path is written into the archive. The input hash manifest is regenerated for this distribution because its README and excluded repository metadata differ from the public checkout. All scientific data and coding labels remain byte-identical to their reviewed public equivalents. The three documented analytical commands were independently run from this standalone distribution and passed.

## Platform and historical limits

GitHub still exposes its hosting-account alias, ownership, PR actors and commit attribution. Existing Git commits use a generic account display label and a GitHub no-reply address, or an anonymous placeholder identity. These are distinguished from the deidentified file contents; they are not represented as removed. Public repository history, cached pages, earlier downloads and cross-repository links cannot be made unlinkable merely by cleaning the working files. The earlier instruction to preserve `main` remains respected; no destructive history rewrite or account-profile mutation was performed.

For blind-review delivery, use the standalone ZIP rather than assuming a GitHub web page is free of platform metadata. Neither this audit nor any automatic scan can guarantee that scientific subject matter or external copies can never support reidentification. The verdict is **PASS for the inspected file contents and metadata**, with these explicit platform/linkability limits.

## Recheck

The checker requires Pillow (installed with the plotting dependencies) and Poppler `pdfinfo`/`pdftotext` for complete PDF review:

```bash
python -B revised_8000/analysis/audit_anonymity.py --history --report /tmp/anonymity-audit.json
```

For a private local identity-term check, optionally supply `--private-terms-file /path/outside/repository/private_terms.json`, containing a JSON array of terms. The checker reports only finding categories and affected file paths, never the identity values. Do not publish that dictionary. The normal `check_release.py` also rejects identifying email/path/credential patterns while permitting the reserved anonymous email placeholder used in archived anonymous metadata.

The two public anonymized Excel files and their structural checks are documented in [coding provenance](revised_8000/disclosure_validation/PROVENANCE.md). Their privacy cleanup changes file hashes relative to the historical records; all published scientific annotations are unchanged.
