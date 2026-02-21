#!/usr/bin/env python3
"""
Generate a dbt manifest.json compatible with Lightdash without needing
a live database connection. Reads models/*.sql and models/schema.yml.
Run from inside the lightdash/ directory.
"""
import json, yaml, uuid, datetime, hashlib
from pathlib import Path

PROJECT = "stockpulse"
DATABASE = "postgres"
SCHEMA   = "public"
DBT_SCHEMA_VERSION = "https://schemas.getdbt.com/dbt/manifest/v12/manifest.json"
DBT_VERSION        = "1.11.6"

root = Path(__file__).parent
models_dir = root / "models"

# Load schema.yml
with open(models_dir / "schema.yml") as f:
    schema = yaml.safe_load(f)

schema_models = {m["name"]: m for m in schema.get("models", [])}

def col_entry(col: dict) -> dict:
    return {
        "name":        col["name"],
        "description": col.get("description", ""),
        "meta":        col.get("meta", {}),
        "data_type":   None,
        "constraints": [],
        "quote":       None,
        "tags":        [],
    }

def node_config():
    return {
        "enabled": True,
        "alias": None,
        "schema": None,
        "database": None,
        "tags": [],
        "meta": {},
        "group": None,
        "materialized": "view",
        "incremental_strategy": None,
        "persist_docs": {},
        "post-hook": [],
        "pre-hook": [],
        "quoting": {},
        "column_types": {},
        "full_refresh": None,
        "unique_key": None,
        "on_schema_change": "ignore",
        "on_configuration_change": "apply",
        "grants": {},
        "packages": [],
        "docs": {"show": True, "node_color": None},
        "contract": {"enforced": False, "alias_types": True},
        "access": "protected",
    }

nodes = {}
for sql_file in sorted(models_dir.glob("*.sql")):
    name = sql_file.stem
    raw_code = sql_file.read_text()
    uid = f"model.{PROJECT}.{name}"

    sm = schema_models.get(name, {})
    cols_yaml = {c["name"]: c for c in sm.get("columns", [])}
    columns = {cn: col_entry(cv) for cn, cv in cols_yaml.items()}

    checksum_val = hashlib.md5(raw_code.encode()).hexdigest()

    nodes[uid] = {
        "database":            DATABASE,
        "schema":              SCHEMA,
        "name":                name,
        "resource_type":       "model",
        "package_name":        PROJECT,
        "path":                f"{name}.sql",
        "original_file_path":  f"models/{name}.sql",
        "unique_id":           uid,
        "fqn":                 [PROJECT, name],
        "alias":               name,
        "checksum":            {"name": "md5", "checksum": checksum_val},
        "config":              node_config(),
        "tags":                [],
        "description":         sm.get("description", ""),
        "columns":             columns,
        "meta":                {},
        "group":               None,
        "docs":                {"show": True, "node_color": None},
        "patch_path":          f"{PROJECT}://models/schema.yml",
        "build_path":          None,
        "deferred":            False,
        "unrendered_config":   {"materialized": "view", "schema": SCHEMA},
        "created_at":          datetime.datetime.utcnow().timestamp(),
        "relation_name":       f'"{DATABASE}"."{SCHEMA}"."{name}"',
        "raw_code":            raw_code,
        "language":            "sql",
        "refs":                [],
        "sources":             [],
        "metrics":             [],
        "depends_on":          {"macros": [], "nodes": []},
        "compiled_path":       None,
        "compiled":            True,
        "compiled_code":       raw_code,
        "extra_ctes_injected": False,
        "extra_ctes":          [],
        "contract":            {"enforced": False, "alias_types": True, "checksum": None},
        "access":              "protected",
        "constraints":         [],
        "version":             None,
        "latest_version":      None,
        "deprecation_date":    None,
    }

manifest = {
    "metadata": {
        "dbt_schema_version": DBT_SCHEMA_VERSION,
        "dbt_version":        DBT_VERSION,
        "generated_at":       datetime.datetime.utcnow().isoformat() + "Z",
        "invocation_id":      str(uuid.uuid4()),
        "env":                {},
    },
    "nodes":         nodes,
    "sources":       {},
    "macros":        {},
    "docs":          {},
    "exposures":     {},
    "metrics":       {},
    "groups":        {},
    "selectors":     {},
    "disabled":      {},
    "parent_map":    {uid: [] for uid in nodes},
    "child_map":     {uid: [] for uid in nodes},
    "group_map":     {},
    "saved_queries": {},
    "semantic_models": {},
    "unit_tests":    {},
}

target_dir = root / "target"
target_dir.mkdir(exist_ok=True)
out = target_dir / "manifest.json"
out.write_text(json.dumps(manifest, indent=2))
print(f"Written {len(nodes)} models to {out}")
for n in sorted(nodes):
    print(f"  ✓ {n}")
