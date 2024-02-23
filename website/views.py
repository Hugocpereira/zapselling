from flask import Blueprint, render_template, request, flash, redirect, session, url_for, abort
from flask_login import login_required, current_user
views = Blueprint('views', __name__)
from .models import Post, User, Arquivo, ArquivoExcluido, PostExcluido, Mensagem
from . import db
from . import allowed_file
from flask import current_app
from werkzeug.utils import secure_filename
import time 
import base64

TEMPORARY_GARBAGE_TIMEOUT = 3000
BLIP_API_URL = 'https://msging.net/messages'
BLIP_AUTH_KEY = 'your_blip_auth_key'
UPLOAD_FOLDER = '/caminho/para/upload'

@views.route('/')
@views.route('/home')
@login_required
def home():
    return render_template('home.html', name=current_user.nome)


@views.route('/auto_message')
def auto_message():
    arquivos = Arquivo.query.all()
    return render_template('auto_message.html', arquivos=arquivos)


@views.route('/help')
def help():
    return render_template('help.html')

@views.route('/comunidade', methods=['GET', 'POST'])
@login_required
def comunidade():
    if request.method == 'POST':
        text = request.form.get('text')
        if not text:
            flash('Postagem não encontrada.', category='error')
        else:
            post = Post(text=text, author=current_user.id)
            db.session.add(post)
            db.session.commit()
            flash('Postado com sucesso!', category='sucess')
    posts = Post.query.all()
    return render_template('comunidade.html', posts=posts, user=current_user)



@views.route('/upload', methods=['POST', 'GET'])
def upload_file():
    if 'file' not in request.files:
        flash('Nenhum arquivo selecionado.', category='error')
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash('Nenhum arquivo selecionado.', category='error')
        return redirect(request.url)

    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']  

    if file and allowed_file(file.filename, allowed_extensions):  
        filename = secure_filename(file.filename)
        tipo = filename.rsplit('.', 1)[1].lower()
        conteudo = file.read()

        novo_arquivo = Arquivo(nome=filename, conteudo=conteudo, tipo=tipo, user_id=current_user.id)
        db.session.add(novo_arquivo)
        db.session.commit()

        flash('Arquivo enviado com sucesso!', category='success')
        return redirect(url_for('views.auto_message'))

    flash('Tipo de arquivo não permitido.', category='error')
    return redirect(request.url)


@views.route('/lixo', methods=['GET'])  
def set_temporary_garbage():
    arquivos_excluidos = ArquivoExcluido.query.filter_by(user_id=current_user.id).all()
    posts_excluidos = PostExcluido.query.filter_by(user_id=current_user.id).all()
    garbage_list = []
    for arquivo in arquivos_excluidos:
        garbage_list.append(arquivo)
    for post in posts_excluidos:
        garbage_list.append(post)
    
    return render_template('lixo.html', garbage_list=garbage_list)  

def get_temporary_garbage():
    data = session.get('temporary_garbage')
    if data:
        return data
    else:
        return 'No temporary garbage found'

@views.before_request
def clear_temporary_garbage():
    if 'last_activity' in session and time.time() - session['last_activity'] > TEMPORARY_GARBAGE_TIMEOUT:
        session.pop('temporary_garbage', None)
    session['last_activity'] = time.time()
    

@views.route('/visualizar_arquivo/<int:arquivo_id>')
def visualizar_arquivo(arquivo_id):
    arquivo = Arquivo.query.filter_by(id=arquivo_id).first()
    if arquivo:
        arquivo.conteudo_base64 = base64.b64encode(arquivo.conteudo).decode('utf-8')
        return render_template('visualizar_arquivo.html', arquivo=arquivo)
    else:
        flash('Arquivo não encontrado.', category='error')
        return redirect(url_for('views.auto_message'))


@views.route('/delete_post/<int:id>')
def delete_post(id):
    post = Post.query.get(id)

    if not post:
        flash('Postagem não encontrada.', category='error')
    elif current_user != post.user: 
        flash('Você não tem permissão para excluir esta postagem.', category='error')
    else:
        post_excluido = PostExcluido(text=post.text, user_id=current_user.id)
        db.session.add(post_excluido)
        db.session.delete(post)
        db.session.commit()
        flash('Postagem deletada com sucesso.', category='success')

    return redirect(url_for('views.comunidade'))

@views.route('/apagar_arquivo/<int:id>', methods=['POST'])
def delete_arquivo(id):
    arquivo = Arquivo.query.get(id)

    if not arquivo:
        flash('Arquivo não encontrado.', category='error')
    elif current_user != arquivo.user: 
        flash('Você não tem permissão para excluir este arquivo.', category='error')
    else:
        arquivo_excluido = ArquivoExcluido(nome=arquivo.nome, conteudo=arquivo.conteudo, tipo=arquivo.tipo, user_id=current_user.id)
        db.session.add(arquivo_excluido)
        db.session.delete(arquivo)
        db.session.commit()
        flash('Arquivo excluído com sucesso.', category='success')

    return redirect(url_for('views.auto_message'))


