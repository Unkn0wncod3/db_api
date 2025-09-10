-- 0-drop_all.sql — vorhandene Views, Tabellen, Trigger, Funktionen entfernen

BEGIN;

-- 1) Views zuerst
DROP VIEW IF EXISTS v_person_timeline      CASCADE;
DROP VIEW IF EXISTS v_person_profiles      CASCADE;
DROP VIEW IF EXISTS v_person_summary       CASCADE;

-- 2) Tabellen (Reihenfolge beachtet; CASCADE tut's sonst auch)
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

-- 3) Trigger-Funktion(en)
DROP FUNCTION IF EXISTS set_updated_at()   CASCADE;

COMMIT;
