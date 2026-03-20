BEGIN;

-- ============================================================
-- Seed reset for metadata demo data
-- ============================================================

DELETE FROM entry_permissions
WHERE entry_id IN (
    SELECT e.id
    FROM entries e
    JOIN schemas s ON s.id = e.schema_id
    WHERE s.key IN ('person', 'todo', 'vehicle', 'case_file', 'organization')
);

DELETE FROM attachments
WHERE entry_id IN (
    SELECT e.id
    FROM entries e
    JOIN schemas s ON s.id = e.schema_id
    WHERE s.key IN ('person', 'todo', 'vehicle', 'case_file', 'organization')
);

DELETE FROM entry_history
WHERE entry_id IN (
    SELECT e.id
    FROM entries e
    JOIN schemas s ON s.id = e.schema_id
    WHERE s.key IN ('person', 'todo', 'vehicle', 'case_file', 'organization')
);

DELETE FROM entry_relations
WHERE from_entry_id IN (
        SELECT e.id
        FROM entries e
        JOIN schemas s ON s.id = e.schema_id
        WHERE s.key IN ('person', 'todo', 'vehicle', 'case_file', 'organization')
    )
   OR to_entry_id IN (
        SELECT e.id
        FROM entries e
        JOIN schemas s ON s.id = e.schema_id
        WHERE s.key IN ('person', 'todo', 'vehicle', 'case_file', 'organization')
    );

DELETE FROM entries
WHERE schema_id IN (
    SELECT id
    FROM schemas
    WHERE key IN ('person', 'todo', 'vehicle', 'case_file', 'organization')
);

DELETE FROM fields
WHERE schema_id IN (
    SELECT id
    FROM schemas
    WHERE key IN ('person', 'todo', 'vehicle', 'case_file', 'organization')
);

DELETE FROM schemas
WHERE key IN ('person', 'todo', 'vehicle', 'case_file', 'organization');

DELETE FROM users
WHERE username IN ('seed_head_admin', 'seed_admin', 'seed_manager', 'seed_editor', 'seed_reader');


-- ============================================================
-- Users
-- Passwords:
-- HeadAdmin123!
-- Admin123!
-- Manager123!
-- Editor123!
-- Reader123!
-- ============================================================

INSERT INTO users (username, password_hash, role, is_active, profile_picture_url, preferences)
VALUES
(
    'seed_head_admin',
    'QGQJ67MPgBDCI1-jsB5OZXzW9d1GSzopMyqXCbjd5VQTK81X4eywi8774D7odm_F',
    'head_admin',
    TRUE,
    'https://images.example.com/users/head-admin.png',
    '{"theme":"dark","dashboard":"executive"}'::jsonb
),
(
    'seed_admin',
    'n-7Qgxu3r5Zi9pVHwrza6NaHHMSe7WBdEgqoVNWAE6dmqqmq2Z0H7srX4iKslxYk',
    'admin',
    TRUE,
    'https://images.example.com/users/admin.png',
    '{"theme":"light","dashboard":"admin"}'::jsonb
),
(
    'seed_manager',
    'CcofVXDiShpNs_Vs8nTbn-MemZ-4_9AC_V9oodUz5S3FOw1Q8OsvsaWxUR4Z9F7r',
    'manager',
    TRUE,
    'https://images.example.com/users/manager.png',
    '{"team":"operations","locale":"de-DE"}'::jsonb
),
(
    'seed_editor',
    'SpZ1EwVnkXFR9mLu9OgDC-m8TbU_fnm8dT9Oe0K1MSbRm7mdssCrkqnoy_we5Hhh',
    'editor',
    TRUE,
    'https://images.example.com/users/editor.png',
    '{"team":"analysis","locale":"en-US"}'::jsonb
),
(
    'seed_reader',
    'HkNHemQIESWv9-QKTosa0rsUvnwDZ__Gz1X46oV0EUH-SOE5WONP27yBzIKilmAn',
    'reader',
    TRUE,
    'https://images.example.com/users/reader.png',
    '{"team":"stakeholder","digest":true}'::jsonb
);


-- ============================================================
-- Schemas
-- ============================================================

