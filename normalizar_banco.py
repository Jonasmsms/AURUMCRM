# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('instance/aurum.db')
cur  = conn.cursor()

cur.execute("UPDATE cliente SET etapa='Ativacao' WHERE etapa='Ativação'")
cur.execute("UPDATE cliente SET servico='Gestao Mensal' WHERE servico='Gestão Mensal'")
cur.execute("UPDATE cliente SET servico='Gestao + Setup' WHERE servico='Gestão + Setup'")
conn.commit()

cur.execute('SELECT DISTINCT etapa FROM cliente')
print('Etapas:', [r[0] for r in cur.fetchall()])
cur.execute('SELECT DISTINCT servico FROM cliente')
print('Servicos:', [r[0] for r in cur.fetchall()])
conn.close()
print('OK')
