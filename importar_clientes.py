import sys
sys.path.insert(0, '.')
from app import app, db, Cliente
from datetime import datetime

clientes_data = [
    # ── Rede Croc/Hot ─────────────────────────────────────────────────────────
    {'nome': 'Croc Esteio',           'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Campo Bom',        'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Santa Rita',       'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Sapiranga',        'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc São Leopoldo',     'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Novo Hamburgo',    'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Caxias do Sul',    'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Torres',           'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Tramandaí',        'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Capão da Canoa',   'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Charqueadas',      'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Viamão',           'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Porto Alegre',     'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Araranguá',        'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc São Luís',         'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Mário Quintana',   'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Osório',           'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Biguaçu',          'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Imigrante',        'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Canoas',           'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Tubarão',          'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Criciúma',         'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Croc Bento Gonçalves',  'empresa': 'Rede Croc/Hot', 'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},

    # ── Clientes individuais ───────────────────────────────────────────────────
    {'nome': 'Rota do Farol',              'empresa': '',  'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Joyce Tramandaí',            'empresa': '',  'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Açaí da Marcia Cidreira',    'empresa': '',  'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Açaí da Marcia Tramandaí',   'empresa': '',  'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Quindacell',                 'empresa': '',  'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Qalquimista',                'empresa': '',  'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'Love Picados',               'empresa': '',  'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
    {'nome': 'O Drendi',                   'empresa': '',  'servico': 'Gestão Mensal', 'valor': 500, 'etapa': 'Ativo'},
]

with app.app_context():
    count = 0
    for d in clientes_data:
        existe = Cliente.query.filter_by(nome=d['nome']).first()
        if not existe:
            c = Cliente(
                nome=d['nome'],
                empresa=d.get('empresa', ''),
                servico=d['servico'],
                valor=d['valor'],
                etapa=d['etapa'],
                criado_em=datetime.utcnow(),
                atualizado_em=datetime.utcnow(),
            )
            db.session.add(c)
            count += 1
    db.session.commit()
    print(f'{count} clientes importados com sucesso.')
    total = Cliente.query.count()
    print(f'Total no banco: {total} clientes')
