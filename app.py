# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, stream_with_context, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas as pdfcanvas
from dotenv import load_dotenv
import os, requests as req_lib, json

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:818787818181jJ.@db.lehfjqlicmzrkuzjuupt.supabase.co:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'aurum2026'

db = SQLAlchemy(app)

ETAPAS = ['Acesso', 'Dados', 'Contrato', 'Assinatura', 'Ativacao', 'Ativo', 'Cancelado']
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

DIAS_SEMANA = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']
DIAS_DISPLAY = {
    'segunda': 'Segunda', 'terca': 'Terça', 'quarta': 'Quarta',
    'quinta': 'Quinta', 'sexta': 'Sexta', 'sabado': 'Sábado', 'domingo': 'Domingo'
}

PLATAFORMAS_LOGIN = [
    ('instagram',  'Instagram'),
    ('facebook',   'Facebook (pessoal)'),
    ('maps',       'Google Maps'),
    ('ifood',      'iFood'),
    ('saipos',     'Saipos'),
    ('brendi',     'Brendi'),
    ('app99food',  '99Food'),
]


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
    cnpj          = db.Column(db.String(20))
    whatsapp      = db.Column(db.String(30))
    obs_whatsapp  = db.Column(db.Text)
    instagram     = db.Column(db.String(120))
    obs_instagram = db.Column(db.Text)
    facebook      = db.Column(db.String(120))
    obs_facebook  = db.Column(db.Text)
    google_maps   = db.Column(db.String(255))
    obs_google_maps = db.Column(db.Text)
    ifood         = db.Column(db.String(255))
    obs_ifood     = db.Column(db.Text)
    google_drive  = db.Column(db.String(255))
    criado_em     = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow)
    tarefas       = db.relationship('Tarefa',   backref='cliente', lazy=True, cascade='all, delete-orphan')
    historico     = db.relationship('Historico', backref='cliente', lazy=True, cascade='all, delete-orphan')

    # Novos campos
    emails_rede       = db.Column(db.Text)
    instagram_login   = db.Column(db.String(120))
    instagram_senha   = db.Column(db.String(120))
    facebook_login    = db.Column(db.String(120))
    facebook_senha    = db.Column(db.String(120))
    maps_login        = db.Column(db.String(120))
    maps_senha        = db.Column(db.String(120))
    ifood_login       = db.Column(db.String(120))
    ifood_senha       = db.Column(db.String(120))
    saipos_login      = db.Column(db.String(120))
    saipos_senha      = db.Column(db.String(120))
    brendi_login      = db.Column(db.String(120))
    brendi_senha      = db.Column(db.String(120))
    app99food_login   = db.Column(db.String(120))
    app99food_senha   = db.Column(db.String(120))
    horario_segunda_abertura    = db.Column(db.String(10))
    horario_segunda_fechamento  = db.Column(db.String(10))
    horario_terca_abertura      = db.Column(db.String(10))
    horario_terca_fechamento    = db.Column(db.String(10))
    horario_quarta_abertura     = db.Column(db.String(10))
    horario_quarta_fechamento   = db.Column(db.String(10))
    horario_quinta_abertura     = db.Column(db.String(10))
    horario_quinta_fechamento   = db.Column(db.String(10))
    horario_sexta_abertura      = db.Column(db.String(10))
    horario_sexta_fechamento    = db.Column(db.String(10))
    horario_sabado_abertura     = db.Column(db.String(10))
    horario_sabado_fechamento   = db.Column(db.String(10))
    horario_domingo_abertura    = db.Column(db.String(10))
    horario_domingo_fechamento  = db.Column(db.String(10))
    cardapio_link   = db.Column(db.String(500))
    cardapio_dados  = db.Column(db.Text)
    instagram_dados = db.Column(db.Text)   # JSON com bio, posts, hashtags
    endereco        = db.Column(db.String(255))
    logo_path       = db.Column(db.String(255))

    @property
    def pontuacao(self):
        # 10 campos obrigatórios — 1 ponto cada
        campos = [
            self.empresa,
            self.telefone,
            self.email,
            self.servico,
            self.dia_cobranca,
            self.cnpj,
            self.responsavel,
            self.google_drive,
            self.emails_rede,
            self.horario_segunda_abertura or self.horario_terca_abertura or
            self.horario_quarta_abertura  or self.horario_quinta_abertura or
            self.horario_sexta_abertura   or self.horario_sabado_abertura or
            self.horario_domingo_abertura,
        ]
        return sum(1 for c in campos if c)

    def to_dict(self):
        d = {
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
            'cnpj':             self.cnpj or '',
            'whatsapp':         self.whatsapp or '',
            'obs_whatsapp':     self.obs_whatsapp or '',
            'instagram':        self.instagram or '',
            'obs_instagram':    self.obs_instagram or '',
            'facebook':         self.facebook or '',
            'obs_facebook':     self.obs_facebook or '',
            'google_maps':      self.google_maps or '',
            'obs_google_maps':  self.obs_google_maps or '',
            'ifood':            self.ifood or '',
            'obs_ifood':        self.obs_ifood or '',
            'google_drive':     self.google_drive or '',
            'emails_rede':      self.emails_rede or '',
            'instagram_login':  self.instagram_login or '',
            'instagram_senha':  self.instagram_senha or '',
            'facebook_login':   self.facebook_login or '',
            'facebook_senha':   self.facebook_senha or '',
            'maps_login':       self.maps_login or '',
            'maps_senha':       self.maps_senha or '',
            'ifood_login':      self.ifood_login or '',
            'ifood_senha':      self.ifood_senha or '',
            'saipos_login':     self.saipos_login or '',
            'saipos_senha':     self.saipos_senha or '',
            'brendi_login':     self.brendi_login or '',
            'brendi_senha':     self.brendi_senha or '',
            'app99food_login':  self.app99food_login or '',
            'app99food_senha':  self.app99food_senha or '',
            'cardapio_link':    self.cardapio_link or '',
            'cardapio_dados':   self.cardapio_dados or '',
            'endereco':         self.endereco or '',
        }
        for dia in DIAS_SEMANA:
            d[f'horario_{dia}_abertura']    = getattr(self, f'horario_{dia}_abertura') or ''
            d[f'horario_{dia}_fechamento']  = getattr(self, f'horario_{dia}_fechamento') or ''
        return d


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

