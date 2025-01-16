from app.database.processing import loads_word_replacements
from typing import Dict
import unicodedata
import re
import pickle

class TextCleaner:
    def __init__(self, config: Dict):
        self.config = config
        self.word_replacements_default = {
            # Perguntas
            'qual': 'qual',
            'quanto': 'qual',
            'quais': 'qual',
            'onde': 'local',
            'como': 'modo',
            'quando': 'tempo',
            'porquê': 'motivo',
            'por que': 'motivo',
            'quem': 'pessoa',
            
            # Verbs and actions
            'tem': 'existe',
            'há': 'existe',
            'possui': 'existe',
        }
        self.word_replacements_database = loads_word_replacements()

    def clean_text(self, text: str) -> str:
        if self.config['lowercase']:
            text = text.lower()
        
        if self.config['remove_accents_and_special_characters']:
            text = self._remove_accents_and_special_characters(text)

        if self.config['remove_punctuation']:
            text = self._remove_punctuation(text)

        return self._normalize_words(text)

    def _remove_accents_and_special_characters(self, text: str) -> str:
        """ Remove todos os acentos e caracteres especiais"""
        return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')

    def _remove_punctuation(self, text: str) -> str:
        return re.sub(r'[^\w\s]', '', text)
    
    def _normalize_words(self, text: str) -> str:
        word_replacements = {**self.word_replacements_default,**self.word_replacements_database}
        words = text.split()
        return ' '.join(word_replacements.get(word, word) for word in words)
    
    def generate_word_replacements(self):
        word_replacements = {**self.word_replacements_default,**self.word_replacements_database}

        if len(word_replacements) > 0:
            with open("mod/app/models/saved/word_replacements.pkl", "wb") as f:
                pickle.dump(word_replacements, f)