INSERT INTO schemas (key, name, description, icon, is_active)
VALUES
('person', 'Person', 'Dynamic person records used for case work and CRM-style capture.', 'user-round', TRUE),
('organization', 'Organization', 'Companies, agencies and other legal entities.', 'building-2', TRUE),
('todo', 'Task', 'Actionable work items with due dates and assignees.', 'check-square', TRUE),
('vehicle', 'Vehicle', 'Tracked vehicles with lifecycle and registration metadata.', 'car-front', TRUE),
('case_file', 'Case File', 'Investigation or dossier container with references to entities.', 'folder-lock', TRUE);


-- ============================================================
-- Fields
-- ============================================================

INSERT INTO fields (
    schema_id, key, label, description, data_type, is_required, is_unique,
    default_value, sort_order, is_active, validation_json, settings_json
)
SELECT s.id, v.key, v.label, v.description, v.data_type::field_data_type_enum, v.is_required, v.is_unique,
       v.default_value::jsonb, v.sort_order, TRUE, v.validation_json::jsonb, v.settings_json::jsonb
FROM schemas s
JOIN (
    VALUES
    ('person', 'first_name', 'First Name', 'Stable given name key.', 'text', TRUE, FALSE, NULL, 10, '{"min_length":1,"max_length":100}', '{}'),
    ('person', 'last_name', 'Last Name', 'Stable family name key.', 'text', TRUE, FALSE, NULL, 20, '{"min_length":1,"max_length":100}', '{}'),
    ('person', 'email', 'Email', 'Primary email address.', 'email', FALSE, TRUE, NULL, 30, '{"max_length":255,"allow_null":true}', '{}'),
    ('person', 'phone', 'Phone', 'Primary phone number.', 'text', FALSE, FALSE, NULL, 40, '{"max_length":50,"allow_null":true}', '{}'),
    ('person', 'birth_date', 'Birth Date', 'Date of birth.', 'date', FALSE, FALSE, NULL, 50, '{"allow_null":true}', '{}'),
    ('person', 'risk_level', 'Risk Level', 'Operational assessment.', 'select', FALSE, FALSE, '"medium"', 60, '{"options":["low","medium","high"]}', '{}'),
    ('person', 'tags', 'Tags', 'Multi-tag classification.', 'multi_select', FALSE, FALSE, '[]', 70, '{"options":["vip","internal","watchlist","supplier","prospect"]}', '{}'),
    ('person', 'notes', 'Notes', 'Long form notes.', 'long_text', FALSE, FALSE, NULL, 80, '{"allow_null":true}', '{}'),
    ('person', 'primary_org_id', 'Primary Organization', 'Reference to organization entry.', 'reference', FALSE, FALSE, NULL, 90, '{"allow_null":true}', '{}'),

    ('organization', 'legal_name', 'Legal Name', 'Registered legal entity name.', 'text', TRUE, TRUE, NULL, 10, '{"min_length":2,"max_length":200}', '{}'),
    ('organization', 'org_type', 'Organization Type', 'Classification of the organization.', 'select', TRUE, FALSE, '"company"', 20, '{"options":["company","agency","ngo","vendor"]}', '{}'),
    ('organization', 'website', 'Website', 'Public website.', 'url', FALSE, FALSE, NULL, 30, '{"allow_null":true}', '{}'),
    ('organization', 'country', 'Country', 'Main country.', 'text', FALSE, FALSE, NULL, 40, '{"max_length":80,"allow_null":true}', '{}'),
    ('organization', 'industry', 'Industry', 'Industry vertical.', 'text', FALSE, FALSE, NULL, 50, '{"max_length":120,"allow_null":true}', '{}'),

    ('todo', 'summary', 'Summary', 'Task summary.', 'text', TRUE, FALSE, NULL, 10, '{"min_length":3,"max_length":200}', '{}'),
    ('todo', 'description', 'Description', 'Task details.', 'long_text', FALSE, FALSE, NULL, 20, '{"allow_null":true}', '{}'),
    ('todo', 'priority', 'Priority', 'Priority bucket.', 'select', TRUE, FALSE, '"medium"', 30, '{"options":["low","medium","high","critical"]}', '{}'),
    ('todo', 'due_at', 'Due At', 'Due date and time.', 'datetime', FALSE, FALSE, NULL, 40, '{"allow_null":true}', '{}'),
    ('todo', 'effort_hours', 'Effort Hours', 'Estimated effort.', 'decimal', FALSE, FALSE, '"2.5"', 50, '{"min":0,"max":200}', '{}'),
    ('todo', 'assignee_user_id', 'Assignee User ID', 'Assigned system user id.', 'integer', FALSE, FALSE, NULL, 60, '{"allow_null":true,"min":1}', '{}'),
    ('todo', 'related_case_id', 'Related Case', 'Reference to case file.', 'reference', FALSE, FALSE, NULL, 70, '{"allow_null":true}', '{}'),
    ('todo', 'blocked', 'Blocked', 'Whether the task is blocked.', 'boolean', FALSE, FALSE, 'false', 80, '{}', '{}'),

    ('vehicle', 'make', 'Make', 'Manufacturer.', 'text', TRUE, FALSE, NULL, 10, '{"min_length":1,"max_length":80}', '{}'),
    ('vehicle', 'model', 'Model', 'Vehicle model.', 'text', TRUE, FALSE, NULL, 20, '{"min_length":1,"max_length":80}', '{}'),
    ('vehicle', 'license_plate', 'License Plate', 'Registration plate.', 'text', FALSE, TRUE, NULL, 30, '{"max_length":20,"allow_null":true}', '{}'),
    ('vehicle', 'build_year', 'Build Year', 'Production year.', 'integer', FALSE, FALSE, NULL, 40, '{"min":1950,"max":2035,"allow_null":true}', '{}'),
    ('vehicle', 'energy_type', 'Energy Type', 'Fuel or power source.', 'select', FALSE, FALSE, '"petrol"', 50, '{"options":["petrol","diesel","electric","hybrid"]}', '{}'),
    ('vehicle', 'owner_person_id', 'Owner Person', 'Reference to person owner.', 'reference', FALSE, FALSE, NULL, 60, '{"allow_null":true}', '{}'),
    ('vehicle', 'metadata', 'Metadata', 'Unstructured metadata block.', 'json', FALSE, FALSE, '{}', 70, '{}', '{}'),

    ('case_file', 'case_number', 'Case Number', 'Stable technical case number.', 'text', TRUE, TRUE, NULL, 10, '{"regex":"^[A-Z]{2,5}-[0-9]{4}-[0-9]{3}$"}', '{}'),
    ('case_file', 'summary', 'Summary', 'Case summary.', 'text', TRUE, FALSE, NULL, 20, '{"min_length":5,"max_length":200}', '{}'),
    ('case_file', 'case_type', 'Case Type', 'Type of case.', 'select', TRUE, FALSE, '"investigation"', 30, '{"options":["investigation","incident","compliance","customer"]}', '{}'),
    ('case_file', 'opened_on', 'Opened On', 'Case opening date.', 'date', TRUE, FALSE, NULL, 40, '{}', '{}'),
    ('case_file', 'budget', 'Budget', 'Budget in EUR.', 'decimal', FALSE, FALSE, '"0"', 50, '{"min":0,"max":1000000}', '{}'),
    ('case_file', 'sensitive', 'Sensitive', 'Sensitive case flag.', 'boolean', FALSE, FALSE, 'true', 60, '{}', '{}'),
    ('case_file', 'attachment_ids', 'Attachment IDs', 'Related attachment ids.', 'file', FALSE, FALSE, '[]', 70, '{"allow_null":true}', '{"multiple":true}')
) AS v(schema_key, key, label, description, data_type, is_required, is_unique, default_value, sort_order, validation_json, settings_json)
    ON v.schema_key = s.key;


