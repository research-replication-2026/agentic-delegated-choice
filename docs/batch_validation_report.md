# Batch validation report

## 1. Files Checked

All required files were present.

## 2. Hashes Before And After

| File | Before | After | Status |
| --- | --- | --- | --- |
| batch/confirmatory_2000_requests.jsonl | `9c89339e0a3c90813528aae6f13e475597cd745359fd553ea560281e9a7b4448` | `9c89339e0a3c90813528aae6f13e475597cd745359fd553ea560281e9a7b4448` | UNCHANGED |
| data/locked/confirmatory_scenarios.json | `1fd1df266514b52723d66b4c128db6bb0b2e358caabd08b824d4409d58d0cb0d` | `1fd1df266514b52723d66b4c128db6bb0b2e358caabd08b824d4409d58d0cb0d` | UNCHANGED |
| data/locked/confirmatory_run_plan.csv | `35714495d2e3ed72523692c15d6d54f2eb972d26aff4f87a3cbe7bb0439fbd92` | `35714495d2e3ed72523692c15d6d54f2eb972d26aff4f87a3cbe7bb0439fbd92` | UNCHANGED |
| data/locked/LOCKED_SET_HASH.txt | `1d053f2e453705b543dc98b12711c50a41c51088aa4f33561c486742643b55c7` | `1d053f2e453705b543dc98b12711c50a41c51088aa4f33561c486742643b55c7` | UNCHANGED |
| data/locked/RUN_PLAN_HASH.txt | `3d880e86c043d1bc4dd9f72f063c703173a5d5a8574ffa1021612cf98130b5d0` | `3d880e86c043d1bc4dd9f72f063c703173a5d5a8574ffa1021612cf98130b5d0` | UNCHANGED |
| schemas/submit_agentic_decision.json | `d3ba1cca96e51fb5e0664fc63be8307f2aa0c0facefac68c23fc2b1916e0dc42` | `d3ba1cca96e51fb5e0664fc63be8307f2aa0c0facefac68c23fc2b1916e0dc42` | UNCHANGED |
| prompts/neutral_low_agenticity.txt | `c653c3db52d8f470ebd73ff349115f68bc199b7c3f8f5f1decb05bc747a71ec9` | `c653c3db52d8f470ebd73ff349115f68bc199b7c3f8f5f1decb05bc747a71ec9` | UNCHANGED |
| prompts/commercial_low_agenticity.txt | `588003ecd992be09e3a8f01123a61bbe9e58fbb6c777891aad88a65cbb9a38fa` | `588003ecd992be09e3a8f01123a61bbe9e58fbb6c777891aad88a65cbb9a38fa` | UNCHANGED |
| prompts/neutral_high_agenticity.txt | `045c0d406c784f886a813ee7c64cb1155c57f358b8c94eaa86a70e80aac1c90f` | `045c0d406c784f886a813ee7c64cb1155c57f358b8c94eaa86a70e80aac1c90f` | UNCHANGED |
| prompts/commercial_high_agenticity.txt | `e76274b42441149cb133e2d5e02671d0235b0248c60f08aa7b0e98ab82853622` | `e76274b42441149cb133e2d5e02671d0235b0248c60f08aa7b0e98ab82853622` | UNCHANGED |

## 3. Line Count

Non-empty JSONL rows: 2000

## 4. JSON Validity

Valid JSON requests: 2000

## 5. Request Uniqueness

Unique custom IDs: 2000

## 6. Distribution By Condition

| Condition | Observations |
| --- | ---: |
| neutral_low_agenticity | 500 |
| commercial_low_agenticity | 500 |
| neutral_high_agenticity | 500 |
| commercial_high_agenticity | 500 |

## 7. Distribution By Domain

| Domain | Observations |
| --- | ---: |
| hotels | 800 |
| software | 600 |
| electronics | 600 |

## 8. Repetitions By Scenario

Each scenario-condition cell has exactly 10 repetitions: PASS.

## 9. Matched Prompt Validation

Matched scenario-repetition blocks checked: 500. User prompts identical within matched blocks: PASS.

## 10. Commercial Instructions

Neutral prompts free of commercial information: PASS.

Commercial prompts valid: PASS.

Commercial requests with valid visible partner ID: 1000 / 1000.

Commercial requests with unresolved placeholder: 0.

Commercial visible partner found in catalogue: 1000 / 1000.

Commercial partner mapping correct: 1000 / 1000.

## 11. Agenticity

Agenticity manipulation valid: PASS.

## 12. Schema

Output schema identical across requests and equal to schema file: PASS.

## 13. Experimental Leakage

Experimental leakage detected in user prompts: NO.

## 14. Secret Scan

API secret detected: NO.

## 15. Real Action Scan

Real action possible from batch contents: NO.

## 16. Twenty-Four Prompt Spot Checks

| Scenario | Domain | Rep | Visible partner | Catalog identical | No leakage | Agenticity valid | Commercial partner identified | Mapping correct | Conclusion |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| CON_HOT_001 | hotels | 1 | V174 | True | True | True | True | True | PASS |
| CON_HOT_011 | hotels | 1 | V514 | True | True | True | True | True | PASS |
| CON_SFT_021 | software | 1 | V860 | True | True | True | True | True | PASS |
| CON_SFT_028 | software | 5 | V827 | True | True | True | True | True | PASS |
| CON_ELC_036 | electronics | 1 | V290 | True | True | True | True | True | PASS |
| CON_ELC_043 | electronics | 5 | V492 | True | True | True | True | True | PASS |

## 17. Automated Tests

Existing automated test suite passed: YES.

## 18. Anomalies

- None.

Warnings:

- Model field is the literal placeholder ${OPENAI_MODEL}; materialize it before any real provider submission if the provider does not resolve placeholders.

## 19. Conclusion

Decision: **GO**

The corrected batch passes critical validation and can proceed to final human review before any separately confirmed paid submission.
