# Metadata type fix report

## Cause

The first Batch `batch_6a42bee0c3a88190b6f498efbdba3d00` failed with 0 successful responses and 2000 errors.

Root cause: Invalid type for 'metadata.expected_action_prepared': expected a string, but got a boolean instead.

The protocol, locked scenarios, locked run plan, prompts, custom IDs, model, endpoint and output schema were not changed.

## Correction

Only `body.metadata` values were normalized for API submission. Boolean values are now serialized as strings (`true` / `false`), numeric values as stable text, strings are kept unchanged, and `None` values are omitted.

Converted metadata values: 6000

Converted fields: expected_action_prepared=2000, expected_confirmation_required=2000, simulation_only=2000

Metadata fields checked: condition, expected_action_level, expected_action_prepared, expected_confirmation_required, observation_key, repetition, scenario_id, simulation_only

No API call was sent. No Batch was submitted.