-- ============================================================
-- Entries
-- ============================================================

INSERT INTO entries (schema_id, title, status, visibility_level, owner_id, created_by, data_json)
SELECT
    s.id,
    x.title,
    x.status,
    x.visibility_level::visibility_level_enum,
    owner_u.id,
    creator_u.id,
    x.data_json::jsonb
FROM schemas s
JOIN (
    VALUES
    (
        'organization',
        'Acme Logistics GmbH',
        'active',
        'internal',
        'seed_manager',
        'seed_head_admin',
        '{"legal_name":"Acme Logistics GmbH","org_type":"company","website":"https://acme-logistics.example.com","country":"Germany","industry":"Logistics"}'
    ),
    (
        'organization',
        'Northwind Investigations',
        'active',
        'restricted',
        'seed_admin',
        'seed_head_admin',
        '{"legal_name":"Northwind Investigations","org_type":"agency","website":"https://northwind.example.com","country":"Germany","industry":"Security"}'
    ),
    (
        'person',
        'Ada Lovelace',
        'active',
        'restricted',
        'seed_editor',
        'seed_manager',
        '{"first_name":"Ada","last_name":"Lovelace","email":"ada@example.com","phone":"+49-30-555-0101","birth_date":"1815-12-10","risk_level":"low","tags":["vip","prospect"],"notes":"Initial stakeholder and public speaker contact."}'
    ),
    (
        'person',
        'Grace Hopper',
        'active',
        'internal',
        'seed_manager',
        'seed_manager',
        '{"first_name":"Grace","last_name":"Hopper","email":"grace@example.com","phone":"+1-202-555-0112","birth_date":"1906-12-09","risk_level":"medium","tags":["internal"],"notes":"Strong domain expert and historical advisor."}'
    ),
    (
        'person',
        'Linus Torvalds',
        'review',
        'public',
        'seed_reader',
        'seed_editor',
        '{"first_name":"Linus","last_name":"Torvalds","email":"linus@example.com","phone":"+358-555-0199","birth_date":"1969-12-28","risk_level":"low","tags":["supplier"],"notes":"Open-source ambassador profile."}'
    ),
    (
        'vehicle',
        'Mercedes Sprinter KA-LX-204',
        'active',
        'internal',
        'seed_manager',
        'seed_manager',
        '{"make":"Mercedes","model":"Sprinter","license_plate":"KA-LX-204","build_year":2022,"energy_type":"diesel","metadata":{"fleet":"west","gps_enabled":true}}'
    ),
    (
        'vehicle',
        'Tesla Model Y B-EV-900',
        'active',
        'restricted',
        'seed_editor',
        'seed_admin',
        '{"make":"Tesla","model":"Model Y","license_plate":"B-EV-900","build_year":2024,"energy_type":"electric","metadata":{"fleet":"executive","gps_enabled":true}}'
    ),
    (
        'case_file',
        'Case CF-2026-001',
        'open',
        'restricted',
        'seed_manager',
        'seed_head_admin',
        '{"case_number":"CF-2026-001","summary":"Supplier due diligence for Acme Logistics.","case_type":"compliance","opened_on":"2026-01-15","budget":"15000","sensitive":true,"attachment_ids":[]}'
    ),
    (
        'case_file',
        'Case OPS-2026-002',
        'open',
        'internal',
        'seed_admin',
        'seed_admin',
        '{"case_number":"OPS-2026-002","summary":"Vehicle incident triage for regional fleet.","case_type":"incident","opened_on":"2026-02-02","budget":"4200","sensitive":false,"attachment_ids":[]}'
    ),
    (
        'todo',
        'Task Review Acme KYC',
        'open',
        'restricted',
        'seed_editor',
        'seed_manager',
        '{"summary":"Review Acme KYC package","description":"Validate registration documents and beneficial ownership.","priority":"high","due_at":"2026-03-28T12:00:00+00:00","effort_hours":"4.5","blocked":false}'
    ),
    (
        'todo',
        'Task Schedule Fleet Inspection',
        'open',
        'internal',
        'seed_manager',
        'seed_admin',
        '{"summary":"Schedule vehicle inspection","description":"Coordinate annual inspection for diesel fleet.","priority":"medium","due_at":"2026-04-05T08:30:00+00:00","effort_hours":"2.0","blocked":true}'
    ),
    (
        'todo',
        'Task Prepare Executive Summary',
        'draft',
        'private',
        'seed_head_admin',
        'seed_head_admin',
        '{"summary":"Prepare executive summary","description":"Draft summary for board meeting.","priority":"critical","due_at":"2026-03-25T09:00:00+00:00","effort_hours":"3.0","blocked":false}'
    )
) AS x(schema_key, title, status, visibility_level, owner_username, created_by_username, data_json)
    ON x.schema_key = s.key
