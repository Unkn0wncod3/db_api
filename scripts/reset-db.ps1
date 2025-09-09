param(
  [switch]$RebuildApi = $false
)

Write-Host "ACHTUNG: Löscht das DB-Volume (alle Daten weg)!" -ForegroundColor Yellow
$confirm = Read-Host "Fortfahren? (ja/nein)"
if ($confirm -ne "ja") { exit 0 }

# Nur DB-Container + Volume löschen
docker compose stop db
# ganzes Compose runter + Volumes löschen (einfachster sicherer Weg)
docker compose down -v

# neu starten
if ($RebuildApi) {
  docker compose up -d --build
} else {
  docker compose up -d
}

# Warten bis DB gesund ist
Write-Host "Warte auf DB Healthcheck..."
docker compose ps
