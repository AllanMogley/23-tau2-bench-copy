-- Hard reset for the Twenty CRM benchmark database.
-- Confirm the table names before running:
--   SELECT tablename FROM pg_tables WHERE schemaname = 'public';
--
-- Twenty's core tables are normally person, company, opportunity and task.
-- Adjust the list if your workspace uses different names.

TRUNCATE TABLE
    task,
    opportunity,
    person,
    company
RESTART IDENTITY CASCADE;

-- If your schema also stores notes, timeline activities or task targets,
-- truncate them as well:
-- TRUNCATE TABLE note, note_target, task_target, timeline_activity
-- RESTART IDENTITY CASCADE;

-- Verify:
-- SELECT COUNT(*) FROM person;
-- SELECT COUNT(*) FROM company;
-- SELECT COUNT(*) FROM opportunity;
-- SELECT COUNT(*) FROM task;
