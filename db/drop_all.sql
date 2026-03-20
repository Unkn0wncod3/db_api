-- Remove all database objects in the correct order to avoid dependency issues

BEGIN;

-- 1) Views 
DROP TABLE IF EXISTS attachments          CASCADE;
DROP TABLE IF EXISTS entry_permissions    CASCADE;
DROP TABLE IF EXISTS entry_history        CASCADE;
DROP TABLE IF EXISTS entry_relations      CASCADE;
DROP TABLE IF EXISTS entries              CASCADE;
DROP TABLE IF EXISTS fields               CASCADE;
DROP TABLE IF EXISTS schemas              CASCADE;
DROP TABLE IF EXISTS users                CASCADE;

-- 3) Trigger
DROP FUNCTION IF EXISTS set_updated_at()   CASCADE;
DROP TYPE IF EXISTS entry_permission_enum  CASCADE;
DROP TYPE IF EXISTS permission_subject_type_enum CASCADE;
DROP TYPE IF EXISTS field_data_type_enum   CASCADE;
DROP TYPE IF EXISTS visibility_level_enum  CASCADE;
COMMIT;