class ChatMensagem(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    role       = db.Column(db.String(20), nullable=False)   # user | assistant
    conteudo   = db.Column(db.Text, nullable=False)
    tipo       = db.Column(db.String(20), default='texto')  # texto | imagem
    criado_em  = db.Column(db.DateTime, default=datetime.utcnow)


def registrar_historico(cliente_id, descricao):
    db.session.add(Historico(cliente_id=cliente_id, descricao=descricao))

def _val(c, field):
    v = getattr(c, field, None)
    return v if v is not None else 0

def _campos_novos(form):
    d = dict(emails_rede=form.get('emails_rede', '').strip() or None)
    for plat, _ in PLATAFORMAS_LOGIN:
        d[f'{plat}_login'] = form.get(f'{plat}_login', '').strip() or None
        d[f'{plat}_senha'] = form.get(f'{plat}_senha', '').strip() or None
    for dia in DIAS_SEMANA:
        d[f'horario_{dia}_abertura']   = form.get(f'horario_{dia}_abertura', '').strip() or None
        d[f'horario_{dia}_fechamento'] = form.get(f'horario_{dia}_fechamento', '').strip() or None
    return d


@app.route('/')
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
        novos = _campos_novos(request.form)
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
            cnpj            = request.form.get('cnpj', '').strip() or None,
            whatsapp        = request.form.get('whatsapp', '').strip() or None,
            obs_whatsapp    = request.form.get('obs_whatsapp', '').strip() or None,
            instagram       = request.form.get('instagram', '').strip() or None,
            obs_instagram   = request.form.get('obs_instagram', '').strip() or None,
            facebook        = request.form.get('facebook', '').strip() or None,
            obs_facebook    = request.form.get('obs_facebook', '').strip() or None,
            google_maps     = request.form.get('google_maps', '').strip() or None,
            obs_google_maps = request.form.get('obs_google_maps', '').strip() or None,
            ifood           = request.form.get('ifood', '').strip() or None,
            obs_ifood       = request.form.get('obs_ifood', '').strip() or None,
            google_drive    = request.form.get('google_drive', '').strip() or None,
            cardapio_link   = request.form.get('cardapio_link', '').strip() or None,
            endereco        = request.form.get('endereco', '').strip() or None,
            **novos,
        )
        db.session.add(c)
        db.session.flush()
        registrar_historico(c.id, 'Cliente criado na etapa "' + c.etapa + '"')
        db.session.commit()
        return redirect(url_for('cliente_detalhe', id=c.id))
    return render_template('form_cliente.html', cliente=None, etapas=ETAPAS,
                           etapas_display=ETAPAS_DISPLAY, servicos=SERVICOS,
                           servicos_display=SERVICOS_DISPLAY,
                           dias_semana=DIAS_SEMANA, dias_display=DIAS_DISPLAY,
                           plataformas_login=PLATAFORMAS_LOGIN)

@app.route('/clientes/<int:id>')
def cliente_detalhe(id):
    c    = db.get_or_404(Cliente, id)
    hoje = date.today()
    return render_template('cliente_detalhe.html', c=c,
                           etapas=ETAPAS, etapas_display=ETAPAS_DISPLAY,
                           servicos=SERVICOS, servicos_display=SERVICOS_DISPLAY, hoje=hoje)

@app.route('/clientes/<int:id>/editar', methods=['GET', 'POST'])
def editar_cliente(id):
    c = db.get_or_404(Cliente, id)
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
        c.cnpj            = request.form.get('cnpj', '').strip() or None
        c.whatsapp        = request.form.get('whatsapp', '').strip() or None
        c.obs_whatsapp    = request.form.get('obs_whatsapp', '').strip() or None
        c.instagram       = request.form.get('instagram', '').strip() or None
        c.obs_instagram   = request.form.get('obs_instagram', '').strip() or None
        c.facebook        = request.form.get('facebook', '').strip() or None
        c.obs_facebook    = request.form.get('obs_facebook', '').strip() or None
        c.google_maps     = request.form.get('google_maps', '').strip() or None
        c.obs_google_maps = request.form.get('obs_google_maps', '').strip() or None
        c.ifood           = request.form.get('ifood', '').strip() or None
        c.obs_ifood       = request.form.get('obs_ifood', '').strip() or None
        c.google_drive    = request.form.get('google_drive', '').strip() or None
        c.cardapio_link   = request.form.get('cardapio_link', '').strip() or None
        c.endereco        = request.form.get('endereco', '').strip() or None
        for k, v in _campos_novos(request.form).items():
            setattr(c, k, v)
        c.atualizado_em = datetime.utcnow()
        if etapa_anterior != c.etapa:
            registrar_historico(c.id, 'Etapa: "' + etapa_anterior + '" para "' + c.etapa + '"')
        db.session.commit()
        return redirect(next_url)
    return render_template('form_cliente.html', cliente=c, etapas=ETAPAS,
                           etapas_display=ETAPAS_DISPLAY, servicos=SERVICOS,
                           servicos_display=SERVICOS_DISPLAY, next_url=next_url,
                           dias_semana=DIAS_SEMANA, dias_display=DIAS_DISPLAY,
                           plataformas_login=PLATAFORMAS_LOGIN)

@app.route('/clientes/<int:id>/deletar', methods=['POST'])
def deletar_cliente(id):
    c = db.get_or_404(Cliente, id)
    db.session.delete(c)
    db.session.commit()
    return redirect(url_for('clientes'))

@app.route('/api/cliente/<int:id>')
def api_cliente(id):
    c = db.get_or_404(Cliente, id)
    return jsonify(c.to_dict())

@app.route('/api/cliente/<int:id>/etapa', methods=['POST'])
def atualizar_etapa(id):
    c = db.get_or_404(Cliente, id)
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

@app.route('/clientes/<int:id>/historico', methods=['POST'])
def add_historico(id):
    db.get_or_404(Cliente, id)
    descricao = request.form.get('descricao', '').strip()
    if descricao:
        registrar_historico(id, descricao)
        db.session.commit()
    return redirect(url_for('cliente_detalhe', id=id))

