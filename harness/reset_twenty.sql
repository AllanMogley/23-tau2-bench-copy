-- Hard reset for the Twenty CRM benchmark database.
-- SAFETY: never TRUNCATE ... CASCADE here. CASCADE follows foreign keys into
-- unrelated tables and can wipe workspace/user/auth rows on a shared instance.
-- Only DELETE rows from the CRM object tables below; the core schema
-- (workspace, user, workspaceMember, keyValue, metadata) is never touched.

-- Optional: scope to one workspace by adding
--   WHERE "workspaceId" = '<uuid>'
-- to each delete. Unscoped is only safe on a dedicated benchmark instance.

DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'taskTarget',
        'noteTarget',
        'timelineActivity',
        'favorite',
        'attachment',
        'note',
        'task',
        'opportunity',
        'person',
        'company'
    ] LOOP
        IF to_regclass(format('public.%I', t)) IS NOT NULL THEN
            EXECUTE format('DELETE FROM public.%I', t);
        END IF;
    END LOOP;
END $$;

-- Verify the CRM objects are empty:
-- SELECT COUNT(*) FROM person;
-- SELECT COUNT(*) FROM company;
-- SELECT COUNT(*) FROM opportunity;
-- SELECT COUNT(*) FROM task;
--
-- Verify login data is intact:
-- SELECT COUNT(*) FROM core.workspace;
-- SELECT COUNT(*) FROM core."user";
