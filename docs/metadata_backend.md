# Metadata Backend

## Architecture Overview

The backend uses a fixed relational core and stores business-specific payloads in `entries.data_json`.
Runtime extensibility is handled through `schemas` and `fields`.

Structure:

- `api/app/core`: typed enums and shared HTTP-level errors
- `api/app/models`: lightweight domain models
- `api/app/repositories`: SQL access layer
- `api/app/services`: business logic for schemas, entries, history, relations, permissions and attachments
- `api/app/validation`: dynamic field validation against schema metadata
- `api/app/permissions`: access-control logic
- `api/app/routers`: generic FastAPI endpoints
- `api/app/example_usage.py`: executable usage examples for common flows

## Core Data Model

The SQL schema is defined in [`db/init.sql`](/c:/dev/git/db_api/db/init.sql).

Core tables:

- `schemas`
- `fields`
- `entries`
- `entry_relations`
- `entry_history`
- `attachments`
- `entry_permissions`

Supporting tables kept from the existing app:

- `users`


## Validation Model

Entry validation is handled in [`api/app/validation/entries.py`](/c:/dev/git/db_api/api/app/validation/entries.py).

Validation flow:

1. Load schema
2. Load active fields
3. Reject unknown keys
4. Apply required/default rules
5. Validate data types
6. Apply field-level rules from `validation_json`
7. Enforce `is_unique` fields against existing entries

Supported validation keys:

- `min_length`
- `max_length`
- `regex`
- `min`
- `max`
- `options`
- `allow_null`

## Permission Model

Access control is implemented in [`api/app/permissions/access_control.py`](/c:/dev/git/db_api/api/app/permissions/access_control.py).

Global roles are defined in [`roles.py`](/c:/dev/git/db_api/api/app/roles.py):

- `head_admin`
- `admin`
- `manager`
- `editor`
- `reader`

Global role intent:

- `head_admin`: full system control
- `admin`: full system control except assigning `admin` and `head_admin`
- `manager`: schema and entry management
- `editor`: entry management
- `reader`: read-only access

Decision order:

1. Admin roles bypass checks
2. `public` entries are readable by everyone
3. `internal` entries are readable by authenticated users
4. Owner has full access
5. Direct `user` grants are checked
6. Matching `role` grants are checked
7. Matching `group` grants are checked

Notes:

- `restricted` and `private` do not grant read access by visibility alone
- `manage` implies all entry permissions
- `manage_permissions` is separate from data editing
- `manage_attachments` is separate from relation management
- `view_history` is separate from normal read access

Available entry permissions:

- `read`
- `view_history`
- `edit`
- `edit_status`
- `edit_visibility`
- `manage_relations`
- `manage_attachments`
- `manage_permissions`
- `delete`
- `manage`

## Example Flows

Examples are implemented in [`api/app/example_usage.py`](/c:/dev/git/db_api/api/app/example_usage.py):

- `create_person_schema_example`
- `create_entry_example`
- `update_entry_with_history_example`
- `check_access_example`
- `create_relation_example`

## API Surface

Generic endpoints:

- `GET /schemas`
- `POST /schemas`
- `POST /schemas/{schema_id}/fields`
- `GET /entries`
- `POST /entries`
- `PATCH /entries/{entry_id}`
- `GET /entries/{entry_id}/history`
- `POST /entries/{entry_id}/relations`
- `POST /entries/{entry_id}/permissions`
- `POST /entries/{entry_id}/attachments`

Attachment link endpoint:

- `POST /entries/{entry_id}/attachments`
- Body example:
```json
{
  "file_name": "contract.pdf",
  "external_url": "https://drive.google.com/file/d/abc/view",
  "mime_type": "application/pdf",
  "file_size": 123456,
  "description": "Google Drive reference"
}
```

## Assumptions

- The project stays on `FastAPI + psycopg` instead of introducing a new ORM stack.
- `reference` fields store entry ids in `data_json`.
- `file` fields store attachment ids in `data_json`.
- Attachments are metadata-only references to external URLs, suitable for Railway hosting.
- `group` permissions rely on `current_user["group_ids"]` when provided by the auth layer.
