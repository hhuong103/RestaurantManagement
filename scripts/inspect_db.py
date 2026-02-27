import sqlite3
import json

DB = 'database.db'

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT id, customer_name, qr_code IS NOT NULL AS has_qr, length(qr_code) as qr_len, substr(qr_code,1,400) as qr_preview FROM orders ORDER BY id DESC LIMIT 10")
rows = c.fetchall()

print('Found', len(rows), 'rows (latest 10):')
for r in rows:
    print('---')
    print('id:', r['id'])
    print('customer:', r['customer_name'])
    print('has_qr:', bool(r['has_qr']))
    print('qr_len:', r['qr_len'])
    preview = r['qr_preview'] if r['qr_preview'] is not None else ''
    print('qr_preview:', preview)

conn.close()
