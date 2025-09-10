-- ================================
-- 2-seed_example_data.sql — Beispiel-Daten
-- ================================

-- Plattformen
INSERT INTO platforms (name, category, base_url, api_base_url)
VALUES 
('Discord', 'social', 'https://discord.com', 'https://discord.com/api'),
('Steam',   'gaming', 'https://steamcommunity.com', NULL),
('X',       'social', 'https://x.com', 'https://api.x.com')
ON CONFLICT (LOWER(name)) DO NOTHING;

-- Personen
INSERT INTO persons (
  first_name, last_name, date_of_birth, gender, email, phone_number,
  address_line1, postal_code, city, country, occupation, tags, metadata
)
VALUES
('John',  'Doe',      '1980-05-15', 'Male',        'john.doe@example.com', '+49 123456789',
 'Example Street 1', '10115', 'Berlin', 'Germany', 'Engineer', ARRAY['vip','driver'], '{"pref":{"lang":"de"}}'),
('Alice', 'Example',   NULL,         'Unspecified', 'alice@example.com',     'N/A',
 NULL, NULL, 'Karlsruhe', 'Germany', NULL, ARRAY['beta'], '{}'),
('Bob',   'Meyer',     '1992-11-02', 'Male',        'bob.meyer@example.com', '+49 987654321',
 'Hauptstr. 5', '76131', 'Karlsruhe', 'Germany', 'Student', ARRAY['gamer'], '{}'),
('Clara', 'Nguyen',    '1999-03-22', 'Female',      'clara.nguyen@example.com', 'N/A',
 NULL, NULL, 'Hamburg', 'Germany', 'Analyst', ARRAY['new'], '{}');

-- Profile
-- John: Discord & Steam
INSERT INTO profiles (platform_id, username, external_id, display_name, url, language, region, is_verified, last_seen_at)
SELECT p.id, 'john_d', '1234567890', 'John D', 'https://discord.com/users/1234567890', 'de', 'EU', TRUE, NOW() - INTERVAL '1 day'
FROM platforms p WHERE p.name='Discord';

INSERT INTO profiles (platform_id, username, external_id, display_name, url, language, region, last_seen_at)
SELECT p.id, 'john_steam', 'STEAM_0:1:111111', 'John on Steam', 'https://steamcommunity.com/id/john_steam', 'en', 'EU', NOW() - INTERVAL '3 hours'
FROM platforms p WHERE p.name='Steam';

-- Alice: X
INSERT INTO profiles (platform_id, username, display_name, url, language)
SELECT p.id, 'alice_x', 'Alice', 'https://x.com/alice_x', 'de'
FROM platforms p WHERE p.name='X';

-- Bob: Discord
INSERT INTO profiles (platform_id, username, display_name, url)
SELECT p.id, 'bob_discord', 'Bob M', 'https://discord.com/users/555666777'
FROM platforms p WHERE p.name='Discord';

-- Map: Personen ↔ Profile
INSERT INTO person_profile_map (person_id, profile_id)
SELECT per.id, prof.id
FROM persons per, profiles prof
WHERE per.email='john.doe@example.com' AND prof.username IN ('john_d','john_steam')
ON CONFLICT DO NOTHING;

INSERT INTO person_profile_map (person_id, profile_id)
SELECT per.id, prof.id
FROM persons per, profiles prof
WHERE per.email='alice@example.com' AND prof.username='alice_x'
ON CONFLICT DO NOTHING;

INSERT INTO person_profile_map (person_id, profile_id)
SELECT per.id, prof.id
FROM persons per, profiles prof
WHERE per.email='bob.meyer@example.com' AND prof.username='bob_discord'
ON CONFLICT DO NOTHING;

-- Fahrzeuge
INSERT INTO vehicles (label, make, model, build_year, license_plate, vehicle_type, energy_type, color, mileage_km, last_service_at, metadata)
VALUES
('Car XY', 'VW', 'Golf', 2019, 'B-AB 1234', 'car', 'petrol', 'blue', 45210, NOW() - INTERVAL '5 months', '{}'),
('E-Van 1','Mercedes', 'eVito', 2022, 'KA-EV 2022', 'van', 'electric', 'white', 18350, NOW() - INTERVAL '2 months', '{"battery_kwh":41}')
ON CONFLICT DO NOTHING;

-- Notizen
INSERT INTO notes (person_id, title, text, pinned)
SELECT id, 'Erstkontakt', 'Kennengelernt auf Meetup in Berlin.', TRUE
FROM persons WHERE email='john.doe@example.com';

INSERT INTO notes (person_id, title, text)
SELECT id, 'Follow-up', 'Ruft nächste Woche an.'
FROM persons WHERE email='alice@example.com';

