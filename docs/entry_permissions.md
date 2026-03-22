# Entry Permissions

Entry-Zugriff wird zentral in `AccessControlService` berechnet. Dieselbe Berechnung wird fuer Bundle-Antworten, Schema-Entry-Listen und `/entries/{id}/access/{permission}` verwendet.

## Auswertung

- Effektive Rechte = globale Basisrechte plus explizite Entry-Grants.
- Entry-spezifische Permissions erweitern Rechte nur, sie schraenken bestehende Rechte nicht ein.
- `manage` impliziert alle Entry-Rechte.

## Subject-Typen

- `user`: Match auf `current_user.id`
- `role`: Match auf `current_user.role`
- `group`: derzeit nicht unterstuetzt, weil kein echtes Gruppenmodell im Backend existiert; Create/Update mit `subject_type = group` werden deshalb mit `422` abgelehnt

## Basisrechte

- Admin-Rollen erhalten Vollzugriff.
- Der Owner eines Entries erhaelt Vollzugriff.
- `visibility_level = public` erlaubt `read` fuer alle.
- `visibility_level = internal` erlaubt `read` fuer eingeloggte User.

Explizite Entry-Grants werden zu diesen Basisrechten hinzuaddiert. Dadurch kann z. B. ein privater Entry durch einen `role`- oder `user`-Grant sichtbar oder bearbeitbar werden.
