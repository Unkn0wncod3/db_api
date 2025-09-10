# Spielt Beispiel-Daten ein
Write-Host "⏳ Seeding example data (using container env)..."

docker compose exec -T db sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /db/example_data.sql'
if ($LASTEXITCODE -eq 0) {
  Write-Host "✅ example_data.sql erfolgreich ausgeführt."
} else {
  Write-Host "❌ Fehler beim Ausführen von example_data.sql."
  exit $LASTEXITCODE
}
