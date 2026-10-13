# =============================================================================
# API Endpoint Test Script - Sampling & Spec R&D
# Jalankan: .\test_endpoints.ps1
# Pastikan backend sudah running di port 8007 sebelum test
# =============================================================================

$BASE = "http://127.0.0.1:8007/api/sampling-spec-rnd"
$PASS = 0
$FAIL = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [string]$Body = $null
    )

    try {
        $params = @{
            Uri    = $Url
            Method = $Method
            UseBasicParsing = $true
            ErrorAction = "Stop"
        }
        if ($Body) {
            $params.Body = $Body
            $params.ContentType = "application/json"
        }
        $response = Invoke-WebRequest @params
        $data = $response.Content | ConvertFrom-Json
        if ($data.success -eq $true -or $data.status) {
            Write-Host "  ✅ PASS - $Name" -ForegroundColor Green
            $script:PASS++
            return $data
        } else {
            Write-Host "  ❌ FAIL - $Name (success=false)" -ForegroundColor Red
            Write-Host "     Response: $($response.Content)" -ForegroundColor DarkRed
            $script:FAIL++
            return $null
        }
    } catch {
        Write-Host "  ❌ FAIL - $Name" -ForegroundColor Red
        Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor DarkRed
        $script:FAIL++
        return $null
    }
}

# =============================================================================
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        API ENDPOINT TEST - Sampling & Spec R&D          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# =============================================================================
Write-Host "▶ HEALTH CHECK" -ForegroundColor Yellow
Write-Host "──────────────────────────────────────────────────────────"

$health = Test-Endpoint "GET /health" "GET" "$BASE/health"
if ($health) {
    Write-Host "     Status: $($health.status)" -ForegroundColor DarkGray
}

# =============================================================================
Write-Host ""
Write-Host "▶ TIME STUDY ENDPOINTS" -ForegroundColor Yellow
Write-Host "──────────────────────────────────────────────────────────"

# 1. Create Study
$create = Test-Endpoint `
    "POST /studies/create" "POST" `
    "$BASE/studies/create?tenant_id=tenant_001&process_id=proc_001&process_name=Jahit+Baju&operator_id=op_001&target_sample_size=5"

$STUDY_ID = $null
if ($create) {
    $STUDY_ID = $create.study_id
    Write-Host "     study_id: $STUDY_ID" -ForegroundColor DarkGray
}

# 2. Start Study
if ($STUDY_ID) {
    $start = Test-Endpoint `
        "POST /studies/{id}/start" "POST" `
        "$BASE/studies/$STUDY_ID/start"
    if ($start) { Write-Host "     Message: $($start.message)" -ForegroundColor DarkGray }
}

# 3. Add Samples (5x)
if ($STUDY_ID) {
    $sampleTimes = @(3500, 3200, 3800, 3400, 3600)
    $i = 1
    foreach ($t in $sampleTimes) {
        $addSample = Test-Endpoint `
            "POST /studies/{id}/add-sample (sample $i)" "POST" `
            "$BASE/studies/$STUDY_ID/add-sample?cycle_time_ms=$t&element_name=Jahit+Bagian+$i"
        if ($addSample) { Write-Host "     cycle_time_ms: ${t}ms" -ForegroundColor DarkGray }
        $i++
    }
}

# 4. Pause Study
if ($STUDY_ID) {
    $pause = Test-Endpoint `
        "POST /studies/{id}/pause" "POST" `
        "$BASE/studies/$STUDY_ID/pause"
    if ($pause) { Write-Host "     Message: $($pause.message)" -ForegroundColor DarkGray }
}

# 5. Resume Study
if ($STUDY_ID) {
    $resume = Test-Endpoint `
        "POST /studies/{id}/resume" "POST" `
        "$BASE/studies/$STUDY_ID/resume"
    if ($resume) { Write-Host "     Message: $($resume.message)" -ForegroundColor DarkGray }
}

# 6. Get Study Stats
if ($STUDY_ID) {
    $stats = Test-Endpoint `
        "GET /studies/{id}/stats" "GET" `
        "$BASE/studies/$STUDY_ID/stats"
    if ($stats -and $stats.statistics) {
        $s = $stats.statistics
        Write-Host "     Total samples: $($s.total_samples)" -ForegroundColor DarkGray
        Write-Host "     Mean cycle time: $($s.mean_cycle_time_ms)ms" -ForegroundColor DarkGray
    }
}

# 7. Complete Study
if ($STUDY_ID) {
    $complete = Test-Endpoint `
        "POST /studies/{id}/complete" "POST" `
        "$BASE/studies/$STUDY_ID/complete"
    if ($complete) { Write-Host "     Message: $($complete.message)" -ForegroundColor DarkGray }
}

# 8. Get Study Data
if ($STUDY_ID) {
    $data = Test-Endpoint `
        "GET /studies/{id}/data" "GET" `
        "$BASE/studies/$STUDY_ID/data"
    if ($data) { Write-Host "     Data exported OK" -ForegroundColor DarkGray }
}

