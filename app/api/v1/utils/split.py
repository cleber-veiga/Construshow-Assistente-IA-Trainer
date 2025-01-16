import re

def split_message(message):
    # Expressão regular para dividir o texto após pontuações ou palavras específicas
    splitters = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!|\,|\;)\s+|(?<=\btambém\b)\s+|(?<=\be\b)\s+|(?<=\bou\b)\s+'
    sub_messages = re.split(splitters, message)
    
    # Filtrar sub-mensagens irrelevantes (como "e", "ou", "também" isolados)
    final_messages = [msg.strip() for msg in sub_messages if msg.strip() and msg.strip() not in ['e', 'ou', 'também']]
    
    return final_messages

def remove_duplicate_dicts(list_of_dicts):
    # Função para converter listas em tuplas dentro do dicionário
    def make_hashable(d):
        if isinstance(d, dict):
            return tuple((k, make_hashable(v)) for k, v in d.items())
        elif isinstance(d, list):
            return tuple(make_hashable(v) for v in d)
        else:
            return d
    
    # Converte cada dicionário em uma tupla hashable
    tuples = [make_hashable(d) for d in list_of_dicts]
    
    # Remove duplicatas usando um conjunto
    unique_tuples = set(tuples)
    
    # Converte as tuplas de volta para dicionários
    unique_dicts = [dict((k, make_hashable(v) if isinstance(v, tuple) else v) for k, v in t) for t in unique_tuples]
    
    return unique_dicts