@app.route('/clientes/<int:id>/pdf')
def cliente_pdf(id):
    c = db.get_or_404(Cliente, id)

    # ── Paleta ──────────────────────────────────────────────────────────
    GOLD        = colors.HexColor('#c9a84c')
    GOLD_LIGHT  = colors.HexColor('#f5f0e0')
    DARK        = colors.HexColor('#1a1a1a')
    DARK2       = colors.HexColor('#2c2c2c')
    GREY_BG     = colors.HexColor('#f4f4f4')
    BORDER      = colors.HexColor('#ddd8cc')
    TEXT_DIM    = colors.HexColor('#555555')
    WHITE       = colors.white

    PAGE_W, PAGE_H = A4
    ML = 2*cm; MR = 2*cm; MT = 4.2*cm; MB = 2.2*cm
    CW = PAGE_W - ML - MR  # largura útil

    # ── Estilos ─────────────────────────────────────────────────────────
    base = getSampleStyleSheet()
    def sty(name, **kw):
        return ParagraphStyle(name, parent=base['Normal'], **kw)

    s_normal  = sty('N',  fontSize=9,  leading=13, textColor=DARK2)
    s_label   = sty('L',  fontSize=8,  leading=11, textColor=TEXT_DIM, fontName='Helvetica-Bold')
    s_value   = sty('V',  fontSize=9,  leading=13, textColor=DARK2)
    s_section = sty('S',  fontSize=10, leading=14, textColor=DARK,
                    fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=4)
    s_footer  = sty('F',  fontSize=7.5, textColor=TEXT_DIM, alignment=TA_CENTER)

    # ── Cabeçalho e rodapé via canvas ───────────────────────────────────
    nome_display    = c.nome or '-'
    empresa_display = c.empresa or ''
    gerado_em       = datetime.now().strftime('%d/%m/%Y  %H:%M')

    def header_footer(canv, doc):
        canv.saveState()
        # Faixa superior escura
        canv.setFillColor(DARK)
        canv.rect(0, PAGE_H - 2.8*cm, PAGE_W, 2.8*cm, fill=1, stroke=0)
        # Linha dourada fina abaixo do cabeçalho
        canv.setFillColor(GOLD)
        canv.rect(0, PAGE_H - 2.85*cm, PAGE_W, 0.05*cm, fill=1, stroke=0)
        # Marca AURUM CRM
        canv.setFont('Helvetica-Bold', 11)
        canv.setFillColor(GOLD)
        canv.drawString(ML, PAGE_H - 1.3*cm, 'AURUM')
        canv.setFont('Helvetica', 11)
        canv.setFillColor(colors.HexColor('#aaaaaa'))
        canv.drawString(ML + 1.55*cm, PAGE_H - 1.3*cm, 'CRM')
        # Nome do cliente
        canv.setFont('Helvetica-Bold', 13)
        canv.setFillColor(WHITE)
        canv.drawString(ML, PAGE_H - 2.1*cm, nome_display)
        if empresa_display:
            canv.setFont('Helvetica', 9)
            canv.setFillColor(colors.HexColor('#bbbbbb'))
            canv.drawString(ML, PAGE_H - 2.55*cm, empresa_display)
        # Número de página (dir)
        canv.setFont('Helvetica', 8)
        canv.setFillColor(colors.HexColor('#888888'))
        canv.drawRightString(PAGE_W - MR, PAGE_H - 1.3*cm,
                             f'Pág. {doc.page}')
        # Rodapé
        canv.setFillColor(BORDER)
        canv.rect(ML, 1.4*cm, CW, 0.03*cm, fill=1, stroke=0)
        canv.setFont('Helvetica', 7.5)
        canv.setFillColor(TEXT_DIM)
        canv.drawString(ML, 1.0*cm, f'Gerado em {gerado_em}   •   AURUM CRM')
        canv.drawRightString(PAGE_W - MR, 1.0*cm, 'Documento confidencial')
        canv.restoreState()

    # ── Funções auxiliares ───────────────────────────────────────────────
    def section_title(txt):
        t = Table([['', Paragraph(txt.upper(), s_section)]],
                  colWidths=[0.3*cm, CW - 0.3*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (0,-1), GOLD),
            ('LEFTPADDING',   (0,0), (-1,-1), 0),
            ('RIGHTPADDING',  (0,0), (-1,-1), 0),
            ('TOPPADDING',    (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING',   (1,0), (1,-1), 8),
            ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ]))
        return t

    def info_table(rows, col1=4.5*cm):
        data = []
        for k, v in rows:
            if not v:
                continue
            data.append([Paragraph(k, s_label), Paragraph(str(v), s_value)])
        if not data:
            return Spacer(1, 1)
        t = Table(data, colWidths=[col1, CW - col1])
        t.setStyle(TableStyle([
            ('ROWBACKGROUNDS', (0,0), (-1,-1), [WHITE, GREY_BG]),
            ('LINEBELOW',  (0,0), (-1,-1), 0.3, BORDER),
            ('VALIGN',     (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING',(0,0), (-1,-1), 8),
            ('RIGHTPADDING',(0,0),(-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING',(0,0),(-1,-1), 6),
            ('BACKGROUND', (0,0), (0,-1), GOLD_LIGHT),
        ]))
        return t

    def badge_etapa(etapa):
        cores_etapa = {
            'Acesso': '#3498db', 'Dados': '#9b59b6', 'Contrato': '#e67e22',
            'Assinatura': '#e74c3c', 'Ativacao': '#f39c12',
            'Ativo': '#27ae60', 'Cancelado': '#95a5a6',
        }
        cor = cores_etapa.get(etapa, '#888')
        return f'<font color="{cor}"><b>{ETAPAS_DISPLAY.get(etapa, etapa)}</b></font>'

    # ── Conteúdo ─────────────────────────────────────────────────────────
    elements = []

    # Card de resumo no topo
    pts = c.pontuacao
    pts_cor = '#27ae60' if pts >= 8 else ('#f0a500' if pts >= 5 else '#e74c3c')
    col_w = CW / 4
    s_card_label = sty('CL', fontSize=7.5, textColor=TEXT_DIM, fontName='Helvetica-Bold')
    s_card_value = sty('CV', fontSize=10,  textColor=DARK2,     fontName='Helvetica-Bold')
    resumo = Table(
        [
            [Paragraph('SERVIÇO',        s_card_label),
             Paragraph('ETAPA',          s_card_label),
             Paragraph('DIA COBRANÇA',   s_card_label),
             Paragraph('COMPLETUDE',     s_card_label)],
            [Paragraph(SERVICOS_DISPLAY.get(c.servico, c.servico or '—'), s_card_value),
             Paragraph(badge_etapa(c.etapa), s_card_value),
             Paragraph(f'Dia {c.dia_cobranca}' if c.dia_cobranca else '—', s_card_value),
             Paragraph(f'<font color="{pts_cor}">{pts}/10</font>', s_card_value)],
        ],
        colWidths=[col_w]*4
    )
    resumo.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), GOLD_LIGHT),
        ('BOX',          (0,0), (-1,-1), 0.5, GOLD),
        ('LINEAFTER',    (0,0), (2,1),   0.3, BORDER),
        ('VALIGN',       (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING',  (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING',   (0,0), (-1,-1), 8),
        ('BOTTOMPADDING',(0,0), (-1,-1), 8),
        ('TOPPADDING',   (1,0), (-1,0),  4),
    ]))
    elements.append(resumo)
    elements.append(Spacer(1, 14))

    # Informações Gerais
    elements.append(section_title('Informações Gerais'))
    elements.append(Spacer(1, 4))
    elements.append(info_table([
        ('Responsável',    c.responsavel),
        ('Telefone',       c.telefone),
        ('E-mail',         c.email),
        ('CNPJ',           c.cnpj),
        ('Criado em',      c.criado_em.strftime('%d/%m/%Y')),
        ('Atualizado em',  c.atualizado_em.strftime('%d/%m/%Y') if c.atualizado_em else None),
    ]))
    elements.append(Spacer(1, 10))

    # Presença Digital
    presenca = [
        ('WhatsApp',     c.whatsapp),
        ('Instagram',    c.instagram),
        ('Facebook',     c.facebook),
        ('Google Maps',  c.google_maps),
        ('iFood',        c.ifood),
    ]
    if any(v for _, v in presenca):
        elements.append(section_title('Presença Digital'))
        elements.append(Spacer(1, 4))
        elements.append(info_table(presenca))
        if any([c.obs_whatsapp, c.obs_instagram, c.obs_facebook, c.obs_google_maps, c.obs_ifood]):
            elements.append(Spacer(1, 4))
            elements.append(info_table([
                ('Obs. WhatsApp',    c.obs_whatsapp),
                ('Obs. Instagram',   c.obs_instagram),
                ('Obs. Facebook',    c.obs_facebook),
                ('Obs. Google Maps', c.obs_google_maps),
                ('Obs. iFood',       c.obs_ifood),
            ]))
        elements.append(Spacer(1, 10))

    # Google Drive + E-mails
    if c.google_drive or c.emails_rede:
        elements.append(section_title('Materiais e Acesso'))
        elements.append(Spacer(1, 4))
        elements.append(info_table([
            ('Google Drive',   c.google_drive),
            ('E-mails da rede', c.emails_rede),
        ], col1=4.5*cm))
        elements.append(Spacer(1, 10))

    # Acessos e Senhas
    acessos = [(label, getattr(c, f'{plat}_login'), getattr(c, f'{plat}_senha'))
               for plat, label in PLATAFORMAS_LOGIN
               if getattr(c, f'{plat}_login') or getattr(c, f'{plat}_senha')]
    if acessos:
        elements.append(section_title('Acessos e Senhas'))
        elements.append(Spacer(1, 4))
        header_row = [Paragraph(t, sty('TH', fontSize=8, fontName='Helvetica-Bold',
                                       textColor=WHITE))
                      for t in ['Plataforma', 'Login / Usuário', 'Senha']]
        rows = [header_row]
        for i, (label, login, senha) in enumerate(acessos):
            bg = GREY_BG if i % 2 else WHITE
            rows.append([
                Paragraph(label,      sty(f'td{i}a', fontSize=9, textColor=DARK2, fontName='Helvetica-Bold')),
                Paragraph(login or '—', sty(f'td{i}b', fontSize=9, textColor=DARK2)),
                Paragraph(senha or '—', sty(f'td{i}c', fontSize=9, textColor=DARK2)),
            ])
        col3 = [4.5*cm, (CW-4.5*cm)/2, (CW-4.5*cm)/2]
        tt = Table(rows, colWidths=col3)
        tt.setStyle(TableStyle([
            ('BACKGROUND',  (0,0), (-1,0),  DARK),
            ('ROWBACKGROUNDS',(0,1),(-1,-1), [WHITE, GREY_BG]),
            ('LINEBELOW',   (0,0), (-1,-1), 0.3, BORDER),
            ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING',(0,0), (-1,-1), 8),
            ('TOPPADDING',  (0,0), (-1,-1), 6),
            ('BOTTOMPADDING',(0,0),(-1,-1), 6),
            ('BOX',         (0,0), (-1,-1), 0.5, BORDER),
        ]))
        elements.append(KeepTogether(tt))
        elements.append(Spacer(1, 10))

    # Horário de Atendimento
    horarios = []
    for dia in DIAS_SEMANA:
        ab = getattr(c, f'horario_{dia}_abertura') or ''
        fe = getattr(c, f'horario_{dia}_fechamento') or ''
        if ab or fe:
            horarios.append((DIAS_DISPLAY[dia], ab or '—', fe or '—'))
    if horarios:
        elements.append(section_title('Horário de Atendimento'))
        elements.append(Spacer(1, 4))
        h_header = [Paragraph(t, sty('HH', fontSize=8, fontName='Helvetica-Bold', textColor=WHITE))
                    for t in ['Dia', 'Abertura', 'Fechamento']]
        h_rows = [h_header]
        for i, (dia_l, ab, fe) in enumerate(horarios):
            h_rows.append([
                Paragraph(dia_l, sty(f'hd{i}', fontSize=9, fontName='Helvetica-Bold', textColor=DARK2)),
                Paragraph(ab,    sty(f'ha{i}', fontSize=9, textColor=DARK2)),
                Paragraph(fe,    sty(f'hf{i}', fontSize=9, textColor=DARK2)),
            ])
        ht = Table(h_rows, colWidths=[5*cm, 5*cm, 5*cm])
        ht.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (-1,0),  DARK),
            ('ROWBACKGROUNDS',(0,1),(-1,-1), [WHITE, GREY_BG]),
            ('LINEBELOW',    (0,0), (-1,-1), 0.3, BORDER),
            ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING',  (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING',   (0,0), (-1,-1), 7),
            ('BOTTOMPADDING',(0,0), (-1,-1), 7),
            ('BOX',          (0,0), (-1,-1), 0.5, BORDER),
        ]))
        elements.append(KeepTogether(ht))
        elements.append(Spacer(1, 10))

    # Notas
    if c.notas:
        elements.append(section_title('Notas'))
        elements.append(Spacer(1, 4))
        nota_data = [[Paragraph(c.notas.replace(chr(10), '<br/>'), s_normal)]]
        nt = Table(nota_data, colWidths=[CW])
        nt.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (-1,-1), GREY_BG),
            ('BOX',          (0,0), (-1,-1), 0.5, BORDER),
            ('LEFTPADDING',  (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING',   (0,0), (-1,-1), 8),
            ('BOTTOMPADDING',(0,0), (-1,-1), 8),
        ]))
        elements.append(nt)

    # ── Build ─────────────────────────────────────────────────────────
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=MT, bottomMargin=MB,
                            leftMargin=ML, rightMargin=MR)
    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
    buf.seek(0)
    filename = (c.empresa or c.nome).replace(' ', '_') + '.pdf'
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=filename)


