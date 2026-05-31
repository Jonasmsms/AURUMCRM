# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aurum.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'aurum2026'

db = SQLAlchemy(app)

# ── Models ────────────────────────────────────────────────────────────────────

ETAPAS   = ['Acesso', 'Dados', 'Contrato', 'Assinatura', 'Ativacao', 'Ativo', 'Cancelado']
ETAPAS_DISPLAY = {
    'Acesso': 'Acesso', 'Dados': 'Dados', 'Contrato': 'Contrato',
    'Assinatura': 'Assinatura', 'Ativacao': 'Ativação', 'Ativo': 'Ativo', 'Cancelado': 'Cancelado'
}
SERVICOS = ['Gestao Mensal', 'Setup Menu', 'Gestao + Setup']
SERVICOS_DISPLAY = {
    'Gestao Mensal': 'Gestão Mensal',
    'Setup Menu': 'Setup Menu',
    'Gestao + Setup': 'Gestão + Setup',
}

class Cliente(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    nome          = db.Column(db.String(120), nullable=False)
    empresa       = db.Column(db.String(120))
    telefone      = db.Column(db.String(30))
    email         = db.Column(db.String(120))
    servico       = db.Column(db.String(50))
    valor         = db.Column(db.Float, default=0)
    valor_socio   = db.Column(db.Float, default=0)
    dia_cobranca  = db.Column(db.Integer)
    etapa         = db.Column(db.String(30), default='Acesso')
    responsavel   = db.Column(db.String(80))
    notas         = db.Column(db.Text)
    criado_em     = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow)
    tarefas       = db.relationship('Tarefa',   backref='cliente', lazy=True, cascade='all, delete-orphan')
    historico     = db.relationship('Historico', backref='cliente', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':           self.id,
            'nome':         self.nome or '',
            'empresa':      self.empresa or '',
            'telefone':     self.telefone or '',
            'email':        self.email or '',
            'servico':      self.servico or '',
            'valor':        self.valor or 0,
            'valor_socio':  self.valor_socio or 0,
            'dia_cobranca': self.dia_cobranca or '',
            'etapa':        self.etapa or '',
            'responsavel':  self.responsavel or '',
            'notas':        self.notas or '',
        }

