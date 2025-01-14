from flask import request
from typing import Tuple, Dict, Any, List

class RequestValidator:
    @staticmethod
    def validate_json_request() -> Tuple[Dict[str, Any], int]:
        try:
            data = request.get_json(force=False)
            
            if data is None:
                return {
                    "error": "O corpo da requisição deve ser um JSON válido."
                }, 400
                
            if not data:
                return {
                    "error": "O corpo da requisição não pode estar vazio."
                }, 400
                
            return None
            
        except Exception as e:
            return {
                "error": f"Erro ao processar a requisição: {str(e)}"
            }, 400
    
    @staticmethod
    def validate_required_fields(data: dict, required_fields: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], int]:
        """
        Valida se todos os campos obrigatórios estão presentes e são do tipo correto.
        
        Args:
            data: Dicionário com os dados da requisição
            required_fields: Lista de dicionários com nome e tipo dos campos obrigatórios
        """
        missing_fields = []
        type_errors = []
        
        for field in required_fields:
            field_name = field['name']
            field_type = field['type']
            
            # Verifica se o campo existe
            if field_name not in data:
                missing_fields.append(field_name)
                continue
            
            # Verifica o tipo do campo
            if field_type == int:
                try:
                    data[field_name] = int(data[field_name])
                except (ValueError, TypeError):
                    type_errors.append(f"O campo '{field_name}' deve ser um número inteiro.")
            elif field_type == str:
                if not isinstance(data[field_name], str):
                    type_errors.append(f"O campo '{field_name}' deve ser uma string.")
            # Pode adicionar mais tipos conforme necessário
        
        if missing_fields:
            return {
                "error": f"Campos obrigatórios ausentes: {', '.join(missing_fields)}"
            }, 400
            
        if type_errors:
            return {
                "error": "Erro de validação de tipos",
                "details": type_errors
            }, 400
            
        return None