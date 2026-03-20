CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'visibility_level_enum') THEN
    CREATE TYPE visibility_level_enum AS ENUM ('private', 'internal', 'restricted', 'public');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'field_data_type_enum') THEN
    CREATE TYPE field_data_type_enum AS ENUM (
      'text', 'long_text', 'integer', 'decimal', 'boolean', 'date', 'datetime',
      'email', 'url', 'select', 'multi_select', 'reference', 'file', 'json'
    );
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'permission_subject_type_enum') THEN
    CREATE TYPE permission_subject_type_enum AS ENUM ('user', 'role', 'group');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'entry_permission_enum') THEN
    CREATE TYPE entry_permission_enum AS ENUM ('read');
  END IF;
END;
$$ LANGUAGE plpgsql;

ALTER TYPE entry_permission_enum ADD VALUE IF NOT EXISTS 'view_history';
ALTER TYPE entry_permission_enum ADD VALUE IF NOT EXISTS 'edit';
ALTER TYPE entry_permission_enum ADD VALUE IF NOT EXISTS 'edit_status';
ALTER TYPE entry_permission_enum ADD VALUE IF NOT EXISTS 'edit_visibility';
ALTER TYPE entry_permission_enum ADD VALUE IF NOT EXISTS 'manage_relations';
ALTER TYPE entry_permission_enum ADD VALUE IF NOT EXISTS 'manage_attachments';
ALTER TYPE entry_permission_enum ADD VALUE IF NOT EXISTS 'manage_permissions';
ALTER TYPE entry_permission_enum ADD VALUE IF NOT EXISTS 'delete';
ALTER TYPE entry_permission_enum ADD VALUE IF NOT EXISTS 'manage';

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'reader' CHECK (role IN ('head_admin', 'admin', 'manager', 'editor', 'reader')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    profile_picture_url TEXT,
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);

DROP TRIGGER IF EXISTS trg_users_updated ON users;
CREATE TRIGGER trg_users_updated
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS schemas (
    id BIGSERIAL PRIMARY KEY,
    key TEXT NOT NULL UNIQUE CHECK (key ~ '^[a-z][a-z0-9_]*$'),
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

DROP TRIGGER IF EXISTS trg_schemas_updated ON schemas;
CREATE TRIGGER trg_schemas_updated
BEFORE UPDATE ON schemas
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS fields (
    id BIGSERIAL PRIMARY KEY,
    schema_id BIGINT NOT NULL REFERENCES schemas(id) ON DELETE CASCADE,
    key TEXT NOT NULL CHECK (key ~ '^[a-z][a-z0-9_]*$'),
    label TEXT NOT NULL,
    description TEXT,
    data_type field_data_type_enum NOT NULL,
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    is_unique BOOLEAN NOT NULL DEFAULT FALSE,
    default_value JSONB,
    sort_order INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    validation_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    settings_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT uq_fields_schema_key UNIQUE (schema_id, key)
);

CREATE INDEX IF NOT EXISTS idx_fields_schema_sort ON fields (schema_id, sort_order, id);
CREATE INDEX IF NOT EXISTS idx_fields_validation_json ON fields USING GIN (validation_json);
CREATE INDEX IF NOT EXISTS idx_fields_settings_json ON fields USING GIN (settings_json);

DROP TRIGGER IF EXISTS trg_fields_updated ON fields;
CREATE TRIGGER trg_fields_updated
BEFORE UPDATE ON fields
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS entries (
    id BIGSERIAL PRIMARY KEY,
    schema_id BIGINT NOT NULL REFERENCES schemas(id) ON DELETE RESTRICT,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    visibility_level visibility_level_enum NOT NULL DEFAULT 'private',
    owner_id INT REFERENCES users(id) ON DELETE SET NULL,
    created_by INT REFERENCES users(id) ON DELETE SET NULL,
    data_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_entries_schema_status ON entries (schema_id, status);
CREATE INDEX IF NOT EXISTS idx_entries_owner ON entries (owner_id);
CREATE INDEX IF NOT EXISTS idx_entries_visibility ON entries (visibility_level);
CREATE INDEX IF NOT EXISTS idx_entries_data_json ON entries USING GIN (data_json);

DROP TRIGGER IF EXISTS trg_entries_updated ON entries;
CREATE TRIGGER trg_entries_updated
BEFORE UPDATE ON entries
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS entry_relations (
    id BIGSERIAL PRIMARY KEY,
    from_entry_id BIGINT NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    to_entry_id BIGINT NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_entry_relations_no_self CHECK (from_entry_id <> to_entry_id)
);

CREATE INDEX IF NOT EXISTS idx_entry_relations_from ON entry_relations (from_entry_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_entry_relations_to ON entry_relations (to_entry_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_entry_relations_metadata ON entry_relations USING GIN (metadata_json);

CREATE TABLE IF NOT EXISTS entry_history (
    id BIGSERIAL PRIMARY KEY,
    entry_id BIGINT NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    changed_by INT REFERENCES users(id) ON DELETE SET NULL,
    change_type TEXT NOT NULL,
    old_data_json JSONB,
    new_data_json JSONB,
    old_visibility_level visibility_level_enum,
    new_visibility_level visibility_level_enum,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    comment TEXT
);

CREATE INDEX IF NOT EXISTS idx_entry_history_entry_time ON entry_history (entry_id, changed_at DESC);

CREATE TABLE IF NOT EXISTS attachments (
    id BIGSERIAL PRIMARY KEY,
    entry_id BIGINT NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    stored_path TEXT NOT NULL CHECK (stored_path ~ '^https?://'),
    mime_type TEXT,
    file_size BIGINT NOT NULL CHECK (file_size >= 0),
    checksum TEXT NOT NULL,
    uploaded_by INT REFERENCES users(id) ON DELETE SET NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    description TEXT,
    CONSTRAINT uq_attachments_entry_checksum UNIQUE (entry_id, checksum)
);

CREATE INDEX IF NOT EXISTS idx_attachments_entry ON attachments (entry_id, uploaded_at DESC);

CREATE TABLE IF NOT EXISTS entry_permissions (
    id BIGSERIAL PRIMARY KEY,
    entry_id BIGINT NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    subject_type permission_subject_type_enum NOT NULL,
    subject_id TEXT NOT NULL,
    permission entry_permission_enum NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by INT REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT uq_entry_permissions UNIQUE (entry_id, subject_type, subject_id, permission)
);

CREATE INDEX IF NOT EXISTS idx_entry_permissions_entry ON entry_permissions (entry_id);
CREATE INDEX IF NOT EXISTS idx_entry_permissions_subject ON entry_permissions (subject_type, subject_id);
