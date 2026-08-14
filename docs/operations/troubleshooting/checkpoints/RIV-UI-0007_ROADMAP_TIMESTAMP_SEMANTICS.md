<!-- Version: 0.7.2 -->
# RIV-UI-0007 - Roadmap timestamp semantics

Component and seam owner: Steward Status roadmap projection and display.

Triggering operation: Viewing the Roadmap table after a master-roadmap synchronization.

Observed failure class: all 103 roadmap rows display the same `roadmap_items.updated_at` timestamp even though the waypoints did not all change state at that time.

Evidence signature:
- `roadmap_items` has 103 rows and one distinct `updated_at` value matching `roadmap_revisions.applied_at`.
- `roadmap_transitions.occurred_at` contains truthful state-change history where recorded.
- older completed rows may have truthful `completed_at` but no transition history.
- pending/active rows with no transition history have no truthful historical status-change timestamp.

Smallest permitted repair:
1. keep `roadmap_items.updated_at` as internal synchronization metadata;
2. project `status_changed_at` as the latest transition time;
3. fall back to `completed_at` only for completed rows without transition history;
4. return NULL where no truthful status-change time exists;
5. render NULL explicitly in Steward Status.

Recovery verification:
- RV-004.1, RV-004.2, and RV-004.3 display their transition times;
- RV-001 through RV-003 fall back to recorded completion time;
- untouched pending waypoints such as RV-004.4 display no fabricated timestamp;
- the dashboard no longer presents master-roadmap publication time as waypoint progress.

Escalation boundary: do not invent timestamps, rewrite transition history, add schema merely for display convenience, or alter roadmap state to repair the UI.

Applicable implementation revision: Steward Status 0.7.1; repair tool 0.7.2.

Validation state: observed; repair acceptance required.