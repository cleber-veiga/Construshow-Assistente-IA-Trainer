import random
from typing import List, Tuple
import pandas as pd

class DataAugmenterIntention:
    def __init__(self, templates: List[str] = None):
        self.templates = templates or [
            "{}",
            "por favor, {}",
            "gostaria de saber {}",
            "me informe {}",
            "poderia me dizer {}",
            "você sabe {}?",
            "sabe me informar {}?",
            "tem como me dizer {}?",
            "consegue me ajudar com {}?",
            "quero saber {}",
            "me diga, {}",
            "{} por gentileza",
            "{} agora mesmo, por favor",
            "uma informação, {}",
            "oi, {}",
            "olá, {}",
            "dá pra me dizer {}?",
            "sabe {}?",
            "como seria {}?",
            "{} pode me ajudar",
            "{} é o que eu quero saber"
        ]

    def generate_variations(self, questions: List[Tuple[str, str, str, List[str]]]) -> List[Tuple[str, str, str, List[str]]]:
        variations = []
        for question, intention, object_, entities in questions:
            question = question.rstrip('?.,!')
            for template in self.templates:
                new_question = template.format(question)
                if not new_question.endswith('?'):
                    new_question += '?'
                variations.append((new_question, intention, object_, entities))
        return variations

    def expand_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        # Extrai as colunas relevantes
        questions = list(zip(df['question'], df['intention'], df['object'], df['entities']))
        # Gera as variações
        variations = self.generate_variations(questions)
        # Cria um novo DataFrame com as variações
        return pd.DataFrame(variations, columns=['question', 'intention', 'object', 'entities'])
    
class DataAugmenter:
    def __init__(self, templates: List[str] = None, max_variations_per_question: int = None):
        self.templates = templates or [
            "{}",
            "por favor, {}",
            "gostaria de saber {}",
            "me informe {}",
            "poderia me dizer {}",
            "você sabe {}?",
            "sabe me informar {}?",
            "tem como me dizer {}?",
            "consegue me ajudar com {}?",
            "quero saber {}",
            "me diga, {}",
            "{} por gentileza",
            "{} agora mesmo, por favor",
            "uma informação, {}",
            "oi, {}",
            "olá, {}",
            "dá pra me dizer {}?",
            "sabe {}?",
            "como seria {}?",
            "{} pode me ajudar",
            "{} é o que eu quero saber"
        ]
        self.max_variations_per_question = max_variations_per_question

    def generate_variations(self, questions: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
        variations = []
        for question, domain_name, domain_address in questions:
            question = question.rstrip('?.,!')
            selected_templates = self.templates
            if self.max_variations_per_question and len(self.templates) > self.max_variations_per_question:
                selected_templates = random.sample(self.templates, self.max_variations_per_question)
            for template in selected_templates:
                new_question = template.format(question)
                if not new_question.endswith('?'):
                    new_question += '?'
                variations.append((new_question, domain_name, domain_address))
        return variations

    def expand_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        # Extrair as colunas relevantes
        questions = list(zip(df['question'], df['domain_name'], df['domain_address']))
        # Gerar variações
        variations = self.generate_variations(questions)
        # Criar um novo DataFrame com as colunas desejadas
        return pd.DataFrame(variations, columns=['question', 'domain_name', 'domain_address'])