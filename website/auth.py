from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from . import db
from .models import User
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .views import set_temporary_garbage, get_temporary_garbage

    

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '')
        senha1 = request.form.get('senha1', '')

        user = User.query.filter_by(email=email).first()
        if user and senha1 and check_password_hash(user.senha1, senha1):
            flash('Login feito com sucesso.', category='success')
            login_user(user, remember=True)
            return redirect(url_for('views.home'))
        else:
            flash('Credenciais inválidas.', category='error')

    return render_template('login.html')


 
@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        nome = request.form.get('nome')
        senha1= request.form.get('senha1')
        senha2 = request.form.get('senha2')
        telefone = request.form.get('telefone')
        
        email_exists = User.query.filter_by(email=email).first()
        nome_exists = User.query.filter_by(nome=nome).first()
        if email_exists:
            flash('E-mail já etá sendo usado.', category='error')
        elif nome_exists:
            flash('Nome de usuário já existe.', category='error')
        elif senha1 != senha2:
            flash('As senhas devem ser iguais.', category='error')    
        elif len(nome) < 2:
            flash('Nome de usuário muito curto.', category='error' )
        elif len(senha1) < 6:
            flash('Senha muito curta.', category='error')
        else:
            new_user = User(email=email, nome=nome, telefone=telefone,senha1 = generate_password_hash(senha1, method='pbkdf2:sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Usuário criado.')
            return redirect(url_for('views.home'))  
            
    return render_template('signup.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))



@auth.route('/exemplo', methods=['POST'])
def exemplo():
    # Define o lixo temporário
    set_temporary_garbage()

    # Redireciona para outra rota
    return redirect(url_for('views.home'))

@auth.route('/exemplo2')
def exemplo2():
    # Obtém todos os lixos temporários armazenados na sessão
    garbage_list = session.get('temporary_garbage_list', [])
    
    # Renderiza o template HTML e passa a lista de lixos temporários
    return render_template('lixo.html', garbage_list=garbage_list)
 