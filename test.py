import pandas as pd
import json

def build_relationship_tree(entity, relations_df, entities):
    """
    Função recursiva para construir o relacionamento completo de uma entidade.
    
    :param entity: Entidade atual.
    :param relations_df: DataFrame contendo os relacionamentos.
    :param entities: Lista de entidades fornecidas para verificar a existência.
    :return: Lista com a hierarquia da entidade.
    """
    # Filtra as linhas onde a entidade é um nó filho (entity).
    related_rows = relations_df[relations_df['entity'] == entity]

    # Inicializa a árvore de relacionamento para a entidade.
    relationships = []

    for _, row in related_rows.iterrows():
        parent_entity = row['parent']
        weight = row['weight'] - 1  # Corrige o peso para refletir a hierarquia.

        # Verifica se o parent_entity deve ter filhos (não deve ser cliente ou produto).
        if pd.notna(parent_entity) and parent_entity not in ["cliente", "produto"]:
            parent_tree = build_relationship_tree(parent_entity, relations_df, entities)
        else:
            parent_tree = []  # Define parent como vazio para cliente e produto.

        # Cria o dicionário de relacionamento.
        relationship = {
            "weight": weight,
            "entity": parent_entity,
            "exists": 1 if parent_entity in entities else 0,
            "parent": parent_tree
        }

        # Adiciona o relacionamento à lista.
        relationships.append(relationship)

    return relationships




def identify_entity_relationships(entities, relations_df):
    """
    Identifica o relacionamento completo para as entidades fornecidas.

    :param entities: Lista de entidades a serem analisadas.
    :param relations_df: DataFrame contendo os dados da tabela relations.
    :return: Dicionário contendo as relações hierárquicas para cada entidade na lista.
    """
    result = {}

    for entity in entities:
        # Filtra o DataFrame para encontrar a entidade com weight == 2.
        if not relations_df[(relations_df['entity'] == entity) & (relations_df['weight'] == 2)].empty:
            result[entity] = build_relationship_tree(entity, relations_df, entities)

    return result

def count_exists(entity_tree):
    count = 0  # Inicializa a variável count

    # Verifica se entity_tree é uma lista
    if isinstance(entity_tree, list):
        for item in entity_tree:
            # Verifica se o item é um dicionário e se contém a chave 'exists' com valor 1
            if isinstance(item, dict) and item.get('exists') == 1:
                count += 1

    return count

def percorrer_nos(no, list_domains, nivel=0):
    """
    Percorre recursivamente os nós para construir a lista de domínios.

    :param no: Nó atual (dicionário).
    :param list_domains: Lista acumulada de domínios.
    :param nivel: Nível atual na hierarquia (peso).
    """
    if 'parent' in no and isinstance(no['parent'], list) and no['parent']:
        list_domains.append({"entity": no['entity'], "weight": no['weight']})
        for parent_no in no:
            qtd_pais = len(no['parent'])
            qtd_exists = count_exists(no['parent'])

            # Condição: Apenas 1 pai existente
            if qtd_pais > 1 and qtd_exists == 1 or qtd_pais == 1 and qtd_exists == 1:
                for sub_no in no['parent']:
                    if sub_no['exists'] == 1:
                        # Verifica se a entidade já está na lista para evitar duplicatas
                        if not any(d['entity'] == sub_no['entity'] for d in list_domains):
                            list_domains.append({"entity": sub_no['entity'], "weight": nivel - 1})
                        percorrer_nos(sub_no, list_domains, nivel - 1)
            # Condição: Mais de 1 pai existente
            elif qtd_pais > 1 and qtd_exists > 1 or qtd_pais > 1 and qtd_exists == 0:
                list_ent = [sub_no['entity'] for sub_no in no['parent']]
                return list_domains.append({"response": montar_resposta(no['entity'], list_ent, entites_words)})
    elif no.get('entity') == 0:
        if not any(d['entity'] == no['entity'] for d in list_domains):
            list_domains.append({"entity": no['entity'], "weight": no['weight']})

def confere_integridade(result, entites_words):
    """
    Confere a integridade das relações e constrói a lista de domínios.

    :param result: Resultado das relações hierárquicas.
    :param entites_words: DataFrame com as palavras em português.
    :return: Lista de domínios.
    """
    list_domains = []
    for chave, lista_nos in result.items():
        # Adiciona a entidade raiz com peso 2
        if not any(d['entity'] == chave for d in list_domains):
            list_domains.append({"entity": chave, "weight": 2})

        qtd_pais = len(lista_nos)
        qtd_exists = count_exists(lista_nos)

        # Condições para processar os nós
        if qtd_pais > 1 and qtd_exists == 1 or qtd_pais == 1 and qtd_exists == 1:
            for no in lista_nos:
                if no['exists'] == 1:
                    percorrer_nos(no, list_domains, no['weight'])
        elif qtd_pais > 1 and qtd_exists > 1 or qtd_pais > 1 and qtd_exists == 0:
            list_ent = [no['entity'] for no in lista_nos]
            return list_domains.append({"response":montar_resposta(chave, list_ent, entites_words)})

    return list_domains  # Retorna todos os domínios processados

def montar_resposta(variavel, lista, df):
    # Verifica se a variável existe no DataFrame
    if variavel in df['entity'].values:
        # Obtém a palavra correspondente em português
        palavra = df.loc[df['entity'] == variavel, 'word'].values[0]
        
        # Formata a lista para o português
        lista_formatada = []
        for item in lista:
            if item in df['entity'].values:
                lista_formatada.append(df.loc[df['entity'] == item, 'word'].values[0])
            else:
                lista_formatada.append(item)  # Caso o item não esteja no dicionário
        
        # Formata a lista com "ou" entre as opções
        if len(lista_formatada) == 1:
            lista_str = lista_formatada[0]
        elif len(lista_formatada) == 2:
            lista_str = " ou ".join(lista_formatada)
        else:
            lista_str = ", ".join(lista_formatada[:-1]) + " ou " + lista_formatada[-1]
        
        # Monta a resposta
        resposta = f"Você está consultando sobre {palavra}, mas está se referindo a que tipo de {palavra}: {lista_str}."
        return resposta
    else:
        return "Variável não encontrada no dicionário."

# Exemplo de uso:
data = {
    "entity": ["cliente", "compra", "compra", "historico", "produto", "devolucao", "devolucao", "historico", "desconto", "desconto"],
    "weight": [0, 1, 1, 2, 0, 1, 1, 2, 2, 2],
    "parent": [None, "cliente", "produto", "compra", None, "cliente", "produto", "devolucao", "compra", "devolucao"]
}

data_entitie = {
    "entity": ["devolucao", "desconto", "historico", "compra", "produto", "cliente"],
    "word": ["Devolução", "Desconto", "Histórico", "Compra", "Produto", "Cliente"]
}

relations_df = pd.DataFrame(data)
entites_words = pd.DataFrame(data_entitie)
entities = ["historico", "compra"]

# Chama a função
result = identify_entity_relationships(entities, relations_df)

# Converte o resultado para JSON e imprime
#print(json.dumps(result, indent=4))
res = confere_integridade(result, entites_words)

response_value = res
for item in res:
    if 'response' in item and item['response']:
        response_value = item['response']
        break
print(response_value)