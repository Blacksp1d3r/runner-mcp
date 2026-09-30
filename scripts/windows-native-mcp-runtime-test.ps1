# Windows-native control test for Runner MCP issue #194.
# Creates only a disposable venv under %TEMP%.

$ErrorActionPreference = "Stop"

function Section([string]$Name) {
    Write-Host ""
    Write-Host "=== $Name ==="
}

$py = $null
try {
    $candidate = (& py -3.12 -c "import sys; print(sys.executable)" 2>$null).Trim()
    if ($candidate) { $py = $candidate }
} catch {}

if (-not $py) {
    try {
        $candidate = (& python -c "import sys; print(sys.executable)" 2>$null).Trim()
        if ($candidate) {
            $ver = & $candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
            if ($ver.Trim() -eq "3.12") { $py = $candidate }
        }
    } catch {}
}

if (-not $py) {
    Write-Host "NO_PYTHON_312"
    Write-Host "Install a native CPython 3.12 runtime first, then rerun this script."
    exit 12
}

Section "BASE PYTHON"
& $py --version
& $py -c "import sys,platform; print(sys.executable); print(platform.platform())"

$venv = Join-Path $env:TEMP "mcp-native-win"
if (Test-Path $venv) { Remove-Item -Recurse -Force $venv }

Section "CREATE DISPOSABLE VENV"
& $py -m venv $venv
$venvPy = Join-Path $venv "Scripts\python.exe"
& $venvPy -m pip install --disable-pip-version-check --upgrade pip

Section "INSTALL EXACT KNOWN STACK"
$pkgs = @(
    "mcp==2.2.0",
    "mcp-types==2.2.0",
    "pydantic==2.13.5",
    "pydantic-core==2.46.5",
    "starlette==0.52.1",
    "httpx2==2.13.1",
    "cryptography==50.0.2",
    "cffi==2.1.1",
    "rpds-py==2026.6.3"
)
& $venvPy -m pip install --disable-pip-version-check --only-binary=:all: $pkgs
& $venvPy -m pip check

Section "VERSIONS"
$code = "import importlib.metadata as m, sys; print(sys.version); [print(p, m.version(p)) for p in ('mcp','mcp-types','pydantic','pydantic-core','starlette','httpx2','cryptography','cffi','rpds-py')]"
& $venvPy -c $code

Section "FRESH-PROCESS STRESS"
$modules = @("mcp_types", "mcp.server")
foreach ($module in $modules) {
    Write-Host "=== TEST: $module ==="
    for ($i = 1; $i -le 100; $i++) {
        & $venvPy -X faulthandler -c "import importlib; importlib.import_module('$module')" *> $null
        $rc = $LASTEXITCODE
        if ($rc -ne 0) {
            Write-Host "FAIL: $module iteration=$i rc=$rc"
            Write-Host ("rc_hex=0x{0:X8}" -f ([uint32]$rc))
            exit $rc
        }
        if (($i % 10) -eq 0) { Write-Host "$module $i/100 OK" }
    }
    Write-Host "PASS: $module 100/100"
}

Section "RESULT"
Write-Host "PASS: native Windows CPython control completed without process crash."
