from logging.handlers import RotatingFileHandler
import logging
import configparser
from typing import Dict
import yaml
import sys
import os


class ConfigManager:
    def __init__(self):
        self.config_file = self._get_config_file()
        self.app_path = self._get_base_dir()
        
        """Configurações gerais"""
        self.connection_file = None
        self.connection_name = None
        self.url_base = "http://+:2710/ia"
        self.debug_file_level = '0'
        self.debug_file = None
        self.environment = None
        
        """Configurações de conexão com o banco de dados Oracle"""
        self.db_server = None
        self.db_username = None
        self.db_password = None
        
        """Configurações do servidor IA"""
        self.server_host = None
        self.server_port = None
        self.server_base = None

        self._load_configuration()
        if self.connection_file and self.connection_name:
            self._load_connection_file()
        self._load_server_configuration()

    def _get_base_dir(self):
        """Determina o diretório base do script ou executável."""
        if getattr(sys, 'frozen', False):  # Executável
            return os.path.dirname(sys.executable)
        else:  # Script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.abspath(os.path.join(current_dir, "config")) 

    def _get_config_file(self):
        """Obtém o caminho completo para o arquivo de configuração."""
        base_dir = self._get_base_dir()
        config_file = os.path.join(base_dir, 'ViasoftServerConstruShowIA.conf')

        if os.path.exists(config_file):
            return config_file
        else:
            raise FileNotFoundError(f"Arquivo de configuração não encontrado em: {config_file}")

    def _replace_app_path(self, value):
        """Substitui {AppPath} pelo caminho do executável ou script."""
        if "{AppPath}" in value:
            return value.replace("{AppPath}", self.app_path)
        return value

    def _load_configuration(self):
        """Carrega as configurações do arquivo principal."""
        try:
            config = configparser.ConfigParser()
            config.read(self.config_file)
        

            if config.has_option('Conexoes', 'ArquivoConexoes'):
                self.connection_file = self._replace_app_path(
                    config.get('Conexoes', 'ArquivoConexoes')
                )

            if config.has_option('Conexoes', 'NomeConexoes'):
                self.connection_name = config.get('Conexoes', 'NomeConexoes')

            if config.has_option('Portas', 'UrlBase'):
                self.url_base = config.get('Portas', 'UrlBase')

            if config.has_option('Debug', 'DebugFileLevel'):
                self.debug_file_level = config.get('Debug', 'DebugFileLevel')
            
            if config.has_option('Debug', 'DebugFile'):
                self.debug_file = self._replace_app_path(
                    config.get('Debug', 'DebugFile')
                )
            
            if config.has_option('Ambiente', 'Ambiente'):
                self.environment = config.get('Ambiente', 'Ambiente')
            else:
                self.environment = 1
            
        except configparser.Error as e:
            raise RuntimeError(f"Erro ao carregar o arquivo de configuração: {e}")

    def _load_connection_file(self):
        """Carrega as informações do arquivo de conexões usando o nome especificado."""
        try:
            if not os.path.exists(self.connection_file):
                raise FileNotFoundError(f"Arquivo de conexões não encontrado: {self.connection_file}")

            config = configparser.ConfigParser(allow_no_value=True)
            config.read(self.connection_file)

            if self.connection_name and self.connection_name in config:
                self.db_server = config.get(self.connection_name, 'Server', fallback=None)
                self.db_username = config.get(self.connection_name, 'Username', fallback=None)
                self.db_password = config.get(self.connection_name, 'Password', fallback=None)

                # Ajusta o formato do Server, se necessário
                if self.db_server and ':' in self.db_server and self.db_server.count(':') == 2:
                    parts = self.db_server.split(':')
                    if len(parts) == 3:
                        self.db_server = f"{parts[0]}:{parts[1]}/{parts[2]}"

            else:
                raise ValueError(
                    f"Seção '{self.connection_name}' não encontrada no arquivo de conexões: {self.connection_file}"
                )
        except configparser.Error as e:
            raise RuntimeError(f"Erro ao carregar o arquivo de conexões: {e}")

    def _load_server_configuration(self):
        """Carrega as informações do servidor IA."""
        try:
            if getattr(sys, 'frozen', False):  # Executável
                client_dir = os.path.join(self.app_path, "..", "..", "Client")
            else:  # Script
                current_dir = os.path.dirname(os.path.abspath(__file__))
                client_dir = os.path.abspath(os.path.join(current_dir, "config"))

            server_file = os.path.join(client_dir, "viasoft.MCP.server")

            if not os.path.exists(server_file):
                raise FileNotFoundError(f"Arquivo do servidor não encontrado: {server_file}")

            config = configparser.ConfigParser(allow_no_value=True)
            config.read(server_file)

            if self.connection_name and self.connection_name in config:
                self.server_host = config.get(self.connection_name, 'IAServerIP', fallback=None)
                self.server_port = config.get(self.connection_name, 'IAServerPort', fallback=None)
                self.server_base = config.get(self.connection_name, 'IAUrlBase', fallback=None)
            else:
                raise ValueError(
                    f"Seção '{self.connection_name}' não encontrada no arquivo do servidor: {server_file}"
                )
        except configparser.Error as e:
            raise RuntimeError(f"Erro ao carregar o arquivo do servidor: {e}")

    def __str__(self):
        """Representação de string para depuração."""
        return (
            f"ConfigManager(\n"
            f"  Config File: {self.config_file}\n"
            f"  Connection File: {self.connection_file}\n"
            f"  Connection Name: {self.connection_name}\n"
            f"  URL Base: {self.url_base}\n"
            f"  Debug File Level: {self.debug_file_level}\n"
            f"  Debug File: {self.debug_file}\n"
            f"  DB Server: {self.db_server}\n"
            f"  DB Username: {self.db_username}\n"
            f"  DB Password: {self.db_password}\n"
            f"  Server Host: {self.server_host}\n"
            f"  Server Port: {self.server_port}\n"
            f"  Server Base: {self.server_base}\n"
            f")"
        )
    
    def get_database_credentials(self):
        """Retorna as credenciais do banco de dados."""
        if not self.db_server or not self.db_username or not self.db_password:
            raise ValueError("As credenciais do banco de dados não foram carregadas corretamente.")
        return {
            "server": self.db_server,
            "username": self.db_username,
            "password": self.db_password
        }

    def get_server_config(self):
        """Retorna as configurações do servidor."""
        if not self.server_host or not self.server_port or not self.server_base:
            raise ValueError("As configurações do servidor IA não foram carregadas corretamente.")
        return {
            "server_host": self.server_host,
            "server_port": self.server_port,
            "server_base": self.server_base
        }

    def get_log_config(self):
        """Retorna as configurações de log."""
        if not self.debug_file or not self.debug_file_level:
            raise ValueError("As configurações de log não foram carregadas corretamente.")
        return {
            "debug_file_level": self.debug_file_level,
            "debug_file": self.debug_file
        }
    
    def get_env_config(self):
        """Retorna as configurações de Ambiente."""
        if not self.environment:
            raise ValueError("As configurações de Ambiente não foram carregadas corretamente.")
        return {
            "environment": self.environment
        }