# ─── Sync Cardápio ─────────────────────────────────────────────────────────────
@app.route('/clientes/<int:id>/sync-cardapio', methods=['POST'])
def sync_cardapio(id):
    c = db.get_or_404(Cliente, id)
    url = c.cardapio_link
    if not url:
        return jsonify({'erro': 'Nenhum link de cardápio cadastrado.'}), 400
    try:
        resp = req_lib.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        ct = resp.headers.get('content-type', '')
        if 'pdf' in ct or url.lower().endswith('.pdf'):
            import PyPDF2, io
            reader = PyPDF2.PdfReader(io.BytesIO(resp.content))
            texto = '\n'.join(p.extract_text() or '' for p in reader.pages)
        else:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            texto = soup.get_text(separator='\n', strip=True)
        texto = '\n'.join(l for l in texto.splitlines() if l.strip())[:8000]
        c.cardapio_dados = texto
        c.atualizado_em = datetime.utcnow()
        db.session.commit()
        return jsonify({'ok': True, 'chars': len(texto), 'preview': texto[:300]})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


# ─── Chat IA ────────────────────────────────────────────────────────────────────
def _extrair_username_instagram(url_ou_user):
    import re
    if not url_ou_user:
        return None
    m = re.search(r'instagram\.com/([^/?#\s]+)', url_ou_user)
    if m:
        return m.group(1).strip('/')
    return url_ou_user.strip('@').strip('/')


