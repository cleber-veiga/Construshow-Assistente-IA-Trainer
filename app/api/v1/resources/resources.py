from app.api.v1.utils.request_validators import RequestValidator
from flask import jsonify, make_response, request
from flask_restful import Resource
from app.core.trainer.train_intention import TrainingIntentionPipeline
from app.core.classify.classify_intention import classifier_intention
from config import conf_model
from app.core.trainer.train import TrainingPipeline

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

            response = make_response(jsonify(object), 200) 
            response.headers["Content-Type"] = "application/json"
            return response
        
        except Exception as e:
            error_response = {
                "error": f"Erro no processamento da requisição: {str(e)}"
            }
            return jsonify(error_response), 500
class ChatTrainerDomainResource(Resource):
    pass