class ConfigManagerModelTraining:
    def __init__(self, config_file=None):
        """
        Gerenciador de configuração para modelos de treinamento.

        :param config_file: Caminho para o arquivo de configuração. Usa o padrão se não fornecido.
        """
        self.config_file = config_file or self._get_default_config_file()
        self.config = None

        # Carrega as configurações do arquivo
        self._load_model_config_file()

    def _get_base_dir(self):
        """Determina o diretório base do script ou executável."""
        if getattr(sys, 'frozen', False):  # Executável
            return os.path.dirname(sys.executable)
        else:  # Script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.abspath(os.path.join(current_dir, "config"))

    def _get_default_config_file(self):
        """Obtém o caminho completo para o arquivo de configuração padrão."""
        base_dir = self._get_base_dir()
        return os.path.join(base_dir, 'ModelConfigurationFile.yaml')

    def _load_model_config_file(self):
        """Carrega as configurações do arquivo YAML."""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Arquivo de configuração não encontrado em: {self.config_file}")

        with open(self.config_file, 'r') as f:
            self.config = yaml.safe_load(f)

    def save_config(self):
        """Salva as configurações atuais de volta no arquivo."""
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f)
        print(f"Configurações salvas em: {self.config_file}")

    def get(self, key, default=None):
        """Obtém uma configuração específica usando uma chave (com suporte a hierarquias)."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, default) if isinstance(value, dict) else default
        return value

    def update(self, key, value):
        """Atualiza uma configuração específica e aplica ao arquivo."""
        keys = key.split('.')
        target = self.config
        for k in keys[:-1]:
            target = target.setdefault(k, {})
        target[keys[-1]] = value

    def validate_config(self):
        """Valida as configurações essenciais."""
        required_keys = ['model', 'model_type', 'preprocessing', 'training']
        missing_keys = [key for key in required_keys if key not in self.config]
        if missing_keys:
            raise ValueError(f"Configurações ausentes: {missing_keys}")

    def show(self):
        """Imprime todas as configurações carregadas."""
        print(yaml.dump(self.config, default_flow_style=False))

    def get_all(self):
        """Retorna todas as configurações carregadas como um dicionário."""
        return self.config
    
    def update_config(self, new_config: Dict):
        """Atualiza todas as configurações com um novo dicionário e salva no arquivo original."""
        self.config = new_config
        self.save_config()

class LogManager:
    def __init__(self, conf):
        log_config = conf.get_log_config()
        self.debug_file_level = log_config['debug_file_level']
        self.debug_file = log_config['debug_file']
        self._validate_config()
        self._setup_logging()

    def _validate_config(self):
        """Valida as configurações de log."""
        if self.debug_file_level not in ['0', '1', '2']:
            raise ValueError("Nível de log inválido: debug_file_level deve ser '0', '1' ou '2'")
        if not isinstance(self.debug_file, str) or not self.debug_file.strip():
            raise ValueError("Caminho do arquivo de log inválido")

    def _ensure_log_directory(self):
        """Garante que o diretório de logs exista, criando-o se necessário."""
        log_dir = os.path.dirname(self.debug_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            print(f"Diretório de logs criado: {log_dir}")

    def _get_handler_level(self):
        """Mapeia debug_file_level para o nível correspondente."""
        if self.debug_file_level == '0':
            return logging.CRITICAL + 1  # Nenhum log será processado
        elif self.debug_file_level == '1':
            return logging.WARNING  # Exibe WARNING e níveis mais altos
        elif self.debug_file_level == '2':
            return logging.DEBUG  # Exibe todos os logs
        return logging.NOTSET

    def _setup_logging(self):
        """Configura o sistema de logs com base nas configurações."""
        self._ensure_log_directory()

        # Remove handlers existentes
        for handler in logging.getLogger().handlers[:]:
            logging.getLogger().removeHandler(handler)

        logging.getLogger().setLevel(logging.DEBUG)

        # Configura o arquivo de log com rotação
        rotating_handler = RotatingFileHandler(
            self.debug_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=2
        )
        rotating_handler.setLevel(self._get_handler_level())
        rotating_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(rotating_handler)

        # Adiciona um handler para o console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self._get_handler_level())
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(console_handler)

    def log(self, log_type="INFO", description=""):
        """Registra mensagens de log."""
        logger = logging.getLogger()
        log_type = log_type.upper()
        if hasattr(logger, log_type.lower()):
            log_method = getattr(logger, log_type.lower())
            log_method(description)

    @staticmethod
    def get_logger(name):
        """Retorna um logger com o nome especificado."""
        logger = logging.getLogger(name)
        if not logger.handlers:
            for handler in logging.getLogger().handlers:
                logger.addHandler(handler)
            logger.setLevel(logging.getLogger().level)
        return logger

conf = ConfigManager()
loger = LogManager(conf)
conf_model = ConfigManagerModelTraining()