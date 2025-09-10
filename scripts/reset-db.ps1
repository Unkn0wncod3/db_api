# Löscht alle Objekte per drop_all.sql, nutzt Container-ENVs
Write-Host "⏳ Dropping all DB objects (using container env)..."

# Nutze die im Container vorhandenen Variablen aus .env
docker compose exec -T db sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /db/drop_all.sql'
if ($LASTEXITCODE -eq 0) {
  Write-Host "✅ drop_all.sql erfolgreich ausgeführt."
} else {
  Write-Host "❌ Fehler beim Ausführen von drop_all.sql."
  exit $LASTEXITCODE
}
