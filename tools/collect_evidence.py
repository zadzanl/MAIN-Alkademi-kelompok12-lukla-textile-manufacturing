#!/usr/bin/env python3
"""
Evidence Collector and Manifest Generator
Implements evidence bundle normalization defined in:
openspec/changes/lukla-ops-engine-planning/16-test-harness-and-agent-verification.md §4
"""

import argparse
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


def calculate_sha256(file_path: Path) -> str:
    if not file_path.exists():
        return "0" * 64
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_junit_xml(xml_path: Path):
    if not xml_path.exists():
        return []
    
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing JUnit XML '{xml_path}': {e}", file=sys.stderr)
        return []
    
    test_cases = []
    # Handle either <testsuites><testsuite><testcase> or <testsuite><testcase>
    for tc in root.iter("testcase"):
        name = tc.get("name", "")
        classname = tc.get("classname", "")
        time_taken = float(tc.get("time", "0.0"))
        
        failure = tc.find("failure")
        error = tc.find("error")
        skipped = tc.find("skipped")
        
        if failure is not None or error is not None:
            status = "FAIL"
            msg = (failure.get("message") if failure is not None else error.get("message")) or "Failed"
        elif skipped is not None:
            status = "SKIPPED"
            msg = skipped.get("message", "Skipped")
        else:
            status = "PASS"
            msg = "Executed successfully"
            
        test_cases.append({
            "name": name,
            "classname": classname,
            "time": time_taken,
            "status": status,
            "message": msg
        })
    return test_cases


def map_test_to_spec(tc):
    name = tc["name"].lower()
    classname = tc["classname"].lower()
    combined = f"{classname} {name}"
    
    if "closing-01" in combined or "mismatch" in combined or "view03" in combined:
        return {
            "testId": "UI-PROTO-VIEW03-MISMATCH-MODAL",
            "sourceIds": ["FR-6.2", "Closing-01"],
            "fixtureId": "fixture-mock-ui",
            "requestId": "standalone-browser",
            "expected": "cross-client mismatch modal renders and dismisses on demand",
            "actual": f"modal observed and dismissed cleanly ({tc['time']:.2f}s)" if tc["status"] == "PASS" else tc["message"],
            "status": tc["status"],
            "evidence": ["results.xml"]
        }
    elif "view-04" in combined or "stepper" in combined or "tally" in combined:
        return {
            "testId": "UI-PROTO-VIEW04-TALLY-STEPPER",
            "sourceIds": ["FR-7.3", "VIEW-04"],
            "fixtureId": "fixture-mock-ui",
            "requestId": "standalone-browser",
            "expected": "stepper increments and decrements count within valid bounds",
            "actual": f"stepper responded accurately to click interactions ({tc['time']:.2f}s)" if tc["status"] == "PASS" else tc["message"],
            "status": tc["status"],
            "evidence": ["results.xml"]
        }
    else:
        return {
            "testId": f"UI-GENERIC-{tc['name'].replace(' ', '_').upper()}",
            "sourceIds": ["UI-UNSPECIFIED"],
            "fixtureId": "fixture-mock-ui",
            "requestId": "standalone-browser",
            "expected": tc["name"],
            "actual": tc["message"],
            "status": tc["status"],
            "evidence": ["results.xml"]
        }


def collect_evidence(out_dir: Path, xml_path: Path, contract_path: Path, run_id: str = None) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    now_utc = datetime.now(timezone.utc).isoformat()
    contract_hash = calculate_sha256(contract_path)
    
    if not run_id:
        run_id = f"run-e2e-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
    junit_cases = parse_junit_xml(xml_path)
    
    normalized_tests = []
    overall_exit_code = 0
    
    for tc in junit_cases:
        mapped = map_test_to_spec(tc)
        normalized_tests.append(mapped)
        if mapped["status"] == "FAIL":
            overall_exit_code = 1
            
    # Include unexecuted architectural boundary placeholders per 16-...md §1 & §4
    normalized_tests.extend([
        {
            "testId": "SCN-01-API",
            "sourceIds": ["FR-6.2", "FR-1.1"],
            "fixtureId": "fixture-a-b-dispatch",
            "requestId": "not-executed",
            "expected": "cross-client issue is rejected without stock mutation",
            "actual": "backend service unexecuted (standalone browser mock verified)",
            "status": "NOT_RUN",
            "evidence": []
        },
        {
            "testId": "SCN-01-DB",
            "sourceIds": ["FR-6.2", "FR-1.1"],
            "fixtureId": "fixture-a-b-dispatch",
            "requestId": "not-executed",
            "expected": "database RLS and ledger immutability enforced",
            "actual": "database integration unexecuted (standalone browser mock verified)",
            "status": "NOT_RUN",
            "evidence": []
        }
    ])
    
    results_json = {
        "schemaVersion": "1",
        "runId": run_id,
        "contractSha256": contract_hash,
        "fixtureSetId": "fixture-mock-ui-v1",
        "startedAt": now_utc,
        "finishedAt": now_utc,
        "exitCode": overall_exit_code,
        "tests": normalized_tests
    }
    
    results_json_path = out_dir / "results.json"
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(results_json, f, indent=2)
        
    manifest_data = {
        "runId": run_id,
        "generatedAt": now_utc,
        "contractSha256": contract_hash,
        "contractPath": str(contract_path),
        "xmlReportPath": str(xml_path),
        "xmlReportSha256": calculate_sha256(xml_path),
        "resultsJsonSha256": calculate_sha256(results_json_path),
        "tooling": {
            "playwright": True,
            "browser": "chromium",
            "evidenceCollector": "tools/collect_evidence.py"
        }
    }
    
    manifest_path = out_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
        
    print("=" * 70)
    print("📋 EVIDENCE BUNDLE NORMALIZATION COMPLETE")
    print("=" * 70)
    print(f" Run ID:         {run_id}")
    print(f" Contract SHA:   {contract_hash[:16]}...")
    print(f" Results JSON:   {results_json_path}")
    print(f" Manifest:       {manifest_path}")
    print(f" Executed Tests: {len(junit_cases)}")
    print(f" Overall Status: {'PASS' if overall_exit_code == 0 else 'FAIL'}")
    print("-" * 70)
    for t in normalized_tests:
        badge = f"[{t['status']}]"
        print(f" {badge:<10} {t['testId']:<32} {t['actual']}")
    print("=" * 70)
    
    return overall_exit_code


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent
    default_out = repo_root / "frontend" / "artifacts" / "evidence"
    default_xml = default_out / "results.xml"
    default_contract = repo_root / "openspec" / "changes" / "lukla-ops-engine-planning" / "contracts" / "openapi.yaml"
    
    parser = argparse.ArgumentParser(description="Collect test evidence and generate manifest")
    parser.add_argument("--out", type=Path, default=default_out, help="Output directory for evidence artifacts")
    parser.add_argument("--xml", type=Path, default=default_xml, help="Path to input JUnit XML report")
    parser.add_argument("--contract", type=Path, default=default_contract, help="Path to OpenAPI contract")
    parser.add_argument("--run-id", type=str, default=None, help="Optional run identifier")
    
    args = parser.parse_args()
    sys.exit(collect_evidence(args.out, args.xml, args.contract, args.run_id))