def _sistema_ia(c):
    horario_txt = []
    for dia in DIAS_SEMANA:
        ab = getattr(c, f'horario_{dia}_abertura') or ''
        fe = getattr(c, f'horario_{dia}_fechamento') or ''
        if ab or fe:
            horario_txt.append(f'{DIAS_DISPLAY[dia]}: {ab}–{fe}')

    # Bloco de rodapé formatado para a copy
    def _val(v):
        return v if v and str(v).strip().lower() not in ('none', '') else None

    rodape_linhas = []
    if _val(c.endereco):
        rodape_linhas.append(f'📍 {c.endereco}')
    if _val(c.whatsapp):
        rodape_linhas.append(f'📲 {c.whatsapp}')
    if horario_txt:
        horarios_unicos = list(dict.fromkeys(h.split(': ', 1)[1] for h in horario_txt))
        def _fmt_hr(h):
            # "08:00" → "08h" / "08:30" → "08h30"
            p = h.split(':')
            return f"{p[0]}h" if p[1] == '00' else f"{p[0]}h{p[1]}"
        if len(horarios_unicos) == 1:
            ab_hr, fe_hr = horarios_unicos[0].split('–')
            n = len(horario_txt)
            if n == 7:
                label = 'Todos os dias'
            elif n == 6:
                label = 'Segunda a Sábado'
            elif n == 5:
                label = 'Segunda a Sexta'
            else:
                dias_abrev = {'Segunda':'Seg','Terça':'Ter','Quarta':'Qua','Quinta':'Qui',
                              'Sexta':'Sex','Sábado':'Sáb','Domingo':'Dom'}
                label = ', '.join(dias_abrev.get(h.split(':')[0].strip(), h.split(':')[0].strip()) for h in horario_txt)
            rodape_linhas.append(f'🕐 {label}: {_fmt_hr(ab_hr.strip())} às {_fmt_hr(fe_hr.strip())}')
        else:
            dias_abrev = {'Segunda':'Seg','Terça':'Ter','Quarta':'Qua','Quinta':'Qui',
                          'Sexta':'Sex','Sábado':'Sáb','Domingo':'Dom'}
            partes = []
            for h in horario_txt:
                dia, hr = h.split(': ', 1)
                ab_hr, fe_hr = hr.split('–')
                partes.append(f"{dias_abrev.get(dia, dia)}: {_fmt_hr(ab_hr.strip())} às {_fmt_hr(fe_hr.strip())}")
            rodape_linhas.append('🕐 ' + ' | '.join(partes))
    rodape_info = '\n'.join(rodape_linhas) if rodape_linhas else ''

    ig_bloco = ''
    if c.instagram_dados:
        try:
            ig = json.loads(c.instagram_dados)
            ig_bloco = f"""
=== INSTAGRAM SINCRONIZADO ===
Perfil: @{ig.get('username','')} — {ig.get('nome_completo','')}
Bio: {ig.get('bio','')}
Seguidores: {ig.get('seguidores','')}
Últimas legendas publicadas:
{chr(10).join('  • ' + p for p in ig.get('posts',[])[:8])}
Hashtags mais usadas pelo perfil: {', '.join(ig.get('hashtags',[])[:15])}"""
        except Exception:
            ig_bloco = f'\n=== INSTAGRAM ===\n{c.instagram_dados[:500]}'

    tem_cardapio = bool(c.cardapio_dados and c.cardapio_dados.strip())
    cardapio_bloco = ''
    aviso_cardapio = ''
    if tem_cardapio:
        cardapio_bloco = f"""
=== CARDÁPIO / PRODUTOS (FONTE PRINCIPAL DAS COPIES) ===
{c.cardapio_dados[:5000]}
=== FIM DO CARDÁPIO ==="""
    else:
        aviso_cardapio = '\n⚠️ CARDÁPIO NÃO SINCRONIZADO: pergunte ao usuário qual produto/item destacar antes de criar a copy.'

    return f"""Você é um redator publicitário sênior especializado em redes sociais e marketing de performance.
Cria conteúdo exclusivo para o cliente abaixo, contratado pela agência AURUM CRM.

━━━ DADOS DO CLIENTE ━━━
NOME DA LOJA (use este nas copies): {c.nome}
REDE/FRANQUIA (contexto apenas, não usar como nome da loja): {c.empresa or '—'}
ENDEREÇO: {c.endereco or '—'}
WHATSAPP: {c.whatsapp or '—'}
INSTAGRAM: {c.instagram or '—'}
HORÁRIO: {', '.join(horario_txt) if horario_txt else '—'}

RODAPÉ PRONTO (cole exatamente assim ao final de cada copy, após uma linha em branco):
{rodape_info if rodape_info else '(sem endereço/whatsapp/horário cadastrado — omita o rodapé)'}
{ig_bloco}
{cardapio_bloco}
{aviso_cardapio}

━━━ FRAMEWORK OBRIGATÓRIO: AIDA ━━━
A estrutura interna é sempre AIDA — mas os rótulos (Atenção, Interesse, Desejo, Ação) NUNCA aparecem no texto final.
A copy deve sair pronta para copiar e colar direto no Instagram ou gerenciador de anúncios.
Cada bloco AIDA é separado por uma linha em branco — sem títulos, sem comentários, sem explicações antes ou depois.

▸ A — ATENÇÃO (1–2 linhas | guia interno, não aparece na copy)
Gancho que interrompe o scroll. Deve ser específico, inesperado ou emocional.
Varie o tipo a cada copy — NUNCA repita a mesma fórmula:
  • Afirmação ousada: "Essa é a fritura que faz a galera parar o feed."
  • Cena cotidiana concreta: "19h. Fome. Sem paciência pra esperar 40 minutos."
  • Provocação direta: "Você ainda pede frito sem crocância? Que desperdício."
  • Urgência/escassez: "Quantidade limitada. Quem pede primeiro, garante."
  • Desejo latente: "Aquela vontade de comer algo que valha cada centavo."
  • Prova social: "Quem já pediu uma vez não consegue pedir outra coisa."

PROIBIDO no gancho:
  ✗ "Sabe aquele momento que pede algo especial?"
  ✗ "Você merece se presentear"
  ✗ "Nesta sexta-feira", "fim de semana chegando", qualquer menção a dia ou data (a menos que o usuário peça)
  ✗ Qualquer frase genérica que sirva para qualquer produto

▸ I — INTERESSE (1–2 linhas | guia interno, não aparece na copy)
Conecte o gancho ao produto via storytelling, benefício ou contexto emocional.
Aplique gatilhos de prova social, exclusividade ou identificação.
CERTO: "É pra isso que existe o Croc — pra transformar uma noite comum em algo que vale lembrar."
ERRADO: "Venha experimentar nosso delicioso frango artesanal feito com muito carinho."

▸ D — DESEJO (1–3 linhas | guia interno, não aparece na copy)
O produto entra com emoção — nunca com lista de ingredientes.
1 detalhe sensorial (crocância, suculência, textura, cheiro, tamanho) + nome exato do produto.
Use preço como argumento de valor quando disponível. Mencione escassez ou exclusividade se couber.

PROIBIDO: listar ingredientes em sequência. PROIBIDO mencionar gramas ou ml.
  ✗ "Frango empanado, batata frita crocante, anéis de cebola e molho especial da casa."
  ✗ "O Croc Pra Dois tem 500g de frango frito por R$ 67,99."
  ✓ "O Croc Pra Dois serve dois com aquela crocância que não deixa ninguém quieto — R$ 67,99."
  ✓ "Cada mordida do Premium soa igual: aquele estalo que avisa que era isso que faltava."

▸ A — AÇÃO (1 linha | guia interno, não aparece na copy)
CTA direto, com urgência quando pertinente.
REGRA OBRIGATÓRIA DE CTA: use SEMPRE uma variação de "Acesse nosso cardápio e confira tudo".
Exemplos aceitos:
  ✓ "Dá uma olhada no cardápio completo e escolha o seu."
  ✓ "Confira o cardápio e garante o seu agora."
  ✓ "Acessa o cardápio — tem muito mais te esperando."
  ✓ "Vem conferir tudo no nosso cardápio."
PROIBIDO no CTA:
  ✗ "Link na bio"
  ✗ Citar plataformas: "Brendi", "iFood", "WhatsApp"
  ✗ "Venha nos visitar", "entre em contato"

━━━ REGRAS DE ESCRITA ━━━
1. A copy sai PRONTA — sem introdução, sem "aqui está sua copy:", sem comentário final
2. Escreva como uma pessoa real fala — coloquial, direto, zero floreios
3. NUNCA copie descrição do cardápio — use como referência para 1 detalhe sensorial
4. Sempre use o NOME DA LOJA ({c.nome}) nas copies — nunca o nome da rede/franquia
5. PRODUTOS: use apenas os produtos principais da primeira seção/página do cardápio — NUNCA use itens secundários (molhos, bebidas, sobremesas, acompanhamentos) a menos que o usuário peça explicitamente
6. Emojis: máximo 2–3 por copy, pontuais, só quando reforçam o tom
7. Preço: use apenas o valor final (ex: "R$ 67,99") — NUNCA use formato "de R$ X por R$ Y"
8. Quantidade: NUNCA mencione gramas ou ml — use sempre quantas pessoas serve (ex: "serve 2", "pra até 4 pessoas", "perfeito pra galera")
9. Gatilhos mentais (escassez, prova social, urgência, exclusividade) distribuídos naturalmente ao longo da copy — nunca forçados
10. NUNCA mencione dia da semana, data ou período (ex: "nesta sexta", "fim de semana") a menos que o usuário peça explicitamente
11. Varie o tipo de gancho a cada copy — nunca repita a mesma abertura
12. Responda sempre em português brasileiro
13. HASHTAGS: máximo 3 por copy, relevantes ao produto/negócio/local — sem hashtags genéricas como #food #delicia #yummy #bomdemais
14. RODAPÉ OBRIGATÓRIO: após o CTA, antes das hashtags, adicione uma linha em branco e cole o RODAPÉ PRONTO exatamente como fornecido acima — endereço, WhatsApp e horários. Ordem obrigatória: CTA → linha em branco → RODAPÉ → linha em branco → hashtags. Se algum dado estiver ausente, omita apenas aquela linha do rodapé.

━━━ EXEMPLO DE FORMATO DE SAÍDA ESPERADO (Reel) ━━━
[este é o modelo exato — sem rótulos, sem comentários, pronto para copiar e colar]

Quem prova uma vez não consegue pedir outra coisa.

É esse tipo de frango que a Croc Campo Bom faz — crocante por fora, suculento por dentro, do jeito que frango frito deveria ser sempre.

O Premium Croc Pra Dois serve dois com aquela crocância que não deixa ninguém quieto — R$ 85,99. 🍗

Confira o cardápio completo e garante o seu.

📍 Rua Exemplo, 123 – Campo Bom
📲 (51) 99999-9999
🕐 Segunda a Sexta: 11h às 22h

#CrocCampoBom #FrangoFrito #CrocanteDeMais
━━━ FIM DO EXEMPLO ━━━

━━━ FORMATOS ━━━
REEL (tom informal, dinâmico)
→ 4 blocos separados por linha em branco, sem rótulos
→ Gancho / Interesse / Desejo + produto + preço / CTA cardápio
→ Até 3 hashtags no final

STORIES (tom urgente, direto)
→ 3 blocos curtos, sem rótulos
→ Gancho forte / Desejo com detalhe + valor / CTA com urgência
→ Sem hashtags

FEED (tom equilibrado, completo)
→ AIDA fluido em 5–8 linhas corridas, sem rótulos, como post real
→ Linha em branco antes das hashtags
→ Até 3 hashtags relevantes

ANÚNCIO PAGO (tom persuasivo, conversão)
→ HEADLINE: [máx 40 caracteres, impactante, sem ponto final]
→ Linha em branco
→ AIDA em 4 blocos curtos sem rótulos (1–3 linhas cada)
→ CTA cardápio com urgência
→ PÚBLICO SUGERIDO: interesses reais e específicos

CALENDÁRIO SEMANAL
→ 7 dias com formato variado: alterne Reel, Feed, Stories, Anúncio
→ Objetivo diferente por dia: engajamento / alcance / conversão
→ Copy AIDA completa para cada dia, sem rótulos, pronta para usar
→ Pode repetir produtos com ângulos e ganchos diferentes
→ Estrutura por dia:
   📅 Dia X — Formato: [Reel/Feed/Stories/Anúncio] — Objetivo: [engajamento/alcance/conversão]
   [copy completa sem rótulos AIDA]"""


