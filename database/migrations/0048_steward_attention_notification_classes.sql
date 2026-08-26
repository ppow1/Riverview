-- Migration: 0048
-- Purpose: bounded Steward attention notification classes.

BEGIN;

ALTER TABLE steward_notifications
    DROP CONSTRAINT IF EXISTS steward_notifications_notification_type_check;

ALTER TABLE steward_notifications
    ADD CONSTRAINT steward_notifications_notification_type_check
    CHECK (notification_type IN (
        'steward_checkpoint',
        'critical_failure',
        'important_completion',
        'binding_condition',
        'blocked_requires_steward',
        'ready_for_steward_review'
    ));

COMMIT;
