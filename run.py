from waitress import serve
from app import create_the_application
from config import loger, conf

def start_the_application():
    
    """Determina informações de ambiente, servidor e porta"""
    environment = conf.get_env_config()['environment']
    host = conf.get_server_config()['server_host']
    port = conf.get_server_config()['server_port']
    
    """Criação da Aplicação"""
    app = create_the_application()
    
    """Inicia o servidor conforme ambiente"""
    if environment == '1':
        print(f'Servidor iniciando em host:{host}  porta:{port}')
        serve(app, host=host, port=port)
    else:
        print(f'Servidor iniciando em host:{host}  porta:{port}')
        app.run(host=host, port=port, debug=True)
        

if __name__ == '__main__':
    start_the_application()