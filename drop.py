import sqlite3
with sqlite3.connect('geo_saas.db') as conn:
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS audit_usage")
    c.execute("DROP TABLE IF EXISTS billing_history")
    conn.commit()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print(c.fetchall())