-- Games
INSERT INTO games (name, publisher, genre, release_year)
VALUES
('Counter-Strike 2', 'Valve', 'FPS', 2023),
('Dota 2', 'Valve', 'MOBA', 2013)
ON CONFLICT (LOWER(name)) DO NOTHING;

-- Game Profiles (John spielt CS2)
INSERT INTO game_profiles (profile_id, game_id, in_game_name, level, rank, hours_played)
SELECT prof.id, g.id, 'johnCS', 27, 'Gold Nova', 240
FROM profiles prof, games g
WHERE prof.username='john_steam' AND g.name='Counter-Strike 2'
ON CONFLICT DO NOTHING;

-- Communities
INSERT INTO communities (platform_id, name, external_id, url, type, member_count)
SELECT p.id, 'My Discord Server', '9876543210', 'https://discord.gg/example', 'guild', 1200
FROM platforms p WHERE p.name='Discord'
ON CONFLICT DO NOTHING;

-- Memberships
INSERT INTO community_memberships (profile_id, community_id, role, nickname)
SELECT prof.id, comm.id, 'member', 'JD'
FROM profiles prof, communities comm
WHERE prof.username='john_d' AND comm.name='My Discord Server'
ON CONFLICT DO NOTHING;

INSERT INTO community_memberships (profile_id, community_id, role)
SELECT prof.id, comm.id, 'mod'
FROM profiles prof, communities comm
WHERE prof.username='bob_discord' AND comm.name='My Discord Server'
ON CONFLICT DO NOTHING;

-- Usages (Beispielverwendungen)
INSERT INTO usages (person_id, item, usage_date, notes, duration_min, location, cost_amount)
SELECT per.id, 'Car XY', CURRENT_DATE, 'Kurzstrecke', 25, 'Berlin', 7.50
FROM persons per WHERE per.email='john.doe@example.com';

INSERT INTO usages (person_id, item, usage_date, notes, duration_min, location)
SELECT per.id, 'E-Van 1', CURRENT_DATE - INTERVAL '1 day', 'Lieferung Innenstadt', 90, 'Karlsruhe'
FROM persons per WHERE per.email='bob.meyer@example.com';

-- Aktivitäten
-- 1) John fährt Car XY
INSERT INTO activities (person_id, activity_type, vehicle_id, item, notes, details, severity, source, geo_location, ip_address, user_agent, created_by)
SELECT per.id, 'drive', v.id, v.label, 'Testfahrt',
       jsonb_build_object('distance_km', 12.3, 'duration_min', 25),
       'info','manual','Berlin, DE','203.0.113.10','Chrome/Windows','system'
FROM persons per, vehicles v
WHERE per.email='john.doe@example.com' AND v.label='Car XY';

-- 2) John joint Discord-Server
INSERT INTO activities (person_id, activity_type, profile_id, community_id, notes, details, source)
SELECT per.id, 'join_community', prof.id, comm.id, 'Joined via invite',
       jsonb_build_object('invite_code', 'abcd1234'),
       'api'
FROM persons per, profiles prof, communities comm
WHERE per.email='john.doe@example.com' AND prof.username='john_d' AND comm.name='My Discord Server';

-- 3) John Steam Login
INSERT INTO activities (person_id, activity_type, profile_id, notes, details, ip_address, user_agent, source)
SELECT per.id, 'login', prof.id, 'Login from DE',
       jsonb_build_object('ip', '203.0.113.10', 'ua', 'Chrome/Windows'),
       '203.0.113.10', 'Chrome/Windows', 'manual'
FROM persons per, profiles prof
WHERE per.email='john.doe@example.com' AND prof.username='john_steam';

-- 4) Freies Item-Event (Upload)
INSERT INTO activities (person_id, activity_type, item, notes, details, severity, source)
SELECT per.id, 'custom', 'Uploaded PDF Document', 'Manual upload',
       jsonb_build_object('file_id', 'doc_001', 'size_kb', 842),
       'info', 'manual'
FROM persons per WHERE per.email='john.doe@example.com';

-- 5) Bob postet auf Discord
INSERT INTO activities (person_id, activity_type, profile_id, item, notes, details, source, geo_location)
SELECT per.id, 'post', prof.id, '#general', 'Willkommenspost',
       jsonb_build_object('message_id','m_1001','length',120),
       'api','Karlsruhe, DE'
FROM persons per, profiles prof
WHERE per.email='bob.meyer@example.com' AND prof.username='bob_discord';

-- 6) Alice X-Post
INSERT INTO activities (person_id, activity_type, profile_id, item, details, source)
SELECT per.id, 'post', prof.id, '@alice_x',
       jsonb_build_object('tweet_id','t_42','likes',10,'retweets',2),
       'api'
FROM persons per, profiles prof
WHERE per.email='alice@example.com' AND prof.username='alice_x';
