<#
.SYNOPSIS
    verify-traceability.ps1
    Traceability verification script for Lukla Operations Engine planning suite (Phase 5).
.DESCRIPTION
    Checks the planning suite across core documents, 20 FR IDs, 8 RBAC roles,
    4 closing scenarios, and UNRESOLVED register items. Phase C adds harness
    PRD/source preservation, contract catalog, production-blocked defaults, and
    evidence-file checks.
    Exits 0 only when all checks pass; non-zero with a named failure list otherwise.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$ArtifactsDir = $PSScriptRoot
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($ArtifactsDir)) {
    $ArtifactsDir = $PSScriptRoot
}
if ([string]::IsNullOrWhiteSpace($ArtifactsDir)) {
    $ArtifactsDir = (Get-Location).Path
}

if (-not [System.IO.Path]::IsPathRooted($ArtifactsDir)) {
    $targetDir = (Resolve-Path (Join-Path (Get-Location) $ArtifactsDir)).Path
} else {
    $targetDir = (Resolve-Path $ArtifactsDir).Path
}

Write-Host "============================================================"
Write-Host " Lukla Operations Engine — Traceability Verification"
Write-Host " Target Directory: $targetDir"
Write-Host "============================================================"

$failures = [System.Collections.Generic.List[string]]::new()
$warnings = [System.Collections.Generic.List[string]]::new()

# -------------------------------------------------------------------------
# Check (a): Five core documents exist
# -------------------------------------------------------------------------
Write-Host "`n--- Check (a): Core Documents Existence ---"
$coreDocs = [ordered]@{
    'Register'         = '00-deconstruction.md'
    'RBAC Matrix'      = '04-rbac-matrix.md'
    'Acceptance Tests' = '06-acceptance-tests.md'
    'Glossary'         = '07-glossary.md'
    'BRD'              = 'Lukla Operations Engine - BRD v2.2.1 - FINAL.md'
}

$fileContents = @{}

foreach ($key in $coreDocs.Keys) {
    $fileName = $coreDocs[$key]
    $filePath = Join-Path $targetDir $fileName
    if (-not (Test-Path -LiteralPath $filePath -PathType Leaf)) {
        $parentDir = Split-Path -Parent $targetDir
        $rootCandidate = Join-Path $parentDir $fileName
        if (Test-Path -LiteralPath $rootCandidate -PathType Leaf) {
            $filePath = $rootCandidate
        }
        if ($key -eq 'BRD') {
            $candidates = @(
                (Join-Path $parentDir 'BRD - Lukla Operations Engine - v2.2.1 - FINAL.md'),
                (Join-Path (Split-Path -Parent $parentDir) 'BRD - Lukla Operations Engine - v2.2.1 - FINAL.md'),
                (Join-Path $targetDir 'BRD - Lukla Operations Engine - v2.2.1 - FINAL.md')
            )
            foreach ($c in $candidates) {
                if (Test-Path -LiteralPath $c -PathType Leaf) {
                    $filePath = $c
                    break
                }
            }
        }
    }
    if (Test-Path -LiteralPath $filePath -PathType Leaf) {
        Write-Host "  [PASS] Document exists ($key): $fileName"
        $fileContents[$key] = Get-Content -LiteralPath $filePath -Raw -Encoding utf8
    } else {
        $msg = "Check (a) FAIL: Missing core document ($key): $fileName at $filePath"
        Write-Host "  [FAIL] $msg" -ForegroundColor Red
        $failures.Add($msg)
    }
}

if ($failures.Count -gt 0) {
    Write-Host "`nVerification halted due to missing core files." -ForegroundColor Red
    Write-Host "`nFAILED CHECKS ($($failures.Count)):" -ForegroundColor Red
    foreach ($f in $failures) {
        Write-Host " - $f" -ForegroundColor Red
    }
    exit 1
}

$registerText = $fileContents['Register']
$rbacText     = $fileContents['RBAC Matrix']
$atText       = $fileContents['Acceptance Tests']
$glossaryText = $fileContents['Glossary']
$brdText      = $fileContents['BRD']

