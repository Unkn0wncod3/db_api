-- Remove all database objects in the correct order to avoid dependency issues

BEGIN;

-- 1) Views 
DROP VIEW IF EXISTS v_person_timeline      CASCADE;
DROP VIEW IF EXISTS v_person_profiles      CASCADE;
DROP VIEW IF EXISTS v_person_summary       CASCADE;

-- 2) Tables
DROP TABLE IF EXISTS community_memberships CASCADE;
DROP TABLE IF EXISTS game_profiles         CASCADE;
DROP TABLE IF EXISTS usages                CASCADE;
DROP TABLE IF EXISTS activities            CASCADE;
DROP TABLE IF EXISTS notes                 CASCADE;
DROP TABLE IF EXISTS person_profile_map    CASCADE;
DROP TABLE IF EXISTS communities           CASCADE;
DROP TABLE IF EXISTS games                 CASCADE;
DROP TABLE IF EXISTS vehicles              CASCADE;
DROP TABLE IF EXISTS profiles              CASCADE;
DROP TABLE IF EXISTS platforms             CASCADE;
DROP TABLE IF EXISTS persons               CASCADE;
DROP TABLE IF EXISTS users                 CASCADE;

-- 3) Trigger
DROP FUNCTION IF EXISTS set_updated_at()   CASCADE;
DROP TYPE IF EXISTS visibility_level_enum  CASCADE;

COMMIT;