JOIN users owner_u ON owner_u.username = x.owner_username
JOIN users creator_u ON creator_u.username = x.created_by_username;


-- ============================================================
-- Post-insert reference updates inside data_json
-- ============================================================

UPDATE entries person_entry
SET data_json = jsonb_set(
    person_entry.data_json,
    '{primary_org_id}',
    to_jsonb(org_entry.id),
    TRUE
)
FROM entries org_entry
JOIN schemas org_schema ON org_schema.id = org_entry.schema_id,
schemas person_schema
WHERE person_schema.key = 'person'
  AND person_schema.id = person_entry.schema_id
  AND org_schema.key = 'organization'
  AND person_entry.title IN ('Ada Lovelace', 'Grace Hopper')
  AND org_entry.title = 'Acme Logistics GmbH';

UPDATE entries vehicle_entry
SET data_json = jsonb_set(
    vehicle_entry.data_json,
    '{owner_person_id}',
    to_jsonb(person_entry.id),
    TRUE
)
FROM entries person_entry
JOIN schemas person_schema ON person_schema.id = person_entry.schema_id,
schemas vehicle_schema
WHERE vehicle_schema.key = 'vehicle'
  AND vehicle_schema.id = vehicle_entry.schema_id
  AND person_schema.key = 'person'
  AND (
      (vehicle_entry.title = 'Mercedes Sprinter KA-LX-204' AND person_entry.title = 'Grace Hopper')
      OR
      (vehicle_entry.title = 'Tesla Model Y B-EV-900' AND person_entry.title = 'Ada Lovelace')
  );