@app.route('/clientes/<int:id>/ia')
def ia_chat(id):
    c = db.get_or_404(Cliente, id)
    msgs = ChatMensagem.query.filter_by(cliente_id=id).order_by(ChatMensagem.criado_em).all()
    historico_salvo = [{'role': m.role, 'content': m.conteudo, 'tipo': m.tipo} for m in msgs]
    return render_template('ia_chat.html', c=c,
                           etapas_display=ETAPAS_DISPLAY,
                           servicos_display=SERVICOS_DISPLAY,
                           historico_salvo=historico_salvo)


@app.route('/clientes/<int:id>/ia/chat', methods=['POST'])
def ia_chat_post(id):
    c = db.get_or_404(Cliente, id)
    from openai import OpenAI
    client_ai = OpenAI(api_key=os.environ.get('OPENAI_API_KEY', ''))
    data = request.get_json()
    msg_usuario = data.get('mensagem', '')
    # Carrega histórico do banco
    msgs_db = ChatMensagem.query.filter_by(cliente_id=id).order_by(ChatMensagem.criado_em).all()
    historico = [{'role': m.role, 'content': m.conteudo} for m in msgs_db]
    historico.append({'role': 'user', 'content': msg_usuario})
    mensagens = [{'role': 'system', 'content': _sistema_ia(c)}] + historico
    try:
        resp = client_ai.chat.completions.create(
            model='gpt-4o',
            messages=mensagens,
            max_tokens=1400,
            temperature=0.8,
        )
        resposta = resp.choices[0].message.content
        # Salva no banco
        db.session.add(ChatMensagem(cliente_id=id, role='user',      conteudo=msg_usuario))
        db.session.add(ChatMensagem(cliente_id=id, role='assistant', conteudo=resposta))
        db.session.commit()
        return jsonify({'ok': True, 'resposta': resposta})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/clientes/<int:id>/ia/historico', methods=['DELETE'])
