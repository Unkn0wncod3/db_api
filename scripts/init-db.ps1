Write-Host "⏳ Initializing database schema (using container env)..."

docker compose exec -T db sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /db/init.sql'

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ init.sql erfolgreich ausgeführt."
} else {
    Write-Host "❌ Fehler beim Ausführen von init.sql."
    exit $LASTEXITCODE
}