class Tarefa(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    cliente_id  = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    titulo      = db.Column(db.String(200), nullable=False)
    descricao   = db.Column(db.Text)
    responsavel = db.Column(db.String(80))
    prazo       = db.Column(db.Date)
    status      = db.Column(db.String(20), default='pendente')
    criado_em   = db.Column(db.DateTime, default=datetime.utcnow)

class Historico(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    descricao  = db.Column(db.Text, nullable=False)
    criado_em  = db.Column(db.DateTime, default=datetime.utcnow)

# ── Helpers ───────────────────────────────────────────────────────────────────

def registrar_historico(cliente_id, descricao):
    db.session.add(Historico(cliente_id=cliente_id, descricao=descricao))

def _val(c, field):
    v = getattr(c, field, None)
    return v if v is not None else 0

# ── Routes: páginas ───────────────────────────────────────────────────────────

@app.route('/')
def dashboard():
    clientes = Cliente.query.all()
    hoje = date.today()

    por_etapa = {e: 0 for e in ETAPAS}
    for c in clientes:
        if c.etapa in por_etapa:
            por_etapa[c.etapa] += 1

    ativos  = [c for c in clientes if c.etapa == 'Ativo']
    mrr     = sum(_val(c, 'valor')       for c in ativos)
    repasse = sum(_val(c, 'valor_socio') for c in ativos)
    lucro   = mrr - repasse

    tarefas_hoje = Tarefa.query.filter(
        Tarefa.prazo == hoje,
        Tarefa.status != 'concluida'
    ).all()

    tarefas_atrasadas = Tarefa.query.filter(
        Tarefa.prazo < hoje,
        Tarefa.status != 'concluida'
    ).all()

    return render_template('dashboard.html',
        clientes=clientes, por_etapa=por_etapa, etapas=ETAPAS,
        mrr=mrr, repasse=repasse, lucro=lucro,
        tarefas_hoje=tarefas_hoje, tarefas_atrasadas=tarefas_atrasadas, hoje=hoje,
    )

@app.route('/funil')
def funil():
    etapas_funil = [e for e in ETAPAS if e != 'Cancelado']
    clientes = Cliente.query.filter(Cliente.etapa != 'Cancelado').all()
    por_etapa = {e: [] for e in etapas_funil}
    for c in clientes:
        if c.etapa in por_etapa:
            por_etapa[c.etapa].append(c)
    return render_template('funil.html', por_etapa=por_etapa, etapas=etapas_funil,
                           etapas_display=ETAPAS_DISPLAY)

@app.route('/clientes')
def clientes():
    q     = request.args.get('q', '')
    etapa = request.args.get('etapa', '')
    query = Cliente.query
    if q:
        query = query.filter(
            db.or_(Cliente.nome.ilike(f'%{q}%'), Cliente.empresa.ilike(f'%{q}%'))
        )
    if etapa:
        query = query.filter(Cliente.etapa == etapa)
    lista = query.order_by(Cliente.dia_cobranca.asc().nullslast(), Cliente.nome.asc()).all()
    return render_template('clientes.html', clientes=lista, etapas=ETAPAS,
                           etapas_display=ETAPAS_DISPLAY, servicos=SERVICOS,
                           servicos_display=SERVICOS_DISPLAY, q=q, etapa_filtro=etapa)

@app.route('/clientes/novo', methods=['GET', 'POST'])
def novo_cliente():
    if request.method == 'POST':
        c = Cliente(
            nome         = request.form['nome'],
            empresa      = request.form.get('empresa', '').strip() or None,
            telefone     = request.form.get('telefone', '').strip() or None,
            email        = request.form.get('email', '').strip() or None,
            servico      = request.form.get('servico') or None,
            valor        = float(request.form.get('valor') or 0),
            valor_socio  = float(request.form.get('valor_socio') or 0),
            dia_cobranca = int(request.form.get('dia_cobranca') or 0) or None,
            etapa        = request.form.get('etapa', 'Acesso'),
            responsavel  = request.form.get('responsavel', '').strip() or None,
            notas        = request.form.get('notas', '').strip() or None,
        )
        db.session.add(c)
        db.session.flush()
        registrar_historico(c.id, 'Cliente criado na etapa "' + c.etapa + '"')
        db.session.commit()
        return redirect(url_for('cliente_detalhe', id=c.id))
    return render_template('form_cliente.html', cliente=None, etapas=ETAPAS,
                           etapas_display=ETAPAS_DISPLAY, servicos=SERVICOS,
                           servicos_display=SERVICOS_DISPLAY)

@app.route('/clientes/<int:id>')
def cliente_detalhe(id):
    c         = Cliente.query.get_or_404(id)
    tarefas   = Tarefa.query.filter_by(cliente_id=id).order_by(
                    Tarefa.prazo.asc().nullslast(), Tarefa.id.asc()).all()
    historico = Historico.query.filter_by(cliente_id=id).order_by(Historico.criado_em.desc()).all()
    hoje = date.today()
    return render_template('cliente_detalhe.html', c=c, tarefas=tarefas, historico=historico,
                           etapas=ETAPAS, etapas_display=ETAPAS_DISPLAY,
                           servicos=SERVICOS, servicos_display=SERVICOS_DISPLAY, hoje=hoje)

@app.route('/clientes/<int:id>/editar', methods=['GET', 'POST'])
def editar_cliente(id):
    c = Cliente.query.get_or_404(id)
    next_url = request.args.get('next') or request.form.get('next') or url_for('cliente_detalhe', id=id)
    if request.method == 'POST':
        etapa_anterior = c.etapa
        c.nome         = request.form['nome']
        c.empresa      = request.form.get('empresa', '').strip() or None
        c.telefone     = request.form.get('telefone', '').strip() or None
        c.email        = request.form.get('email', '').strip() or None
        c.servico      = request.form.get('servico') or None
        c.valor        = float(request.form.get('valor') or 0)
        c.valor_socio  = float(request.form.get('valor_socio') or 0)
        c.dia_cobranca = int(request.form.get('dia_cobranca') or 0) or None
        c.etapa        = request.form.get('etapa', c.etapa)
        c.responsavel  = request.form.get('responsavel', '').strip() or None
        c.notas        = request.form.get('notas', '').strip() or None
        c.atualizado_em = datetime.utcnow()
        if etapa_anterior != c.etapa:
            registrar_historico(c.id, 'Etapa: "' + etapa_anterior + '" para "' + c.etapa + '"')
        db.session.commit()
        return redirect(next_url)
    return render_template('form_cliente.html', cliente=c, etapas=ETAPAS,
                           etapas_display=ETAPAS_DISPLAY, servicos=SERVICOS,
                           servicos_display=SERVICOS_DISPLAY, next_url=next_url)

@app.route('/clientes/<int:id>/deletar', methods=['POST'])
def deletar_cliente(id):
    c = Cliente.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return redirect(url_for('clientes'))

# ── API ───────────────────────────────────────────────────────────────────────

@app.route('/api/cliente/<int:id>')
def api_cliente(id):
    c = Cliente.query.get_or_404(id)
    return jsonify(c.to_dict())

@app.route('/api/cliente/<int:id>/etapa', methods=['POST'])
def atualizar_etapa(id):
    c = Cliente.query.get_or_404(id)
    data = request.get_json()
    nova_etapa = data.get('etapa')
    if nova_etapa not in ETAPAS:
        return jsonify({'erro': 'Etapa invalida'}), 400
    etapa_anterior = c.etapa
    c.etapa = nova_etapa
    c.atualizado_em = datetime.utcnow()
    registrar_historico(c.id, 'Etapa: "' + etapa_anterior + '" para "' + nova_etapa + '"')
    db.session.commit()
    return jsonify({'ok': True, 'etapa': c.etapa})

# ── Tarefas ───────────────────────────────────────────────────────────────────

@app.route('/clientes/<int:id>/tarefas/nova', methods=['POST'])
def nova_tarefa(id):
    Cliente.query.get_or_404(id)
    prazo_str = request.form.get('prazo', '').strip()
    prazo = None
    if prazo_str:
        try:
            prazo = datetime.strptime(prazo_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    titulo = request.form.get('titulo', '').strip()
    if not titulo:
        return redirect(url_for('cliente_detalhe', id=id))
    t = Tarefa(
        cliente_id  = id,
        titulo      = titulo,
        descricao   = request.form.get('descricao', '').strip() or None,
        responsavel = request.form.get('responsavel', '').strip() or None,
        prazo       = prazo,
    )
    db.session.add(t)
    db.session.commit()
    return redirect(url_for('cliente_detalhe', id=id))

@app.route('/tarefas/<int:id>/status', methods=['POST'])
def atualizar_status_tarefa(id):
    t = Tarefa.query.get_or_404(id)
    novo = request.form.get('status', t.status)
    if novo in ('pendente', 'em_andamento', 'concluida'):
        t.status = novo
        db.session.commit()
    return redirect(url_for('cliente_detalhe', id=t.cliente_id))

@app.route('/tarefas/<int:id>/deletar', methods=['POST'])
def deletar_tarefa(id):
    t = Tarefa.query.get_or_404(id)
    cid = t.cliente_id
    db.session.delete(t)
    db.session.commit()
    return redirect(url_for('cliente_detalhe', id=cid))

@app.route('/tarefas')
def todas_tarefas():
    hoje    = date.today()
    tarefas = Tarefa.query.filter(Tarefa.status != 'concluida').order_by(
                  Tarefa.prazo.asc().nullslast(), Tarefa.id.asc()).all()
    return render_template('tarefas.html', tarefas=tarefas, hoje=hoje)

# ── Historico ─────────────────────────────────────────────────────────────────

@app.route('/clientes/<int:id>/historico', methods=['POST'])
def add_historico(id):
    Cliente.query.get_or_404(id)
    descricao = request.form.get('descricao', '').strip()
    if descricao:
        registrar_historico(id, descricao)
        db.session.commit()
    return redirect(url_for('cliente_detalhe', id=id))

# ── Init ──────────────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