def ia_limpar_historico(id):
    db.get_or_404(Cliente, id)
    ChatMensagem.query.filter_by(cliente_id=id).delete()
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/clientes/<int:id>/sync-instagram', methods=['POST'])
def sync_instagram(id):
    import re
    c = db.get_or_404(Cliente, id)
    username = _extrair_username_instagram(c.instagram)
    if not username:
        return jsonify({'erro': 'Nenhum perfil do Instagram cadastrado no campo Instagram.'}), 400
    headers_mobile = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'x-ig-app-id': '936619743392459',
    }
    dados = {'username': username, 'bio': '', 'nome_completo': '', 'seguidores': '',
             'posts': [], 'hashtags': []}
    try:
        # Tenta API web do Instagram
        r = req_lib.get(
            f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}',
            headers=headers_mobile, timeout=12
        )
        if r.status_code == 200:
            raw = r.json()
            user = raw.get('data', {}).get('user', {})
            dados['bio']          = user.get('biography', '')
            dados['nome_completo']= user.get('full_name', '')
            dados['seguidores']   = str(user.get('edge_followed_by', {}).get('count', ''))
            edges = user.get('edge_owner_to_timeline_media', {}).get('edges', [])
            for e in edges[:12]:
                node = e.get('node', {})
                caps = node.get('edge_media_to_caption', {}).get('edges', [])
                if caps:
                    dados['posts'].append(caps[0]['node']['text'][:200])
        else:
            # Fallback: scraping HTML
            r2 = req_lib.get(f'https://www.instagram.com/{username}/',
                             headers=headers_mobile, timeout=12)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r2.text, 'html.parser')
            desc = soup.find('meta', attrs={'name': 'description'})
            if desc:
                dados['bio'] = desc.get('content', '')
            title = soup.find('meta', attrs={'property': 'og:title'})
            if title:
                dados['nome_completo'] = title.get('content', '').split('(')[0].strip()
        # Extrai hashtags dos posts
        todas_tags = re.findall(r'#(\w+)', ' '.join(dados['posts']) + ' ' + dados['bio'])
        freq = {}
        for t in todas_tags:
            freq[t] = freq.get(t, 0) + 1
        dados['hashtags'] = [t for t, _ in sorted(freq.items(), key=lambda x: -x[1])][:20]
        c.instagram_dados = json.dumps(dados, ensure_ascii=False)
        c.atualizado_em = datetime.utcnow()
        db.session.commit()
        return jsonify({'ok': True, 'dados': dados})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/static/generated/<path:filename>')
def imagem_gerada(filename):
    return send_file(os.path.join(app.root_path, 'static', 'generated', filename))


