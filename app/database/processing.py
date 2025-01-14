from . import db
import pandas as pd
from sqlalchemy import text
from typing import Union, Dict, List
from sqlalchemy.engine.row import Row

def loads_word_replacements() -> Union[Dict[str, str], Dict[str, str]]:
    query = text("""
        SELECT
            s.word,
            s.synonym
        FROM synonyms s
    """)
    
    try:
        result = db.session.execute(query).fetchall()
        
        if not result:  # Verifica se o resultado está vazio
            return {"error": "Nenhum resultado encontrado"}
        
        # Converte o resultado para um dicionário no formato desejado
        replacements = {row.word: row.synonym for row in result}
        return replacements
        
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}
    
    finally:
        db.session.close()

def loads_entity_questions_training() -> pd.DataFrame:
    query = text("""
        SELECT
            q.question AS question,
            i.intention AS intention,
            o.object AS object,
            q.entities AS entities
        FROM questions q
        INNER JOIN intentions i ON q.intention_id = i.id
        INNER JOIN objects o ON q.object_id = o.id

    """)

    try:
        result = db.session.execute(query).fetchall()
        
        if not result:
            return pd.DataFrame({"error": ["Nenhum resultado encontrado"]})
        
        df = pd.DataFrame(result, columns=["question", "intention","object","entities"])
        return df
        
    except Exception as e:
        db.session.rollback()
        return pd.DataFrame({"error": [str(e)]})

    finally:
        db.session.close()

def loads_entity_relationship_training() -> pd.DataFrame:
    query = text("""
        SELECT
            e.translation as entity,
            w.weight as weight,
            p.translation as parent
        FROM relations r
        LEFT JOIN entities e ON r.entity_id = e.id
        LEFT JOIN weights w on r.weight_id = w.id
        LEFT JOIN entities p ON r.parent_id = p.id
    """)

    try:
        result = db.session.execute(query).fetchall()
        
        if not result:
            return pd.DataFrame({"error": ["Nenhum resultado encontrado"]})
        
        df = pd.DataFrame(result, columns=["entity", "weight","parent"])
        return df
        
    except Exception as e:
        db.session.rollback()
        return pd.DataFrame({"error": [str(e)]})

    finally:
        db.session.close()

def loads_questions(object: str) -> pd.DataFrame:
    query = text("""
        SELECT
            q.question as question,
            i.intention as intention,
            o.object as object,
            q.entities as entities,
            q.domain_address as domain_address,
            q.domain_name as domain_name
        FROM questions q
        LEFT JOIN intentions i ON q.intention_id = i.id
        LEFT JOIN objects o ON q.object_id = o.id
        WHERE (0 = 0)
        AND o.object = :object
    """)

    try:
        # Executando a consulta
        result = db.session.execute(query, {'object': object}).fetchall()

        # Verificando se há resultados
        if not result:
            return {"error": "Nenhum resultado encontrado"}

        # Convertendo os resultados para um DataFrame
        df = pd.DataFrame(
                result, 
                columns=[
                    "question", 
                    "intention",
                    "object",
                    "entities",
                    "domain_address",
                    "domain_name"
                ]
            )
        return df

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}