# QC Inspection Terminal - Endpoint smoke test
#
# Designed for Windows PowerShell 5.1 (no pwsh required).
# Verifies:
#   1. Health endpoint OK
#   2. Unit lookup by serial 200 + 404 for unknown
#   3. PASS inspection creates record + history_count grows
#   4. Idempotency-Key replay (same key+payload) returns same id
#   5. Idempotency-Key conflict (same key, different payload) -> 409
#   6. REPAIR then PASS in second cycle -> 2 history rows, no auto bonus
#   7. REJECT with no defects -> 422
#   8. POST inspection on terminal status -> 422
#   9. POST without Idempotency-Key -> 422 (header required)
#  10. Workflow summary returns shape
#
# Backend HARUS sudah running di http://127.0.0.1:8010
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\test_endpoints.ps1

$BASE = "http://127.0.0.1:8010/api/qc-inspection-terminal"
$PASS = 0
$FAIL = 0
$results = @()

function Write-Case([string]$Name, [bool]$Ok, [string]$Extra = "") {
    if ($Ok) {
        Write-Host "  PASS  $Name" -ForegroundColor Green
        $script:PASS++
    } else {
        Write-Host "  FAIL  $Name  $Extra" -ForegroundColor Red
        $script:FAIL++
    }
}

function Get-Json {
    param([string]$Method, [string]$Url, [string]$Body = $null, [hashtable]$Headers = @{})
    try {
        $params = @{
            Uri            = $Url
            Method         = $Method
            UseBasicParsing = $true
            ErrorAction    = "Stop"
            ContentType    = "application/json"
        }
        if ($Body) { $params.Body = $Body }
        $hdrs = New-Object "System.Collections.Generic.Dictionary[string,string]"
        foreach ($k in $Headers.Keys) { $hdrs[$k] = $Headers[$k] }
        $params.Headers = $hdrs
        $r = Invoke-WebRequest @params
        return @{ Status = [int]$r.StatusCode; Body = ($r.Content | ConvertFrom-Json) }
    } catch {
        if ($_.Exception.Response) {
            $code = 0
            try { $code = [int]$_.Exception.Response.StatusCode } catch {}
            # Windows PowerShell 5.1: on Invoke-WebRequest failure the raw
            # response stream is often already consumed and yields an empty
            # string. $_.ErrorDetails.Message reliably carries the response
            # body; fall back to the stream only if it is unavailable.
            $text = $null
            if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $text = $_.ErrorDetails.Message }
            if (-not $text) {
                try {
                    $stream = $_.Exception.Response.GetResponseStream()
                    $reader = New-Object System.IO.StreamReader($stream)
                    $text = $reader.ReadToEnd()
                } catch {}
            }
            $json = $null
            try { $json = $text | ConvertFrom-Json } catch { $json = $null }
            return @{ Status = $code; Body = $json; Raw = $text }
        }
        return @{ Status = 0; Body = $null; Raw = $_.Exception.Message }
    }
}

# 1. Health
Write-Host ""
Write-Host "[Q1] Health check" -ForegroundColor Yellow
$r = Get-Json -Method GET -Url "$BASE/health"
Write-Case "GET /health 200" ($r.Status -eq 200 -and $r.Body.status -eq "healthy")