UPDATE entries todo_entry
SET data_json = jsonb_set(
    todo_entry.data_json,
    '{related_case_id}',
    to_jsonb(case_entry.id),
    TRUE
)
FROM entries case_entry
JOIN schemas case_schema ON case_schema.id = case_entry.schema_id,
schemas todo_schema
WHERE todo_schema.key = 'todo'
  AND todo_schema.id = todo_entry.schema_id
  AND case_schema.key = 'case_file'
  AND (
      (todo_entry.title = 'Task Review Acme KYC' AND case_entry.title = 'Case CF-2026-001')
      OR
      (todo_entry.title = 'Task Schedule Fleet Inspection' AND case_entry.title = 'Case OPS-2026-002')
      OR
      (todo_entry.title = 'Task Prepare Executive Summary' AND case_entry.title = 'Case CF-2026-001')
  );

UPDATE entries todo_entry
SET data_json = jsonb_set(
    todo_entry.data_json,
    '{assignee_user_id}',
    to_jsonb(assignee.id),
    TRUE
)
FROM users assignee
,
schemas todo_schema
WHERE todo_schema.key = 'todo'
  AND todo_schema.id = todo_entry.schema_id
  AND (
      (todo_entry.title = 'Task Review Acme KYC' AND assignee.username = 'seed_editor')
      OR
      (todo_entry.title = 'Task Schedule Fleet Inspection' AND assignee.username = 'seed_manager')
      OR
      (todo_entry.title = 'Task Prepare Executive Summary' AND assignee.username = 'seed_head_admin')
  );


-- ============================================================
-- Attachments
-- ============================================================

INSERT INTO attachments (entry_id, file_name, stored_path, mime_type, file_size, checksum, uploaded_by, description)
SELECT e.id, a.file_name, a.stored_path, a.mime_type, a.file_size, a.checksum, u.id, a.description
FROM entries e
JOIN schemas s ON s.id = e.schema_id
JOIN (
    VALUES
    (
        'Case CF-2026-001',
        'acme_registry_extract.pdf',
        'https://drive.google.com/file/d/acme-registry-extract/view',
        'application/pdf',
        324881,
        'seed-case-cf-2026-001-registry',
        'seed_manager',
        'Official registry export for Acme Logistics.'
    ),
    (
        'Case CF-2026-001',
        'supplier_risk_matrix.xlsx',
        'https://docs.google.com/spreadsheets/d/acme-risk-matrix/edit',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        91422,
        'seed-case-cf-2026-001-risk-matrix',
        'seed_editor',
        'Risk scoring workbook.'
    ),
    (
        'Case OPS-2026-002',
        'fleet_incident_photos.zip',
        'https://drive.google.com/file/d/fleet-incident-photos/view',
        'application/zip',
        4871202,
        'seed-case-ops-2026-002-photos',
        'seed_admin',
        'Compressed incident photo archive.'
    ),
    (
        'Ada Lovelace',
        'speaker_profile.pdf',
        'https://drive.google.com/file/d/ada-speaker-profile/view',
        'application/pdf',
        120531,
        'seed-person-ada-profile',
        'seed_editor',
        'External speaker profile.'
    )
) AS a(entry_title, file_name, stored_path, mime_type, file_size, checksum, uploaded_by_username, description)
    ON a.entry_title = e.title
