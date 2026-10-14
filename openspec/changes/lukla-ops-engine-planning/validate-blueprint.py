"""Planning-only checks for local OpenAPI 3.1 contracts.

Ceiling: checks references, IDs, path parameters, component schemas and supplied
examples, not full OpenAPI validity, requirement coverage or runtime semantics.
Upgrade: add a full OpenAPI validator and runtime contract tests at implementation.
Registry pattern: https://python-jsonschema.readthedocs.io/en/stable/referencing/
No remote references are fetched. Requires existing PyYAML/jsonschema/referencing.
"""

import argparse
from copy import deepcopy
from pathlib import Path
import re
import sys

try:
    import yaml
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012
except ImportError as exc:
    raise SystemExit(f"Missing validation dependency: {exc.name}. Use an environment with PyYAML, jsonschema and referencing; no packages were installed.")


METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
URI = "urn:lukla:openapi"
DEFAULT = Path(__file__).parent / "contracts" / "openapi.yaml"


def nodes(value, path=""):
    """Walk contract objects, not payload examples that may contain a $ref key."""
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            if key not in {"example", "examples", "default", "enum", "const"}:
                escaped = str(key).replace("~", "~0").replace("/", "~1")
                yield from nodes(child, f"{path}/{escaped}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from nodes(child, f"{path}/{index}")


def resolve(document, value):
    seen = set()
    while isinstance(value, dict) and "$ref" in value:
        ref = value["$ref"]
        if not ref.startswith("#/") or ref in seen:
            raise ValueError(f"Unsupported or cyclic object reference: {ref}")
        seen.add(ref)
        value = document
        for part in ref[2:].split("/"):
            key = part.replace("~1", "/").replace("~0", "~")
            value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def validator(document, pointer):
    registry = Registry().with_resource(
        URI, Resource.from_contents(document, default_specification=DRAFT202012)
    )
    return Draft202012Validator(
        {"$ref": URI + "#" + pointer}, registry=registry, format_checker=FormatChecker()
    )


def check(document):
    errors = []
    counts = {"operations": 0, "refs": 0, "schemas": 0, "examples": 0}
    seen = set()
    for path, item in document["paths"].items():
        for method, op in item.items():
            if method not in METHODS:
                continue
            counts["operations"] += 1
            oid = op.get("operationId")
            if not oid or oid in seen:
                errors.append(f"operationId missing or duplicate: {method} {path}: {oid}")
            seen.add(oid)
            parameters = [resolve(document, p) for p in item.get("parameters", []) + op.get("parameters", [])]
            actual = {p["name"] for p in parameters if p["in"] == "path" and p.get("required") is True}
            if actual != set(re.findall(r"\{([^}]+)\}", path)):
                errors.append(f"Path parameters mismatch: {method} {path}")

    for pointer, node in nodes(document):
        if "$ref" in node:
            counts["refs"] += 1
            try:
                resolve(document, node)
            except (KeyError, ValueError, IndexError, TypeError) as exc:
                errors.append(f"Reference {pointer}: {exc}")
        # Media and parameter examples use a sibling schema. Schema examples
        # live directly on the schema. Named examples resolve Example Objects.
        schema_pointer = pointer + "/schema" if "schema" in node else pointer
        examples = []
        if "example" in node:
            examples.append(node["example"])
        listed = node.get("examples", [])
        if isinstance(listed, list):
            examples.extend(listed)
        elif isinstance(listed, dict):
            for example in listed.values():
                example = resolve(document, example)
                if "externalValue" in example:
                    errors.append(f"External example not checked: {pointer}")
                elif "value" in example:
                    examples.append(example["value"])
        for example in examples:
            counts["examples"] += 1
            for error in validator(document, schema_pointer).iter_errors(example):
                errors.append(f"Example {pointer}: {error.message}")

    for name, schema in document["components"]["schemas"].items():
        counts["schemas"] += 1
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            errors.append(f"Schema {name}: {exc}")
    return errors, counts


def self_test(document):
    baseline, _ = check(document)
    if baseline:
        raise ValueError("Self-test requires a passing contract first")
    for label in ["qc", "tally", "reference", "operation", "path"]:
        changed = deepcopy(document)
        if label in {"qc", "tally"}:
            path = "/qc-inspections" if label == "qc" else "/sewing-tallies"
            data = changed["paths"][path]["post"]["requestBody"]["content"]["application/json"]
            data["example"].pop("assemblyId" if label == "qc" else "pieces")
        elif label == "reference":
            changed["components"]["schemas"]["Broken"] = {"$ref": "#/missing"}
        elif label == "operation":
            changed["paths"]["/qc-inspections"]["post"]["operationId"] = "recordSewingTally"
        else:
            changed["paths"]["/orders/{orderId}"]["get"]["parameters"] = []
        if not check(changed)[0]:
            raise ValueError(f"Negative control failed to detect {label}")
        print(f"NEGATIVE_CONTROL={label}:PASS")

    ids = [f"{i:08d}-1111-4111-8111-111111111111" for i in range(1, 4)]
    request = {
        "effectiveFrom": "2026-10-13", "mealBasis": "VERIFIED_WAGES_PROPOSED",
        "mealBasisPoints": 1200, "mealDistribution": "PROPORTIONAL_PROPOSED",
        "bonusRate": {"amountMinor": 1000, "currency": "IDR"},
        "bonusRecipientIds": ids, "remainderPolicy": "BLOCK_NON_DIVISIBLE",
        "cutoffLocal": "12:00:00", "overheadBasis": "FIRST_PASS_FINISHED_UNITS_PROPOSED",
    }
    response = dict(request, id=ids[0], status="PENDING")
    for name, value in [("FinancialRuleRequest", request), ("FinancialRule", response)]:
        v = validator(document, "/components/schemas/" + name)
        v.validate(value)
        if v.is_valid(dict(value, unexpected=True)):
            raise ValueError(f"{name} accepted an unknown field")
    changed = deepcopy(document)
    changed["components"]["schemas"]["FinancialRule"]["allOf"][0] = {
        "$ref": "#/components/schemas/FinancialRuleRequest"
    }
    if validator(changed, "/components/schemas/FinancialRule").is_valid(response):
        raise ValueError("Closed-base negative control was not rejected")
    print("FINANCIAL_RULE_FIXTURES=PASS; CLOSED_BASE_NEGATIVE_CONTROL=PASS")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", nargs="?", type=Path, default=DEFAULT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        document = yaml.safe_load(args.contract.read_text(encoding="utf-8"))
        errors, counts = check(document)
        for error in errors:
            print("FAIL:", error)
        print(counts)
        if errors:
            return 1
        if args.self_test:
            self_test(document)
        print("CUSTOM_CONTRACT_CHECKS=PASS; SEMANTIC_APPROVAL=NOT_GRANTED")
        return 0
    except Exception as exc:
        print(f"VALIDATION_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())