# -------------------------------------------------------------------------
# Check (a2): Phase C authored artifacts and source preservation
# -------------------------------------------------------------------------
Write-Host "`n--- Check (a2): Phase C Harness and Source Preservation ---"
$changeRoot = Split-Path -Parent $targetDir
$phaseBFiles = @(
    '13-authn-authz-design.md', '14-frontend-architecture.md',
    '15-deployment-and-operations.md', '16-test-harness-and-agent-verification.md',
    '17-semantic-search-module.md', '19-business-defaults-register.md',
    '18-parallelization-and-workstreams.md'
)
foreach ($name in $phaseBFiles) {
    if (Test-Path -LiteralPath (Join-Path $targetDir $name) -PathType Leaf) { Write-Host "  [PASS] Evidence file exists: $name" }
    else { $msg = "Check (a2) FAIL: Missing evidence file: $name"; Write-Host "  [FAIL] $msg" -ForegroundColor Red; $failures.Add($msg) }
}
$harnessPath = Join-Path $targetDir '16-test-harness-and-agent-verification.md'
$harnessText = Get-Content -LiteralPath $harnessPath -Raw -Encoding utf8
$prdIds = @('FR-1.1','FR-1.4','FR-2.1','FR-3.1','FR-4.1','FR-4.2','FR-4.3','FR-5','FR-5.1','FR-5.2','FR-6','FR-6.1','FR-6.2','FR-6.3','FR-7.1','FR-7.2','FR-7.3','FR-7.4','FR-8.1','FR-8.2','FR-9.1','FR-9.2','FR-10.1','FR-10.2','FR-10.3','FR-10.4')
$sourceIds = @('FR-1.1','FR-1.4','FR-2.1','FR-3.1','FR-4.1','FR-5','FR-6','FR-6.2','FR-7.1','FR-7.2','FR-7.3','FR-7.4','FR-8.1','FR-8.2','FR-9.1','FR-9.2','FR-10.1','FR-10.2','FR-10.3','FR-10.4')
foreach ($id in $prdIds) { if ($harnessText -match "\b$([regex]::Escape($id))\b") { } else { $msg = "Check (a2) FAIL: Harness missing PRD ID $id"; Write-Host "  [FAIL] $msg" -ForegroundColor Red; $failures.Add($msg) } }
foreach ($id in $sourceIds) { if ($harnessText -match "\b$([regex]::Escape($id))\b") { } else { $msg = "Check (a2) FAIL: Harness missing source ID $id"; Write-Host "  [FAIL] $msg" -ForegroundColor Red; $failures.Add($msg) } }
if ($harnessText -match 'AT-01' -and $harnessText -match 'AT-R01' -and $harnessText -match 'Closing-01') { Write-Host '  [PASS] Harness scenario families present' } else { $msg = 'Check (a2) FAIL: Harness scenario families are incomplete'; Write-Host "  [FAIL] $msg" -ForegroundColor Red; $failures.Add($msg) }
$defaultsPath = Join-Path $targetDir '19-business-defaults-register.md'
$defaultsText = Get-Content -LiteralPath $defaultsPath -Raw -Encoding utf8
if ($defaultsText -match 'UNRESOLVED / PRODUCTION_BLOCKED') { Write-Host '  [PASS] Production-blocked defaults are preserved' } else { $msg = 'Check (a2) FAIL: Production-blocked default marker missing'; Write-Host "  [FAIL] $msg" -ForegroundColor Red; $failures.Add($msg) }

# -------------------------------------------------------------------------
# Check (b): 20 FR IDs in Register, BRD §16.5, and Acceptance Test Coverage
# -------------------------------------------------------------------------
Write-Host "`n--- Check (b): 20 FR IDs Traceability & Coverage ---"
$frIds = @(
    'FR-1.1', 'FR-1.4', 'FR-2.1', 'FR-3.1', 'FR-4.1',
    'FR-5',   'FR-6',   'FR-6.2', 'FR-7.1', 'FR-7.2',
    'FR-7.3', 'FR-7.4', 'FR-8.1', 'FR-8.2', 'FR-9.1',
    'FR-9.2', 'FR-10.1', 'FR-10.2', 'FR-10.3', 'FR-10.4'
)

$sec165Text = ""
if ($brdText -match '(?ms)(?:#+\s*(?:\*\*)?16\.5).*?(?=#+\s*(?:\*\*)?16\.6|\Z)') {
    $sec165Text = $Matches[0]
} else {
    $msg = "Check (b) FAIL: Could not locate Section 16.5 in BRD"
    Write-Host "  [FAIL] $msg" -ForegroundColor Red
    $failures.Add($msg)
}