# 2. Lookup
Write-Host "[Q2] Lookup by serial" -ForegroundColor Yellow
$r = Get-Json -Method GET -Url "$BASE/units/lookup?serial=U-501"
Write-Case "GET /units/lookup?serial=U-501 (200, pending_qc=True)" `
    ($r.Status -eq 200 -and $r.Body.unit.serial_code -eq "U-501" -and $r.Body.unit.pending_qc -eq $true)
$r404 = Get-Json -Method GET -Url "$BASE/units/lookup?serial=NOPE-$$"
Write-Case "GET /units/lookup?serial=NOPE -> 404" ($r404.Status -eq 404)

# 3. PASS workflow
Write-Host "[Q3] Record PASS for U-501" -ForegroundColor Yellow
$KEY_PASS = "tc-pass-$([guid]::NewGuid().ToString())"
$body1 = @{
    unit_id      = $r.Body.unit.id
    disposition  = "PASS"
    inspector_id = "qc-001"
    defects      = @()
    notes        = "smoke-test pass"
} | ConvertTo-Json -Depth 6
$rPass = Get-Json -Method POST -Url "$BASE/inspections" -Body $body1 -Headers @{ "Idempotency-Key" = $KEY_PASS }
Write-Case "POST /inspections PASS U-501 -> 201" ($rPass.Status -eq 201)
Write-Case "side_effects.wage_credit_created == False" `
    ($rPass.Body.side_effects.wage_credit_created -eq $false)
Write-Case "side_effects.qc_bonus_accrual_created == False" `
    ($rPass.Body.side_effects.qc_bonus_accrual_created -eq $false)
Write-Case "unit_after.is_pass == True" ($rPass.Body.unit_after.is_pass -eq $true)
Write-Case "unit_after.pending_qc == False" ($rPass.Body.unit_after.pending_qc -eq $false)
$pass_id = $rPass.Body.inspection.id

# 4. Idempotent replay (same key + same body)
Write-Host "[Q4] Idempotent replay (same key + same body)" -ForegroundColor Yellow
$rReplay = Get-Json -Method POST -Url "$BASE/inspections" -Body $body1 -Headers @{ "Idempotency-Key" = $KEY_PASS }
Write-Case "Replay returns same inspection.id" ($rReplay.Body.inspection.id -eq $pass_id)
Write-Case "Replay flagged idempotent_replay=True" ($rReplay.Body.idempotent_replay -eq $true)

# 5. Idempotency conflict (same key, different body)
Write-Host "[Q5] Idempotency conflict (same key, different body) -> 409" -ForegroundColor Yellow
$body2 = @{
    unit_id      = $r.Body.unit.id
    disposition  = "REJECT"
    inspector_id = "qc-001"
    defects      = @( @{
        component_code = "SLEEVE"
        code           = "DEFECT_A"
    } )
    notes = "different payload - hash mismatch"
} | ConvertTo-Json -Depth 6
$rConflict = Get-Json -Method POST -Url "$BASE/inspections" -Body $body2 -Headers @{ "Idempotency-Key" = $KEY_PASS }
Write-Case "Conflict returns 409" ($rConflict.Status -eq 409)
Write-Case "Conflict code == IDEMPOTENCY_CONFLICT" ($rConflict.Body.detail.code -eq "IDEMPOTENCY_CONFLICT")

# 6. REPAIR then PASS again on U-502
Write-Host "[Q6] REPAIR then PASS on U-502 (2 history rows, no auto bonus)" -ForegroundColor Yellow
$r502 = Get-Json -Method GET -Url "$BASE/units/lookup?serial=U-502"
$unit502 = $r502.Body.unit.id
$KEY_REPAIR = "tc-repair-$([guid]::NewGuid().ToString())"
$bodyRepair = @{
    unit_id      = $unit502
    disposition  = "REPAIR"
    inspector_id = "qc-001"
    defects      = @( @{ component_code = "ZIPPER"; code = "ZIPPER_OFF" } )
    notes        = "rework"
} | ConvertTo-Json -Depth 6
$rRepair = Get-Json -Method POST -Url "$BASE/inspections" -Body $bodyRepair -Headers @{ "Idempotency-Key" = $KEY_REPAIR }
Write-Case "POST REPAIR U-502 -> 201" ($rRepair.Status -eq 201 -and $rRepair.Body.unit_after.status -eq "REWORK")
$KEY_REPASS = "tc-repass-$([guid]::NewGuid().ToString())"
$bodyPass = @{
    unit_id      = $unit502
    disposition  = "PASS"
    inspector_id = "qc-001"
    defects      = @()
    notes        = "after repair pass"
} | ConvertTo-Json -Depth 6
$rRePass = Get-Json -Method POST -Url "$BASE/inspections" -Body $bodyPass -Headers @{ "Idempotency-Key" = $KEY_REPASS }
Write-Case "POST PASS U-502 (after REPAIR) -> 201" ($rRePass.Status -eq 201)
Write-Case "side_effects.wage_credit_created == False (no double credit)" `
    ($rRePass.Body.side_effects.wage_credit_created -eq $false)
