param([ValidateSet('build','run','stop','logs','test','health')][string]$Action = 'run')
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    switch ($Action) {
        'build' { docker compose build }
        'run' { docker compose up -d --build --wait }
        'stop' { docker compose down }
        'logs' { docker compose logs -f }
        'test' { docker compose run --rm --no-deps -v "${PWD}/tests:/app/tests:ro" taskboard python -m unittest discover -s tests -v }
        'health' { docker compose exec -T taskboard python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read().decode())" }
    }
    if ($LASTEXITCODE -ne 0) { throw "Docker command failed (exit $LASTEXITCODE)." }
} finally { Pop-Location }
