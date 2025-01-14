import os
from flask_sqlalchemy import SQLAlchemy
from config import loger,conf

# Instância do SQLAlchemy
db = SQLAlchemy()

def start_the_database(app):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(current_dir))

        db_path = os.path.join(root_dir, 'data.db')

        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        db.init_app(app)
    except FileNotFoundError as e:
        #loger.log('ERROR',f'Erro ao inicializar o banco de dados: {e}')
        print(f'Erro no arquivo de banco de dados: {e}')
        raise
    except Exception as e:
        print(f'Erro inesperado ao inicializar o banco de dados: {e}')
        #loger.log('ERROR',f'Erro inesperado ao inicializar o banco de dados: {e}')