Write-Case "side_effects.qc_bonus_accrual_created == False" `
    ($rRePass.Body.side_effects.qc_bonus_accrual_created -eq $false)

# 7. REJECT without defects -> 422
Write-Host "[Q7] REJECT without defects -> 422" -ForegroundColor Yellow
$r503 = Get-Json -Method GET -Url "$BASE/units/lookup?serial=U-503"
$unit503 = $r503.Body.unit.id
$KEY_REJECT_EMPTY = "tc-reject-empty-$([guid]::NewGuid().ToString())"
$bodyBad = @{
    unit_id      = $unit503
    disposition  = "REJECT"
    inspector_id = "qc-001"
    defects      = @()
    notes        = "should be rejected"
} | ConvertTo-Json -Depth 6
$rBad = Get-Json -Method POST -Url "$BASE/inspections" -Body $bodyBad -Headers @{ "Idempotency-Key" = $KEY_REJECT_EMPTY }
Write-Case "REJECT without defects -> 422" ($rBad.Status -eq 422)

# 8. Inspecting a terminal unit again -> 422
Write-Host "[Q8] Inspecting already-PASS U-501 -> 422" -ForegroundColor Yellow
$KEY_AGAIN = "tc-again-$([guid]::NewGuid().ToString())"
$bodyAgain = @{
    unit_id      = $r.Body.unit.id
    disposition  = "PASS"
    inspector_id = "qc-001"
    defects      = @()
    notes        = "second pass attempt"
} | ConvertTo-Json -Depth 6
$rAgain = Get-Json -Method POST -Url "$BASE/inspections" -Body $bodyAgain -Headers @{ "Idempotency-Key" = $KEY_AGAIN }
Write-Case "Terminal status guard -> 422" ($rAgain.Status -eq 422)

# 9. POST without Idempotency-Key -> 422
Write-Host "[Q9] POST without Idempotency-Key -> 422" -ForegroundColor Yellow
$bodyNoKey = @{
    unit_id      = $unit503
    disposition  = "REJECT"
    inspector_id = "qc-001"
    defects      = @( @{
        component_code = "COLLAR"
        code           = "STITCH_LOOSE"
    } )
    notes = "should fail without header"
} | ConvertTo-Json -Depth 6
$rNoKey = Get-Json -Method POST -Url "$BASE/inspections" -Body $bodyNoKey
Write-Case "Missing Idempotency-Key -> 422" ($rNoKey.Status -eq 422)

# 10. History per unit
Write-Host "[Q10] History per unit (U-502 should have 2)" -ForegroundColor Yellow
$rHist = Get-Json -Method GET -Url "$BASE/units/$unit502/inspections"
Write-Case "GET /units/{id}/inspections 200" ($rHist.Status -eq 200)
Write-Case "history_count >= 2 for U-502" ($rHist.Body.history_count -ge 2)
Write-Case "append_only == True" ($rHist.Body.append_only -eq $true)

# 11. Workflow summary
Write-Host "[Q11] Workflow summary shape" -ForegroundColor Yellow
$rSum = Get-Json -Method GET -Url "$BASE/workflow/summary"
Write-Case "summary has qc.pass_count" ($null -ne $rSum.Body.qc.pass_count)
Write-Case "summary has qc.reject_count" ($null -ne $rSum.Body.qc.reject_count)

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " PASS = $PASS / FAIL = $FAIL" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
if ($FAIL -gt 0) { exit 1 } else { exit 0 }