JOIN users u ON u.username = a.uploaded_by_username
WHERE s.key IN ('case_file', 'person');

UPDATE entries case_entry
SET data_json = jsonb_set(
    case_entry.data_json,
    '{attachment_ids}',
    COALESCE((
        SELECT to_jsonb(array_agg(att.id ORDER BY att.id))
        FROM attachments att
        WHERE att.entry_id = case_entry.id
    ), '[]'::jsonb),
    TRUE
)
FROM schemas s
WHERE s.id = case_entry.schema_id
  AND s.key = 'case_file';


-- ============================================================
-- Entry relations
-- ============================================================

INSERT INTO entry_relations (from_entry_id, to_entry_id, relation_type, sort_order, metadata_json)
SELECT from_entry.id, to_entry.id, rel.relation_type, rel.sort_order, rel.metadata_json::jsonb
FROM (
    VALUES
    ('Case CF-2026-001', 'Ada Lovelace', 'contains', 10, '{"reason":"Primary contact"}'),
    ('Case CF-2026-001', 'Acme Logistics GmbH', 'references', 20, '{"reason":"Target organization"}'),
    ('Case CF-2026-001', 'Task Review Acme KYC', 'contains', 30, '{"reason":"Open action"}'),
    ('Case OPS-2026-002', 'Mercedes Sprinter KA-LX-204', 'contains', 10, '{"reason":"Affected vehicle"}'),
    ('Case OPS-2026-002', 'Task Schedule Fleet Inspection', 'contains', 20, '{"reason":"Follow-up action"}'),
    ('Ada Lovelace', 'Acme Logistics GmbH', 'assigned_to', 10, '{"reason":"External liaison"}'),
    ('Grace Hopper', 'Mercedes Sprinter KA-LX-204', 'related_to', 10, '{"reason":"Vehicle oversight"}'),
    ('Task Prepare Executive Summary', 'Case CF-2026-001', 'belongs_to', 10, '{"reason":"Board reporting"}')
) AS rel(from_title, to_title, relation_type, sort_order, metadata_json)
JOIN entries from_entry ON from_entry.title = rel.from_title
JOIN entries to_entry ON to_entry.title = rel.to_title;


-- ============================================================
-- Entry permissions
-- ============================================================

INSERT INTO entry_permissions (entry_id, subject_type, subject_id, permission, created_by)
SELECT
    e.id,
    p.subject_type::permission_subject_type_enum,
    COALESCE(target_user.id::text, p.subject_id),
    p.permission::entry_permission_enum,
    creator.id
FROM entries e
JOIN (
    VALUES
    ('Case CF-2026-001', 'role', 'manager', 'manage', 'seed_head_admin'),
    ('Case CF-2026-001', 'role', 'editor', 'view_history', 'seed_head_admin'),
    ('Case CF-2026-001', 'user', 'seed_reader', 'read', 'seed_head_admin'),
    ('Case OPS-2026-002', 'role', 'editor', 'manage_attachments', 'seed_admin'),
    ('Case OPS-2026-002', 'role', 'reader', 'read', 'seed_admin'),
    ('Task Review Acme KYC', 'user', 'seed_editor', 'edit', 'seed_manager'),
    ('Task Review Acme KYC', 'role', 'manager', 'manage_permissions', 'seed_manager'),
    ('Ada Lovelace', 'role', 'reader', 'read', 'seed_manager'),
    ('Ada Lovelace', 'role', 'editor', 'manage_attachments', 'seed_manager'),
    ('Mercedes Sprinter KA-LX-204', 'group', 'fleet_ops', 'manage_relations', 'seed_admin')
) AS p(entry_title, subject_type, subject_id, permission, created_by_username)
    ON e.title = p.entry_title
