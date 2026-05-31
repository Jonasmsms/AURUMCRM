import sys
sys.path.insert(0, '.')
from app import app, db, Cliente
from datetime import datetime

# formato: nome_correto, empresa, dia_cobranca, valor, valor_socio
# valor_socio = 0 significa que Gerson não participa desse cliente
dados = [
    # ── Rede Croc/Hot ─────────────────────────────────────────────────────────
    ('Croc Santa Rita',       'Rede Croc/Hot',  1,  500,  200),
    ('Croc Campo Bom',        'Rede Croc/Hot',  1,  500,  200),
    ('Hotfood Canoas',        'Rede Croc/Hot',  3,  800,    0),
    ('Croc Tubarão',          'Rede Croc/Hot',  3,  500,  200),
    ('Croc Sapiranga',        'Rede Croc/Hot',  4,  500,  200),
    ('Croc São Leopoldo',     'Rede Croc/Hot',  4,  500,  200),
    ('Croc Criciúma',         'Rede Croc/Hot',  4,  500,  200),
    ('Croc Bento Gonçalves',  'Rede Croc/Hot',  5,  500,  200),
    ('Croc Novo Hamburgo',    'Rede Croc/Hot',  5, 1000,  450),
    ('Croc Caxias do Sul',    'Rede Croc/Hot',  6,  500,  200),
    ('Croc Torres',           'Rede Croc/Hot',  8, 1000,  400),
    ('Croc Tramandaí',        'Rede Croc/Hot', 12,  500,  200),
    ('Croc Capão da Canoa',   'Rede Croc/Hot', 15,  500,  200),
    ('Croc Hípica',           'Rede Croc/Hot', 18,  600,  250),
    ('Croc Viamão',           'Rede Croc/Hot', 20, 1000,  400),
    ('Croc Porto Alegre',     'Rede Croc/Hot', 21, 1000,  400),
    ('Croc Araranguá',        'Rede Croc/Hot', 27,  500,  200),
    ('Croc São Luís',         'Rede Croc/Hot', 28, 1000,  400),
    ('Croc Esteio',           'Rede Croc/Hot', 28, 1000,  400),
    ('Croc Mário Quintana',   'Rede Croc/Hot', 31,  500,  200),
    ('Croc Osório',           'Rede Croc/Hot', 31,  500,  200),
    ('Croc Biguaçu',          'Rede Croc/Hot',  0,  500,    0),
    ('Croc Imbituba',         'Rede Croc/Hot',  0,  500,    0),

    # ── Clientes individuais ───────────────────────────────────────────────────
    ('Rota do Sol',              '', 9,   600, 300),
    ('Exuberance',               '', 10,  500,   0),
    ('Joyce Tramandaí',          '', 10,  800, 400),
    ('Mauri Semideus',           '', 10,  500,   0),
    ('Love Burguer',             '', 18, 1000, 500),
    ('Açaí da Marcia Cidreira',  '', 25,  400, 200),
    ('Açaí da Marcia Tramandaí', '',  0,  400, 200),
    ('Blinda Cel',               '',  0,  400, 200),
    ('O Alquimista',             '',  0, 1500,   0),
]

# mapa de nomes antigos → novos (para corrigir clientes já importados)
renomear = {
    'Croc Charqueadas':          'Croc Hípica',
    'Croc Canoas':               'Hotfood Canoas',
    'Rota do Farol':             'Rota do Sol',
    'Qalquimista':               'O Alquimista',
    'Love Picados':              'Love Burguer',
    'Quindacell':                'Blinda Cel',
    'Croc Imigrante':            'Croc Imbituba',
    'O Drendi':                  None,  # remover se não está na lista financeira
}

with app.app_context():
    # Renomear/remover clientes com nomes errados
    for nome_antigo, nome_novo in renomear.items():
        c = Cliente.query.filter_by(nome=nome_antigo).first()
        if c:
            if nome_novo is None:
                db.session.delete(c)
                print(f'Removido: {nome_antigo}')
            else:
                c.nome = nome_novo
                print(f'Renomeado: {nome_antigo} -> {nome_novo}')

    db.session.commit()

    # Atualizar ou criar cada cliente
    criados = 0
    atualizados = 0
    for nome, empresa, dia, valor, valor_socio in dados:
        c = Cliente.query.filter_by(nome=nome).first()
        if c:
            c.empresa      = empresa or c.empresa
            c.dia_cobranca = dia if dia else c.dia_cobranca
            c.valor        = valor
            c.valor_socio  = valor_socio
            c.etapa        = 'Ativo'
            c.servico      = 'Gestão Mensal'
            atualizados += 1
        else:
            c = Cliente(
                nome=nome,
                empresa=empresa,
                servico='Gestão Mensal',
                valor=valor,
                valor_socio=valor_socio,
                dia_cobranca=dia if dia else None,
                etapa='Ativo',
                criado_em=datetime.utcnow(),
                atualizado_em=datetime.utcnow(),
            )
            db.session.add(c)
            criados += 1

    db.session.commit()
    total = Cliente.query.count()
    mrr   = sum(c.valor for c in Cliente.query.filter_by(etapa='Ativo').all())
    custo = sum(c.valor_socio for c in Cliente.query.filter_by(etapa='Ativo').all())
    print(f'\nCriados: {criados} | Atualizados: {atualizados}')
    print(f'Total de clientes: {total}')
    print(f'MRR total:         R$ {mrr:,.0f}')
    print(f'Repasse Gerson:    R$ {custo:,.0f}')
    print(f'Lucro líquido:     R$ {mrr - custo:,.0f}')
