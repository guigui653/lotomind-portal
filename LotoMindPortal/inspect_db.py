import sqlite3
conn = sqlite3.connect('instance/lotomind.db')
cursor = conn.cursor()
tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tabelas:", tables)
for t in tables:
    count = cursor.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {count} registros")
    # Mostrar 2 exemplos
    rows = cursor.execute(f"SELECT * FROM {t} LIMIT 2").fetchall()
    cols = [d[0] for d in cursor.description]
    print(f"    Colunas: {cols}")
    for r in rows:
        print(f"    → {r}")
conn.close()
