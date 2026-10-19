#!/usr/bin/env python3
"""Apply an Offline DAoC release's structured db-<version>.json world delta to a SQLite world DB.

Starting with 0.37, upstream ships world changes as a row-level JSON delta (Insert/Update/Delete per
table, keyed by each table's primary key) instead of a full world DB inside a release zip - see its
game-patch zip, file db-<version>.json (db-<version>b.json is the same file for the Sluaghbinder
edition; the world data does not differ by edition).

  apply-release-db-delta.py <db-X.json> <pristine prior-release.sqlite> <out pristine-X.sqlite>

Verifies every Update's "Old" row matches <in.sqlite> exactly before writing (ignoring
LastTimeRowUpdated, a timestamp with no game meaning) - this catches a baseline mismatch before it
silently produces wrong data. Prints per-kind counts and any mismatches found (exits 1 if any).

A "NewTables" entry is only a schema addition (no row data): confirms the table already exists (our
own WorldBuilder creates it from a matching C# DataObject) and otherwise flags it as a real problem
to investigate - a brand new progress/bot table needs a DataObject on our side, not an upstream SQL
CREATE TABLE import.

After this, feed the output into the normal pipeline (see docs/RELEASING.md): regenerate
world/patches/200-*.sql with derive-world-delta.py against it, then verify (patches-only rebuild,
0 tables differ).
"""
import json
import shutil
import sqlite3
import sys

if len(sys.argv) != 4:
    print(__doc__)
    sys.exit(2)

delta_path, in_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

with open(delta_path) as f:
    delta = json.load(f)

shutil.copyfile(in_path, out_path)
conn = sqlite3.connect(out_path)
conn.isolation_level = None
cur = conn.cursor()

mismatches = []
totals = {"insert": 0, "update": 0, "delete": 0}

for t in delta["Tables"]:
    table = t["Table"]
    columns = t["Columns"]
    keys = t["Key"]
    key_idx = [columns.index(k) for k in keys]
    ignore_idx = {i for i, c in enumerate(columns) if c.lower() == "lasttimerowupdated"}
    col_list_quoted = ",".join(f'"{c}"' for c in columns)

    def where_clause(row):
        return " AND ".join(f'"{columns[i]}" = ?' for i in key_idx), [row[i] for i in key_idx]

    for row in t.get("Insert", []):
        placeholders = ",".join("?" for _ in columns)
        cur.execute(f'INSERT INTO "{table}" ({col_list_quoted}) VALUES ({placeholders})', row)
        totals["insert"] += 1

    for entry in t.get("Update", []):
        old, new = entry["Old"], entry["New"]
        where_sql, where_vals = where_clause(old)
        cur.execute(f'SELECT {col_list_quoted} FROM "{table}" WHERE {where_sql}', where_vals)
        current = cur.fetchone()
        if current is None:
            mismatches.append((table, "missing-row", old))
            continue
        current_cmp = [v for i, v in enumerate(current) if i not in ignore_idx]
        old_cmp = [v for i, v in enumerate(old) if i not in ignore_idx]
        if current_cmp != old_cmp:
            mismatches.append((table, "old-row-differs", {"expected": old, "actual": list(current)}))
        set_sql = ",".join(f'"{c}" = ?' for c in columns)
        cur.execute(f'UPDATE "{table}" SET {set_sql} WHERE {where_sql}', new + where_vals)
        totals["update"] += 1

    for row in t.get("Delete", []):
        where_sql, where_vals = where_clause(row)
        cur.execute(f'DELETE FROM "{table}" WHERE {where_sql}', where_vals)
        totals["delete"] += 1

for nt in delta.get("NewTables", []):
    name = nt["Table"]
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    if cur.fetchone() is None:
        mismatches.append((name, "new-table-missing-from-schema",
                            "no matching DataObject on our side yet - add one before re-running"))
    else:
        print(f"NewTables: {name} already exists in schema (from our own DataObject); no row data to apply.")

conn.commit()
conn.execute("VACUUM")
conn.close()

print(f"Applied: {totals['insert']} inserted, {totals['update']} updated, {totals['delete']} deleted")
if mismatches:
    print(f"\n{len(mismatches)} MISMATCH(ES) - investigate before trusting {out_path}:")
    for m in mismatches[:20]:
        print(" ", m)
    sys.exit(1)
print("No mismatches: every Update's 'Old' row matched the input DB exactly before writing.")
