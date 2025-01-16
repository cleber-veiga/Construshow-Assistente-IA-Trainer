import os
from app.api.v1.utils.identify_relationship import ClassifyRelationship
from app.api.v1.utils.request_validators import RequestValidator
from flask import jsonify, make_response, request
from flask_restful import Resource
from app.core.classify.classify import classifier
from app.core.trainer.train_intention import TrainingIntentionPipeline
from app.core.classify.classify_intention import classifier_intention
from app.core.trainer.training import TrainingIntentionManangerPipeline, TrainingManangerPipeline
from config import conf_model
from app.core.trainer.train import TrainingPipeline
from app.api.v1.utils.split import split_message,remove_duplicate_dicts

class ChatTrainerManager(Resource):
    def get(self):
        
        """ Treinamento do modelo de Intenções"""
        pipeline_intention = TrainingIntentionManangerPipeline()
        pipeline_intention.run()

        """ Treinamento do modelo de classificação"""
        pipeline_main = TrainingManangerPipeline()
        pipeline_main.run()

        """ Gera os arquivos de relacionamento das entidades"""
        pipeline_relationship = ClassifyRelationship(['training'])
        pipeline_relationship.generate_entity_relationship()
        
        return {"message": "Treinamento concluído!"}

class ChatTrainerIntentionResource(Resource):
    def get(self):
        
        """ Busca dados para treinamento"""
        pipeline = TrainingIntentionPipeline()
        pipeline.run()
    
        return {"message": "Treinamento concluído!"}
    
    def post(self):
        """Realiza validação da estrutura do JSON recebido"""
        validation_error = RequestValidator.validate_json_request()
        if validation_error:
            return validation_error

        try:
            data = request.get_json()

            """Realiza validação dos campos obrigatórios"""
            required_fields = [
                {'name': 'message', 'type': str}
            ]

            field_validation_error = RequestValidator.validate_required_fields(data, required_fields)
            if field_validation_error:
                return field_validation_error
            
            message = data['message']

            result = classifier_intention(message,conf_model.get('processing.cleaning'))
            print(result)
            response = make_response(jsonify(result), 200)  # Código 200 ou outro status apropriado
            response.headers["Content-Type"] = "application/json"
            return response
        
        except Exception as e:
            error_response = {
                "error": f"Erro no processamento da requisição: {str(e)}"
            }
            return jsonify(error_response), 500

class ChatTrainerResource(Resource):
    def get(self):
        return {"message": "Chat Trainer API endpoint"}
    
    def post(self):
        """Realiza validação da estrutura do JSON recebido"""
        validation_error = RequestValidator.validate_json_request()
        if validation_error:
            return validation_error

        try:
            data = request.get_json()

            """Realiza validação dos campos obrigatórios"""
            required_fields = [
                {'name': 'object', 'type': str}
            ]

            field_validation_error = RequestValidator.validate_required_fields(data, required_fields)
            if field_validation_error:
                return field_validation_error
            
            object = data['object']

            training = TrainingPipeline()
            training.run(object)

            classify_relation = ClassifyRelationship(['training'])
            classify_relation.generate_entity_relationship()

            response = make_response(jsonify(object), 200) 
            response.headers["Content-Type"] = "application/json"
            return response
        
        except Exception as e:
            error_response = {
                "error": f"Erro no processamento da requisição: {str(e)}"
            }
            return jsonify(error_response), 500

class ChatTrainerDomainResource(Resource):
    def post(self):
        """Realiza validação da estrutura do JSON recebido"""
        validation_error = RequestValidator.validate_json_request()
        if validation_error:
            return validation_error

        try:
            data = request.get_json()

            """Realiza validação dos campos obrigatórios"""
            required_fields = [
                {'name': 'message', 'type': str}
            ]

            field_validation_error = RequestValidator.validate_required_fields(data, required_fields)
            if field_validation_error:
                return field_validation_error
            
            message = data['message']
            validation_entities = []

            sub_messages = split_message(message)
            for idx, sub_msg in enumerate(sub_messages):
                result = classifier_intention(sub_msg,conf_model.get('processing.cleaning'))

                classify_relation = ClassifyRelationship(result['entities'])
                response_identify= classify_relation.run_relationship_processing()
                string_intention = 'search' if result['intention'] == 'BUSCAR_DADO' else 'doubt'
                validation_entities.append(response_identify)
                validation_entities[idx]['shot_message'] = sub_msg
                validation_entities[idx]['string_intention'] = string_intention

            validation_entities = remove_duplicate_dicts(validation_entities)
            
            trust_scores = {}
            for item in validation_entities:
                for chave, valor in item.items():
                    if chave == 'shot_message':
                        sub_msg = valor
                    if chave == 'path_rn':
                        string_domain = valor
                    if chave == 'string_intention':
                        string_intention = valor
                sub_msg, domains, trust, mlb = classifier(sub_msg,string_intention + string_domain,conf_model.get('processing.cleaning'))

                for domain in domains:
                    index = list(mlb.classes_).index(domain)  # Localiza o índice da categoria no MultiLabelBinarizer
                    score = trust[index]  # Associa a confiança correta
                    
                    # Atualiza ou adiciona a maior confiança para a categoria
                    if domain not in trust_scores or trust_scores[domain]['trust'] < score:
                        trust_scores[idx] = {'domain': domain, 'trust': score, 'short_message': sub_msg}

            response_data = {
                idx: {
                    'domain': v['domain'],  # Inclui o domínio, se necessário
                    'trust': float(v['trust']),
                    'short_message': v['short_message']
                }
                for idx, (_, v) in enumerate(sorted(trust_scores.items(), key=lambda item: item[0]))
            }

            response = make_response(jsonify(response_data))
            response.status_code = 200
            return response
        
        except Exception as e:
            error_response = {
                "error": f"Erro no processamento da requisição: {str(e)}"
            }
            return error_response, 500