def _compor_texto_imagem(img_bytes, nome_loja, copy_txt, preco, cta='VER CARDÁPIO', logo_path=None):
    """Design profissional: gradientes, logo, copy, preço e CTA via Pillow."""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    from io import BytesIO
    import math

    GOLD       = (201, 168, 76, 255)
    GOLD_DARK  = (160, 128, 40, 255)
    WHITE      = (255, 255, 255, 255)
    BLACK_S    = (0, 0, 0, 180)
    FONT_DIR   = 'C:/Windows/Fonts/'

    def fnt(nome, size):
        for n in [nome, 'arialbd.ttf', 'arial.ttf']:
            try: return ImageFont.truetype(FONT_DIR + n, size)
            except: pass
        return ImageFont.load_default()

    def wrap(draw, text, font, max_w):
        words, lines, line = text.split(), [], []
        for w in words:
            test = ' '.join(line + [w])
            bb = draw.textbbox((0,0), test, font=font)
            if bb[2]-bb[0] > max_w and line:
                lines.append(' '.join(line)); line = [w]
            else: line.append(w)
        if line: lines.append(' '.join(line))
        return lines

    img = Image.open(BytesIO(img_bytes)).convert('RGBA')
    W, H = img.size

    # Levemente aumenta saturação e contraste da foto base
    rgb = img.convert('RGB')
    rgb = ImageEnhance.Color(rgb).enhance(1.15)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.08)
    img = rgb.convert('RGBA')

    ov = Image.new('RGBA', (W, H), (0,0,0,0))
    d  = ImageDraw.Draw(ov)

    # ── GRADIENTE INFERIOR (55% da altura) ──────────────────────────────────
    gh = int(H * 0.55)
    for y in range(gh):
        t = y / gh
        a = int(235 * (t ** 1.6))
        d.rectangle([(0, H-gh+y),(W, H-gh+y+1)], fill=(10,8,5,a))

    # ── GRADIENTE TOPO (18% da altura) ──────────────────────────────────────
    th = int(H * 0.18)
    for y in range(th):
        a = int(170 * (1 - y/th)**1.4)
        d.rectangle([(0,y),(W,y+1)], fill=(0,0,0,a))

    # ── LINHA DECORATIVA DOURADA ─────────────────────────────────────────────
    lw = int(W * 0.55)
    lx = (W - lw) // 2
    ly = int(H * 0.195)
    d.rectangle([(lx, ly),(lx+lw, ly+2)], fill=GOLD)

    # ── LOGO ─────────────────────────────────────────────────────────────────
    logo_h_used = 0
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert('RGBA')
            max_logo_h = int(H * 0.09)
            ratio = max_logo_h / logo.height
            logo = logo.resize((int(logo.width * ratio), max_logo_h), Image.LANCZOS)
            lx2 = (W - logo.width) // 2
            ly2 = int(H * 0.04)
            ov.paste(logo, (lx2, ly2), logo)
            logo_h_used = max_logo_h + int(H * 0.01)
        except Exception:
            pass

    # ── NOME DA LOJA (quando não há logo) ───────────────────────────────────
    if not logo_h_used:
        fn_nome = fnt('bahnschrift.ttf', max(30, W // 13))
        nome_up = nome_loja.upper()
        bb = d.textbbox((0,0), nome_up, font=fn_nome)
        x = (W - (bb[2]-bb[0])) // 2
        y = int(H * 0.038)
        d.text((x+2, y+2), nome_up, font=fn_nome, fill=(0,0,0,140))
        d.text((x, y),     nome_up, font=fn_nome, fill=GOLD)
        logo_h_used = (bb[3]-bb[1]) + int(H * 0.01)

    # Linha decorativa abaixo do logo/nome
    lw2 = int(W * 0.3)
    d.rectangle([((W-lw2)//2, int(H*0.04)+logo_h_used), ((W+lw2)//2, int(H*0.04)+logo_h_used+1)], fill=(201,168,76,140))

    # ── ÁREA DE CONTEÚDO INFERIOR ────────────────────────────────────────────
    y_cur = H - int(H * 0.50)

    # Copy principal
    if copy_txt:
        fn_copy = fnt('ariblk.ttf', max(32, W // 13))
        lines   = wrap(d, copy_txt, fn_copy, int(W * 0.84))
        lh      = fn_copy.size + 6
        for i, ln in enumerate(lines):
            bb = d.textbbox((0,0), ln, font=fn_copy)
            x  = (W - (bb[2]-bb[0])) // 2
            # Sombra suave
            d.text((x+3, y_cur+3), ln, font=fn_copy, fill=(0,0,0,160))
            d.text((x,   y_cur),   ln, font=fn_copy, fill=WHITE)
            y_cur += lh
        y_cur += int(H * 0.018)

    # Linha separadora fina antes do preço
    if preco and copy_txt:
        sw = int(W * 0.18)
        d.rectangle([((W-sw)//2, y_cur),((W+sw)//2, y_cur+1)], fill=(201,168,76,180))
        y_cur += int(H * 0.016)

    # Preço
    if preco:
        fn_preco = fnt('ariblk.ttf', max(54, W // 8))
        bb  = d.textbbox((0,0), preco, font=fn_preco)
        x   = (W - (bb[2]-bb[0])) // 2
        d.text((x+3, y_cur+3), preco, font=fn_preco, fill=(0,0,0,180))
        d.text((x,   y_cur),   preco, font=fn_preco, fill=(255,215,55,255))
        y_cur += (bb[3]-bb[1]) + int(H * 0.022)

    # Badge CTA
    if cta:
        fn_cta  = fnt('arialbd.ttf', max(20, W // 20))
        bb      = d.textbbox((0,0), cta, font=fn_cta)
        tw, th2 = bb[2]-bb[0], bb[3]-bb[1]
        px, py  = int(W*0.07), int(H*0.013)
        bx      = (W - tw - px*2) // 2
        by      = y_cur
        # Sombra do botão
        d.rounded_rectangle([bx+3,by+3,bx+tw+px*2+3,by+th2+py*2+3], radius=10, fill=(0,0,0,100))
        # Botão dourado
        d.rounded_rectangle([bx,by,bx+tw+px*2,by+th2+py*2], radius=10, fill=(201,168,76,240))
        # Borda levemente mais escura
        d.rounded_rectangle([bx,by,bx+tw+px*2,by+th2+py*2], radius=10, outline=(160,128,40,200), width=2)
        d.text((bx+px, by+py), cta, font=fn_cta, fill=(15,12,5,255))

    # Composição final
    img = Image.alpha_composite(img, ov).convert('RGB')
    out = BytesIO()
    img.save(out, format='PNG', optimize=True)
    return out.getvalue()


@app.route('/clientes/<int:id>/ia/imagem', methods=['POST'])
def ia_imagem(id):
    import base64, uuid
    c = db.get_or_404(Cliente, id)
    from openai import OpenAI
    client_ai = OpenAI(api_key=os.environ.get('OPENAI_API_KEY', ''))
    data = request.get_json()
    prompt_usuario = data.get('prompt', '')

    nome_loja = c.nome
    cardapio_trecho = (c.cardapio_dados or '')[:200]
    prompt_usuario = data.get('prompt', '').strip()
    preco  = data.get('preco', '').strip()
    copy   = data.get('copy', '').strip()

    # Prompt limpo — SEM texto na imagem (Pillow cuida disso depois)
    prompt_final = f"""Professional food photography for Instagram Reel (9:16 portrait), brand "{nome_loja}".

Scene: {prompt_usuario if prompt_usuario else f'crispy golden fried chicken, appetizing and glistening'}. {cardapio_trecho[:100] if cardapio_trecho else ''}

Style rules:
- Premium dark studio or moody lifestyle background — never white, never generic
- Dramatic directional lighting making the product glow and pop
- Boost saturation and contrast naturally — vivid, appetizing colors
- Ultra sharp product details, editorial food photography quality
- No text, no watermarks, no logos — clean photo only
- Overall: luxury fast-casual food brand, high-end editorial"""

    gen_dir = os.path.join(app.root_path, 'static', 'generated')
    os.makedirs(gen_dir, exist_ok=True)

    try:
        resp = client_ai.images.generate(
            model='gpt-image-1',
            prompt=prompt_final,
            size='1024x1536',
            quality='high',
            n=1,
        )
        b64 = resp.data[0].b64_json
        img_bytes = base64.b64decode(b64)

        # Adiciona texto profissionalmente com Pillow
        img_final = _compor_texto_imagem(img_bytes, nome_loja, copy, preco, logo_path=c.logo_path)

        fname = f"reel_{id}_{uuid.uuid4().hex[:8]}.png"
        fpath = os.path.join(gen_dir, fname)
        with open(fpath, 'wb') as f:
            f.write(img_final)
        url_local = f"/static/generated/{fname}"

        db.session.add(ChatMensagem(cliente_id=id, role='user',
            conteudo=f'[IMAGEM] {prompt_usuario}', tipo='imagem'))
        db.session.add(ChatMensagem(cliente_id=id, role='assistant',
            conteudo=url_local, tipo='imagem'))
        db.session.commit()
        return jsonify({'ok': True, 'url': url_local})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/clientes/<int:id>/logo', methods=['POST'])
def upload_logo(id):
    c = db.get_or_404(Cliente, id)
    f = request.files.get('logo')
    if not f:
        return jsonify({'erro': 'Nenhum arquivo'}), 400
    logo_dir = os.path.join(app.root_path, 'static', 'logos')
    os.makedirs(logo_dir, exist_ok=True)
    ext  = os.path.splitext(f.filename)[1].lower() or '.png'
    fname = f"logo_{id}{ext}"
    fpath = os.path.join(logo_dir, fname)
    f.save(fpath)
    c.logo_path = fpath
    db.session.commit()
    return jsonify({'ok': True, 'url': f'/static/logos/{fname}'})


@app.route('/clientes/<int:id>/ia/imagem/upload', methods=['POST'])
def ia_imagem_upload(id):
    import base64, uuid
    c = db.get_or_404(Cliente, id)
    from openai import OpenAI
    client_ai = OpenAI(api_key=os.environ.get('OPENAI_API_KEY', ''))

    arquivo = request.files.get('imagem')
    contexto = request.form.get('contexto', '').strip()
    preco    = request.form.get('preco', '').strip()
    copy     = request.form.get('copy', '').strip()
    if not arquivo:
        return jsonify({'erro': 'Nenhuma imagem enviada'}), 400

    nome_loja = c.nome
    cardapio_trecho = (c.cardapio_dados or '')[:150]

    # Prompt limpo — SEM texto na imagem (Pillow cuida disso depois)
    prompt_design = f"""Professional food photo editor. Edit this product image for "{nome_loja}" Instagram Reel (9:16 portrait).

MANDATORY RULES:
- Keep the product EXACTLY as it is — shape, form, details UNCHANGED
- Replace original background with premium scenario: dark studio, marble, moody bokeh, or luxury surface
- Boost saturation and contrast naturally — vivid, appetizing, not plastic
- Dramatic directional lighting consistent between product and new background
- Product must look naturally placed in the new scene
- Ultra sharp, editorial quality — luxury fast-casual food brand feel
- No text, no watermarks, no logos — clean photo only

Context: {contexto if contexto else nome_loja + ' food product'}"""

    gen_dir = os.path.join(app.root_path, 'static', 'generated')
    os.makedirs(gen_dir, exist_ok=True)

    try:
        from io import BytesIO
        img_bytes_input = arquivo.read()
        img_file = BytesIO(img_bytes_input)
        img_file.name = arquivo.filename or 'produto.png'

        resp = client_ai.images.edit(
            model='gpt-image-1',
            image=img_file,
            prompt=prompt_design,
            size='1024x1536',
        )
        b64 = resp.data[0].b64_json
        out_bytes = base64.b64decode(b64)

        # Adiciona texto profissionalmente com Pillow
        img_final = _compor_texto_imagem(out_bytes, nome_loja, copy, preco, logo_path=c.logo_path)

        fname = f"reel_{id}_{uuid.uuid4().hex[:8]}.png"
        fpath = os.path.join(gen_dir, fname)
        with open(fpath, 'wb') as f:
            f.write(img_final)
        url_local = f"/static/generated/{fname}"

        db.session.add(ChatMensagem(cliente_id=id, role='user',
            conteudo=f'[IMAGEM COM UPLOAD] {contexto}', tipo='imagem'))
        db.session.add(ChatMensagem(cliente_id=id, role='assistant',
            conteudo=url_local, tipo='imagem'))
        db.session.commit()
        return jsonify({'ok': True, 'url': url_local})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