foreach ($fr in $frIds) {
    # 1. Register presence
    $pattern = "\b" + [regex]::Escape($fr) + "\b"
    if ($registerText -match $pattern) {
        Write-Host "  [PASS] Register contains $fr"
    } else {
        $msg = "Check (b) FAIL: Register (00-deconstruction.md) missing $fr"
        Write-Host "  [FAIL] $msg" -ForegroundColor Red
        $failures.Add($msg)
    }

    # 2. BRD §16.5 presence
    if ($sec165Text -match $pattern) {
        Write-Host "  [PASS] BRD §16.5 contains $fr"
    } else {
        $msg = "Check (b) FAIL: BRD §16.5 missing $fr"
        Write-Host "  [FAIL] $msg" -ForegroundColor Red
        $failures.Add($msg)
    }

    # 3. Acceptance test coverage check
    # Note: FR-8.2 is linked as FR-8.1/8.2 in 06-acceptance-tests.md AT-05
    $atPattern = if ($fr -eq 'FR-8.2') {
        '(?:\bFR-8\.2\b|FR-8\.1/8\.2)'
    } else {
        "\b" + [regex]::Escape($fr) + "\b"
    }

    if ($atText -match $atPattern) {
        Write-Host "  [PASS] Acceptance tests cover $fr"
    } else {
        $warnMsg = "Check (b) WARN: Acceptance tests (06-acceptance-tests.md) lack explicit test case for $fr"
        Write-Host "  [WARN] $warnMsg" -ForegroundColor Yellow
        $warnings.Add($warnMsg)
    }
}

# -------------------------------------------------------------------------
# Check (c): All 8 role names in RBAC Matrix
# -------------------------------------------------------------------------
Write-Host "`n--- Check (c): 8 Role Names in RBAC Matrix ---"
$roleNames = @(
    'Owner/Eksekutif',
    'Tim Sample/Adis',
    'Gudang/Warehouse',
    'Kepala Produksi/Mandor',
    'Penjahit/Tailor',
    'QC Inspector',
    'Finance & Payroll',
    'Klien Maklon/Ext'
)

foreach ($role in $roleNames) {
    if ($rbacText.Contains($role)) {
        Write-Host "  [PASS] RBAC Matrix contains role: $role"
    } else {
        $msg = "Check (c) FAIL: RBAC Matrix (04-rbac-matrix.md) missing role: $role"
        Write-Host "  [FAIL] $msg" -ForegroundColor Red
        $failures.Add($msg)
    }
}

# -------------------------------------------------------------------------
# Check (d): Four closing scenarios in Acceptance Tests
# -------------------------------------------------------------------------
Write-Host "`n--- Check (d): 4 Closing Scenarios in Acceptance Tests ---"
$scenarios = @(
    @{
        Name = "Scenario 1 (cross-client material rejection / cross-client contamination)"
        Check = ($atText -match 'Closing scenario 1' -and $atText -match 'cross-client')
    },
    @{
        Name = "Scenario 2 (midweek +5 sewers & Saturday piece-rate payroll)"
        Check = ($atText -match 'Closing scenario 2' -and $atText -match '\+5 (sewers|midweek)')
    },
    @{
        Name = "Scenario 3 (3,000 Pass QC units & bonus pool ÷3)"
        Check = ($atText -match 'Closing scenario 3' -and $atText -match 'bonus pool')
    },
    @{
        Name = "Scenario 4 (sample v1 → v2 revision & Semi-CMT mass order)"
        Check = ($atText -match 'Closing scenario 4' -and $atText -match 'sample v1.*v2')
    }
)

foreach ($sc in $scenarios) {
    if ($sc.Check) {
        Write-Host "  [PASS] Acceptance tests contain $($sc.Name)"
    } else {
        $msg = "Check (d) FAIL: Acceptance tests missing $($sc.Name)"
        Write-Host "  [FAIL] $msg" -ForegroundColor Red
        $failures.Add($msg)
    }
}

# -------------------------------------------------------------------------
# Check (e): Every UNRESOLVED item in register echoed in BRD §13.3
# -------------------------------------------------------------------------
Write-Host "`n--- Check (e): UNRESOLVED Items in Register Echoed in BRD §13.3 ---"
$sec133Text = ""
if ($brdText -match '(?ms)(?:#+\s*(?:\*\*)?13\.3).*?(?=#+\s*(?:\*\*)?13\.4|#+\s*(?:\*\*)?14|\Z)') {
    $sec133Text = $Matches[0]
} else {
    $msg = "Check (e) FAIL: Could not locate Section 13.3 in BRD"
    Write-Host "  [FAIL] $msg" -ForegroundColor Red
    $failures.Add($msg)
}