@views.route('/lixo_temporario', methods=['GET', 'POST'])
@login_required
def lixo_temporario():
    if request.method == 'POST':
        selected_item_id = request.form.get('garbage')
        selected_item_type = request.form.get('item_type')

        if selected_item_type == 'arquivo':
            item = ArquivoExcluido.query.filter_by(id=selected_item_id, user_id=current_user.id).first()
        elif selected_item_type == 'postagem':
            item = PostExcluido.query.filter_by(id=selected_item_id, user_id=current_user.id).first()
        else:
            flash('Tipo de item selecionado inválido.', category='error')
            return redirect(url_for('views.lixo_temporario'))

        if item:
            flash(f'Item "{item.nome}" recuperado com sucesso.', category='success')
            # Faça o que precisa ser feito para recuperar o item

    arquivos_excluidos = ArquivoExcluido.query.filter_by(user_id=current_user.id).all()
    posts_excluidos = PostExcluido.query.filter_by(user_id=current_user.id).all()
    return render_template('lixo_temporario.html', arquivos_excluidos=arquivos_excluidos, posts_excluidos=posts_excluidos)

@views.route('/funil', methods=['GET', 'POST'])
@login_required
def funil():
    if request.method == 'POST':
        conteudo = request.form.get('conteudo')
        arquivo_id = request.form.get('arquivo')  

        if 'enviar' in request.form:
            enviar_mensagem(conteudo, arquivo_id)
        elif 'salvar' in request.form:
            salvar_mensagem(conteudo, request.files.get('arquivo'))

    arquivos = current_user.arquivos
    mensagens = Mensagem.query.filter_by(user_id=current_user.id).all()
    return render_template('funil.html', arquivos=arquivos, mensagens=mensagens)


def excluir_mensagem(mensagem_id):
    mensagem = Mensagem.query.get(mensagem_id)

    if mensagem:
        if mensagem.user_id == current_user.id:
            db.session.delete(mensagem)
            db.session.commit()
            flash('Mensagem excluída com sucesso.', category='success')
        else:
            flash('Você não tem permissão para excluir esta mensagem.', category='error')
    else:
        flash('Mensagem não encontrada.', category='error')


def enviar_mensagem(conteudo, arquivo_id):
    # Salvar a mensagem no banco de dados associada ao usuário atual
    nova_mensagem = Mensagem(conteudo=conteudo, user_id=current_user.id, arquivo_id=arquivo_id)
    db.session.add(nova_mensagem)
    db.session.commit()

    # Enviar a mensagem pelo WhatsApp usando a API Blip
    try:
        arquivo = Arquivo.query.filter_by(user_id=current_user.id).all()
        if arquivo:
            media_url = request.url_root + arquivo.caminho
            payload = {
                "to": current_user.telefone,
                "type": "application/json",
                "content": {
                    "type": "text/plain",
                    "text": conteudo,
                    "mediaLink": media_url
                }
            }
        else:
            payload = {
                "to": current_user.telefone,
                "type": "application/json",
                "content": {
                    "type": "text/plain",
                    "text": conteudo
                }
            }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Key {BLIP_API_KEY}'
        }

        response = requests.post('https://msging.net/messages', json=payload, headers=headers)
        if response.status_code == 200:
            flash('Mensagem enviada com sucesso pelo WhatsApp.', category='success')
        else:
            flash('Erro ao enviar mensagem pelo WhatsApp.', category='error')
    except Exception as e:
        flash(f'Erro ao enviar mensagem pelo WhatsApp: {str(e)}', category='error')


def salvar_mensagem(conteudo, arquivo):
    caminho_arquivo = salvar_arquivo(arquivo)
    
    if caminho_arquivo:
        novo_arquivo = Arquivo(
            nome=arquivo.filename,
            caminho=caminho_arquivo,
            user_id=current_user.id
        )
        db.session.add(novo_arquivo)
        db.session.commit()

        nova_mensagem = Mensagem(
            conteudo=conteudo,
            arquivo_id=novo_arquivo.id,
            user_id=current_user.id
        )
        db.session.add(nova_mensagem)
        db.session.commit()
        flash('Mensagem e arquivo salvos com sucesso.', category='success')
    else:
        nova_mensagem = Mensagem(
            conteudo=conteudo,
            user_id=current_user.id
        )
        db.session.add(nova_mensagem)
        db.session.commit()
        flash('Mensagem salva com sucesso.', category='success')

def salvar_arquivo(arquivo):
    if arquivo:
        nome_arquivo = secure_filename(arquivo.filename)
        caminho_arquivo = os.path.join(UPLOAD_FOLDER, nome_arquivo)
        arquivo.save(caminho_arquivo)
        return caminho_arquivo
    return None


def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


@views.route('/configuracao')
def configuracao():
    return render_template('configuracao.html')

@views.route('/excluir_conta', methods=['GET', 'POST'])
@login_required
def excluir_conta():
    if request.method == 'POST':
        # Exclua o usuário e todos os dados associados
        user = current_user
        db.session.delete(user)
        db.session.commit()
        flash('Sua conta foi excluída com sucesso.', category='success')
        return redirect(url_for('auth.logout'))  # Redireciona para a rota de logout após excluir a conta
    else:
        return render_template('excluir_conta.html')  # Se a solicitação for GET, renderize o formulário de confirmação







