from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    telefone = db.Column(db.String(20))
    nome = db.Column(db.String(150), unique=True)
    senha1 = db.Column(db.String(150))
    posts = db.relationship('Post', backref='user', passive_deletes=True)
    arquivos = db.relationship('Arquivo', backref='user', passive_deletes=True)
    arquivos_excluidos = db.relationship('ArquivoExcluido', backref='user', passive_deletes=True)
    posts_excluidos = db.relationship('PostExcluido', backref='user', passive_deletes=True)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    author = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

class Arquivo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    conteudo = db.Column(db.LargeBinary)
    tipo = db.Column(db.String(10))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

    def __init__(self, nome, conteudo, tipo, user_id):
        self.nome = nome
        self.conteudo = conteudo
        self.tipo = tipo
        self.user_id = user_id

class ArquivoExcluido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    conteudo = db.Column(db.LargeBinary)
    tipo = db.Column(db.String(10))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

class PostExcluido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)



class Mensagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conteudo = db.Column(db.Text, nullable=False)
    arquivo_id = db.Column(db.Integer, db.ForeignKey('arquivo.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    data_criacao = db.Column(db.DateTime(timezone=True), default=func.now())

    arquivo = db.relationship('Arquivo', backref='mensagens')
    user = db.relationship('User', backref='mensagens')


