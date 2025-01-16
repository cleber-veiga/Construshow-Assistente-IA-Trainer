import pandas as pd
from app.database.processing import loads_entity_relationship_training,loads_entity_origins

class ClassifyRelationship:

    def __init__(self,entities):
        self.entities = entities
        self.df = loads_entity_relationship_training()
        self.data = self.transform_df_to_dictionary()
        self.translation_df = loads_entity_origins()
        
    def transform_df_to_dictionary(self):
        df_filtered = self.df[['entity', 'weight', 'parent']]
        result_dict = {}

        for _, row in df_filtered.iterrows():
            entity = row['entity']
            weight = row['weight']
            parent = row['parent']

            # Se a entidade ainda não estiver no dicionário, adicioná-la
            if entity not in result_dict:
                result_dict[entity] = {
                    'weight': weight,
                    'parents': []
                }
            if parent:
                result_dict[entity]['parents'].append(parent)

        # Remover duplicatas nas listas de dependências
        for entity in result_dict:
            result_dict[entity]['parents'] = list(set(result_dict[entity]['parents']))

        return result_dict

    def generate_path_to_RN(self):
        """Gera o caminho para a RN com base nas entidades identificadas."""
        filtered_entities = [entity for entity in self.entities if self.data[entity]["weight"] != 2]
        ordered_entities = sorted(filtered_entities, key=lambda e: self.data[e]["weight"])
        
        translated_entities = [
            self.translation_df.loc[self.translation_df["translation"] == entity, "entity"].values[0]
            for entity in ordered_entities
        ]

        return "/" + "/".join(translated_entities)
    
    def validate_relationship(self):
        for entity in self.entities:
            dependencies = self.data[entity]['parents']
            # Ignora dependências alternativas se pelo menos uma está presente
            if any(dep in self.entities for dep in dependencies):
                continue
            missing = [dep for dep in dependencies if dep not in self.entities]
            if missing:
                return False, missing, entity
        return True, [], ""

    def run_relationship_processing(self):
        valid, missing, main_entity = self.validate_relationship()

        if valid:
            path = self.generate_path_to_RN()
            result = {
                "success": True,
                "path_rn": path,
                "entitie": "",
                "missing": []
            }
        else:
            result = {
                "success": False,
                "path_rn": "",
                "entitie": main_entity,
                "missing": missing
            }

        return result