JOIN users creator ON creator.username = p.created_by_username
LEFT JOIN users target_user
    ON p.subject_type = 'user'
   AND target_user.username = p.subject_id;


-- ============================================================
-- Entry history
-- ============================================================

INSERT INTO entry_history (
    entry_id, changed_by, change_type, old_data_json, new_data_json,
    old_visibility_level, new_visibility_level, changed_at, comment
)
SELECT
    e.id,
    u.id,
    h.change_type,
    h.old_data_json::jsonb,
    h.new_data_json::jsonb,
    h.old_visibility_level::visibility_level_enum,
    h.new_visibility_level::visibility_level_enum,
    h.changed_at,
    h.comment
FROM entries e
JOIN (
    VALUES
    (
        'Ada Lovelace',
        'seed_manager',
        'created',
        NULL,
        '{"first_name":"Ada","last_name":"Lovelace","email":"ada@example.com","phone":"+49-30-555-0101","birth_date":"1815-12-10","risk_level":"low","tags":["vip","prospect"],"notes":"Initial stakeholder and public speaker contact."}',
        NULL,
        'restricted',
        NOW() - INTERVAL '12 days',
        'Initial profile import.'
    ),
    (
        'Ada Lovelace',
        'seed_editor',
        'updated',
        '{"first_name":"Ada","last_name":"Lovelace","email":"ada@example.com","phone":"+49-30-555-0101","birth_date":"1815-12-10","risk_level":"medium","tags":["vip"],"notes":"Initial stakeholder and public speaker contact."}',
        '{"first_name":"Ada","last_name":"Lovelace","email":"ada@example.com","phone":"+49-30-555-0101","birth_date":"1815-12-10","risk_level":"low","tags":["vip","prospect"],"notes":"Initial stakeholder and public speaker contact."}',
        'restricted',
        'restricted',
        NOW() - INTERVAL '4 days',
        'Adjusted risk level and tags after review.'
    ),
    (
        'Case CF-2026-001',
        'seed_head_admin',
        'created',
        NULL,
        '{"case_number":"CF-2026-001","summary":"Supplier due diligence for Acme Logistics.","case_type":"compliance","opened_on":"2026-01-15","budget":"15000","sensitive":true}',
        NULL,
        'restricted',
        NOW() - INTERVAL '20 days',
        'Case opened by leadership.'
    ),
    (
        'Case OPS-2026-002',
        'seed_admin',
        'visibility_changed',
        '{"case_number":"OPS-2026-002","summary":"Vehicle incident triage for regional fleet.","case_type":"incident","opened_on":"2026-02-02","budget":"4200","sensitive":false}',
        '{"case_number":"OPS-2026-002","summary":"Vehicle incident triage for regional fleet.","case_type":"incident","opened_on":"2026-02-02","budget":"4200","sensitive":false}',
        'private',
        'internal',
        NOW() - INTERVAL '7 days',
        'Visibility relaxed for regional ops access.'
    ),
    (
        'Task Review Acme KYC',
        'seed_manager',
        'status_changed',
        '{"summary":"Review Acme KYC package","description":"Validate registration documents and beneficial ownership.","priority":"high","due_at":"2026-03-28T12:00:00+00:00","effort_hours":"4.5","blocked":true}',
        '{"summary":"Review Acme KYC package","description":"Validate registration documents and beneficial ownership.","priority":"high","due_at":"2026-03-28T12:00:00+00:00","effort_hours":"4.5","blocked":false}',
        'restricted',
        'restricted',
        NOW() - INTERVAL '1 day',
        'Dependency resolved after receiving registry extract.'
    )
) AS h(
    entry_title, changed_by_username, change_type, old_data_json, new_data_json,
    old_visibility_level, new_visibility_level, changed_at, comment
)
    ON e.title = h.entry_title
JOIN users u ON u.username = h.changed_by_username;

COMMIT;
