from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

class TokenizerWrapperIntention:
    def __init__(self, config):
        self.config = config
        self.tokenizer = Tokenizer(num_words=config['vocab_size'])
        
    def fit(self, texts):
        self.tokenizer.fit_on_texts(texts)
        
    def transform(self, texts):
        # Converte textos para sequências
        sequences = self.tokenizer.texts_to_sequences(texts)
        max_len = max(len(seq) for seq in sequences)
        # Pad sequences para ter o mesmo tamanho
        padded_sequences = pad_sequences(
            sequences, 
            maxlen=self.config['max_length'],
            padding='post',
            truncating='post'
        )
        return padded_sequences
        
    def fit_transform(self, texts):
        self.fit(texts)
        return self.transform(texts)

class TokenizerWrapper:
    def __init__(self, config):
        self.config = config
        self.tokenizer = Tokenizer(num_words=config['vocab_size'])
        
    def fit(self, texts):
        self.tokenizer.fit_on_texts(texts)
        
    def transform(self, texts):
        # Converte textos para sequências
        sequences = self.tokenizer.texts_to_sequences(texts)
        # Pad sequences para ter o mesmo tamanho
        padded_sequences = pad_sequences(
            sequences, 
            maxlen=self.config['max_length'],
            padding='post',
            truncating='post'
        )
        return padded_sequences
        
    def fit_transform(self, texts):
        self.fit(texts)
        return self.transform(texts)