# =============================================================================
Write-Host ""
Write-Host "▶ SPECIFICATION ENDPOINTS" -ForegroundColor Yellow
Write-Host "──────────────────────────────────────────────────────────"

# 9. Create Spec
$createSpec = Test-Endpoint `
    "POST /specs/create" "POST" `
    "$BASE/specs/create?tenant_id=tenant_001&spec_id=spec_001&spec_name=Spec+Kain+Katun&created_by=user_001&version_number=1.0.0"

$VERSION_ID = $null
if ($createSpec) {
    $VERSION_ID = $createSpec.version_id
    Write-Host "     version_id: $VERSION_ID" -ForegroundColor DarkGray
}

# 10. Record Spec Change
if ($VERSION_ID) {
    $change = Test-Endpoint `
        "POST /specs/{id}/record-change" "POST" `
        "$BASE/specs/$VERSION_ID/record-change?change_type=TOLERANCE_CHANGE&parameter_name=Lebar+Kain&old_value=150&new_value=152&changed_by=user_001&reason=Penyesuaian+standar+baru"
    if ($change) { Write-Host "     Message: $($change.message)" -ForegroundColor DarkGray }
}

# 11. Record Drift
if ($VERSION_ID) {
    $drift = Test-Endpoint `
        "POST /specs/{id}/record-drift" "POST" `
        "$BASE/specs/$VERSION_ID/record-drift?parameter_name=Lebar+Kain&specification_limit=152&measured_value=155&severity=medium&corrective_action=Review+mesin"
    if ($drift) { Write-Host "     Message: $($drift.message)" -ForegroundColor DarkGray }
}

# 12. Submit for Review
if ($VERSION_ID) {
    $review = Test-Endpoint `
        "POST /specs/{id}/submit-review" "POST" `
        "$BASE/specs/$VERSION_ID/submit-review?reviewer_id=reviewer_001"
    if ($review) { Write-Host "     Message: $($review.message)" -ForegroundColor DarkGray }
}

# 13. Approve Spec
if ($VERSION_ID) {
    $approve = Test-Endpoint `
        "POST /specs/{id}/approve" "POST" `
        "$BASE/specs/$VERSION_ID/approve?approver_id=approver_001"
    if ($approve) { Write-Host "     Message: $($approve.message)" -ForegroundColor DarkGray }
}

# 14. Activate Spec
if ($VERSION_ID) {
    $activate = Test-Endpoint `
        "POST /specs/{id}/activate" "POST" `
        "$BASE/specs/$VERSION_ID/activate"
    if ($activate) { Write-Host "     Message: $($activate.message)" -ForegroundColor DarkGray }
}

# 15. Get Drift Report
if ($VERSION_ID) {
    $driftReport = Test-Endpoint `
        "GET /specs/{id}/drift-report" "GET" `
        "$BASE/specs/$VERSION_ID/drift-report"
    if ($driftReport) { Write-Host "     Report generated OK" -ForegroundColor DarkGray }
}

# 16. Get Drift Analysis
if ($VERSION_ID) {
    $driftAnalysis = Test-Endpoint `
        "GET /specs/{id}/drift-analysis" "GET" `
        "$BASE/specs/$VERSION_ID/drift-analysis"
    if ($driftAnalysis) { Write-Host "     Risk score: $($driftAnalysis.risk_score)" -ForegroundColor DarkGray }
}

# 17. Get Change History
if ($VERSION_ID) {
    $history = Test-Endpoint `
        "GET /specs/{id}/change-history" "GET" `
        "$BASE/specs/$VERSION_ID/change-history"
    if ($history) { Write-Host "     History retrieved OK" -ForegroundColor DarkGray }
}

# 18. Get Spec Data
if ($VERSION_ID) {
    $specData = Test-Endpoint `
        "GET /specs/{id}/data" "GET" `
        "$BASE/specs/$VERSION_ID/data"
    if ($specData) { Write-Host "     Spec data exported OK" -ForegroundColor DarkGray }
}

# =============================================================================
Write-Host ""
Write-Host "▶ WORKFLOW ENDPOINTS" -ForegroundColor Yellow
Write-Host "──────────────────────────────────────────────────────────"

# 19. Workflow Summary
$summary = Test-Endpoint `
    "GET /workflow/summary" "GET" `
    "$BASE/workflow/summary?tenant_id=tenant_001"
if ($summary) { Write-Host "     Summary retrieved OK" -ForegroundColor DarkGray }

# =============================================================================
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                   TEST RESULTS                          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

$TOTAL = $PASS + $FAIL
Write-Host ""
Write-Host "  Total  : $TOTAL endpoints" -ForegroundColor White
Write-Host "  Passed : $PASS ✅" -ForegroundColor Green
Write-Host "  Failed : $FAIL ❌" -ForegroundColor $(if ($FAIL -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($FAIL -eq 0) {
    Write-Host "  🎉 ALL TESTS PASSED! Backend is fully functional." -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Some tests failed. Check backend logs for details." -ForegroundColor Yellow
    Write-Host "  Tip: Make sure backend is running: uvicorn src.main:app --reload --port 8007" -ForegroundColor DarkYellow
}
Write-Host ""