$unresolvedItems = @(
    @{ Name = "Slide 02c entire content"; Pattern = "02c" },
    @{ Name = "Slide 07 original on-disk photo"; Pattern = "07" },
    @{ Name = "FR-5 (Gudang) detail"; Pattern = "FR-5" },
    @{ Name = "FR-6 (Cutting) detail"; Pattern = "FR-6" },
    @{ Name = "FR-1.4 exact wording"; Pattern = "FR-1.4" },
    @{ Name = "Bonus pool ÷3 configurability"; Pattern = "bonus" },
    @{ Name = "Uang makan base definition"; Pattern = "uang makan" }
)

foreach ($item in $unresolvedItems) {
    if ($sec133Text -match $item.Pattern) {
        Write-Host "  [PASS] BRD §13.3 echoes UNRESOLVED item: $($item.Name)"
    } else {
        $msg = "Check (e) FAIL: BRD §13.3 missing UNRESOLVED item: $($item.Name) (pattern '$($item.Pattern)')"
        Write-Host "  [FAIL] $msg" -ForegroundColor Red
        $failures.Add($msg)
    }
}

# -------------------------------------------------------------------------
# Check (f): Contract catalog uniqueness and source metadata counts
# -------------------------------------------------------------------------
Write-Host "`n--- Check (f): Contract Catalog ---"
$contractPath = Join-Path $targetDir 'contracts\openapi.yaml'
if (Test-Path -LiteralPath $contractPath -PathType Leaf) {
    $contractText = Get-Content -LiteralPath $contractPath -Raw -Encoding utf8
    $operationIds = [regex]::Matches($contractText, '(?m)^\s*operationId:\s*([^\s#]+)') | ForEach-Object { $_.Groups[1].Value }
    $duplicates = $operationIds | Group-Object | Where-Object Count -gt 1
    if ($operationIds.Count -gt 0 -and $duplicates.Count -eq 0) { Write-Host "  [PASS] operationId values unique ($($operationIds.Count))" } else { $msg = 'Check (f) FAIL: operationId values are missing or duplicated'; Write-Host "  [FAIL] $msg" -ForegroundColor Red; $failures.Add($msg) }
    foreach ($token in @('Owner','SampleTeam','Warehouse','ProductionHead','Tailor','QCInspector','FinancePayroll','MaklonClient')) { if ($contractText -match [regex]::Escape($token)) { } else { $msg = "Check (f) FAIL: Contract missing role metadata $token"; Write-Host "  [FAIL] $msg" -ForegroundColor Red; $failures.Add($msg) } }
    foreach ($token in @('VIEW-01','VIEW-02','VIEW-03','VIEW-04','VIEW-05','VIEW-06')) { if ($contractText -match [regex]::Escape($token)) { } else { $msg = "Check (f) FAIL: Contract missing view metadata $token"; Write-Host "  [FAIL] $msg" -ForegroundColor Red; $failures.Add($msg) } }
} else { $msg = "Check (f) FAIL: Missing OpenAPI contract: $contractPath"; Write-Host "  [FAIL] $msg" -ForegroundColor Red; $failures.Add($msg) }

# -------------------------------------------------------------------------
# Summary & Exit Code
# -------------------------------------------------------------------------
Write-Host "`n============================================================"
Write-Host " Verification Summary"
Write-Host "============================================================"
if ($warnings.Count -gt 0) {
    Write-Host "Warnings ($($warnings.Count)):" -ForegroundColor Yellow
    foreach ($w in $warnings) {
        Write-Host "  - $w" -ForegroundColor Yellow
    }
}

if ($failures.Count -eq 0) {
    Write-Host "`nALL TRACEABILITY CHECKS PASSED (exit code 0)." -ForegroundColor Green
    exit 0
} else {
    Write-Host "`nFAILED CHECKS ($($failures.Count)):" -ForegroundColor Red
    foreach ($f in $failures) {
        Write-Host "  - $f" -ForegroundColor Red
    }
    Write-Host "`nVerification failed with $($failures.Count) error(s) (exit code 1)." -ForegroundColor Red
    exit 1
}
