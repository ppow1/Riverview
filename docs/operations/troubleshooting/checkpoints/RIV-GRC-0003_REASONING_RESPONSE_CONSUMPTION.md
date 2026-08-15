<!-- Version: 0.1.0 -->
# RIV-GRC-0003 - Grace reasoning-response consumption

Owner: Riverview Grace response consumer and PostgreSQL objective model.

## SYMPTOM

A completed mailbox response cannot be consumed, is already consumed, has a
request/correlation mismatch, lacks evidence, or does not advance the declared
acceptance objective.

## LIKELY BOUNDARY

The durable mailbox response, correlation identity, authorized producer,
response schema, Grace consumption record, or declared objective/stage.

## SAFE DIAGNOSTIC

Inspect only bounded metadata in `mailbox_responses`,
`grace_response_consumptions`, `objectives`, `objective_stages`, and River
events by `response_id` and `correlation_id`. Do not read arbitrary SQL or
conversation contents.

## EXPECTED HEALTHY RESULT

One consumption row exists for the response, with one `grace.response.consumed`
event, one `grace.response.evaluated` event, and—only for
`advisory_accepted`—one bounded objective advancement.

## KNOWN FAILURE RESULT

- `RIV-GRC-0003`: missing response/objective/stage, invalid correlation,
  unauthorized producer, incompatible schema, missing evidence, or ineligible
  objective stage.
- Replaying the same response returns the original consumption identity and
  creates no duplicate logical consumption or objective progression.

## REPAIR

Restore only the missing bounded state or declared objective/stage. Do not
rewrite mailbox history, fabricate response evidence, or turn advisory text
into a work order.

## VERIFY

Run the response-consumption contract tests, replay the same response, and
verify one consumption row and one River lineage by `response_id`.

## DO NOT

Do not implement Steward seed submission, momentum evaluation, provider
dispatch, arbitrary work creation, roadmap mutation, shell, filesystem, SQL,
Undercurrent, or conversation-text authority here.

## EVIDENCE

PostgreSQL `mailbox_responses`, `grace_response_consumptions`, objective tables,
and River events are authoritative. Response payloads remain bounded advisory
data.
