"""Search state DBs for rules/skills configuration."""
import json
import sqlite3
from pathlib import Path

paths = [
    Path(r"C:\Users\Kellerian\AppData\Roaming\Cursor\User\globalStorage\state.vscdb"),
    Path(
        r"C:\Users\Kellerian\AppData\Roaming\Cursor\User\workspaceStorage"
        r"\2f0e9a2d8520f70a472810f3924b83d4\state.vscdb"
    ),
]
for db in paths:
    print(f"\n######## {db.name} ({db.parent.name}) ########")
    conn = sqlite3.connect(db)
    rows = conn.execute(
        "SELECT key FROM ItemTable WHERE key LIKE '%skill%' OR key LIKE '%rule%' OR key LIKE '%command%' OR key LIKE '%pill%'"
    ).fetchall()
    for (key,) in rows:
        print(key)
