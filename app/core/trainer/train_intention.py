import pickle
import numpy as np
from sklearn.calibration import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer
from app.core.data.augmentation import DataAugmenterIntention
from app.core.data.cleaner import TextCleaner
from app.core.data.tokenizer import TokenizerWrapperIntention
from app.core.model.architectures.factory import ModelFactory
from app.database.processing import loads_entity_questions_training
from app.core.data.balancing import performing_data_balancing_intention
from config import conf_model
from pathlib import Path
from tensorflow.keras.callbacks import EarlyStopping

class TrainingIntentionPipeline:
    def __init__(self):
        self.config = conf_model.get_all()
        self.tokenizer = None
        self.label_encoders = {}
        self.model = None
        self.history = None
        self.mlb = None
        self.intention_encoder = None
        self.object_encoder = None

    def _ensure_directory(self, path):
        """Garante que o diretório exista."""
        Path(path).mkdir(parents=True, exist_ok=True)

    def save_components(self):
        """Salva o modelo e os componentes."""
        self._ensure_directory('mod/app/models/saved')
        self.model.save('mod/app/models/saved/intention_best_model.keras')

        with open('mod/app/models/saved/intention_tokenizer.pkl', 'wb') as f:
            pickle.dump(self.tokenizer, f)

        with open('mod/app/models/saved/intention_mlb.pkl', 'wb') as f:
            pickle.dump(self.mlb, f)

        # Salvar os encoders de intenção e objeto
        with open('mod/app/models/saved/intention_encoder.pkl', 'wb') as f:
            pickle.dump(self.intention_encoder, f)
        
        with open('mod/app/models/saved/object_encoder.pkl', 'wb') as f:
            pickle.dump(self.object_encoder, f)
        

        print("\nModelo e componentes salvos com sucesso!")

    def process_entities(self, df):
        """Transforma entidades em formato binário para treinamento."""
        self.mlb = MultiLabelBinarizer()
        df['entities'] = df['entities'].apply(lambda x: x.split(','))
        y_entities = self.mlb.fit_transform(df['entities'])
        return y_entities, self.mlb

    def processing_data_for_training(self):
        """Processa e prepara os dados para treinamento."""
        # Carregar os dados de treinamento
        df = loads_entity_questions_training()

        if df is not None and len(df) > 0:

            # Balancear os dados
            df_balanced = performing_data_balancing_intention(df, self.config['processing']['target_samples'])

            # Aumentar os dados
            augmenter = DataAugmenterIntention()
            expanded_df = augmenter.expand_dataset(df_balanced)

            # Limpar os textos
            cleaner = TextCleaner(self.config['processing']['cleaning'])
            expanded_df['question'] = expanded_df['question'].apply(cleaner.clean_text)

            return expanded_df

        return df
    
    def encode_training_data(self, df):
        """Tokeniza e codifica os dados de treinamento."""
        self.tokenizer = TokenizerWrapperIntention(self.config['processing'])
        X = self.tokenizer.fit_transform(df['question'])

        y_intention = df['intention'].values
        y_object = df['object'].values
        y_entities, mlb = self.process_entities(df)

        return X, y_intention, y_object, y_entities, mlb
    
    def train_model(self, X, y_intention, y_object, y_entities, mlb):
        """Cria e treina o modelo."""
        # Criar o modelo
        self.model = ModelFactory.create_model(
            model_type="intention",
            config=self.config['model_intention']
        )

        # Configurar Early Stopping
        early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

        # Converter rótulos textuais para numéricos usando LabelEncoder
        self.intention_encoder = LabelEncoder()
        self.object_encoder = LabelEncoder()

        y_intention = self.intention_encoder.fit_transform(y_intention) 
        y_object = self.object_encoder.fit_transform(y_object)

        # Garantir que y_entities seja do tipo float
        y_entities = np.array(y_entities, dtype=np.float32)

        # Garantir que X seja numérico
        X = np.array(X, dtype=np.float32)

        # Divisão do conjunto de dados
        X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)
        y_intention_train, y_intention_test = train_test_split(y_intention, test_size=0.2, random_state=42)
        y_object_train, y_object_test = train_test_split(y_object, test_size=0.2, random_state=42)
        y_entities_train, y_entities_test = train_test_split(y_entities, test_size=0.2, random_state=42)

        # Treinar o modelo
        self.history = self.model.fit(
            X_train,
            {
                "intention": y_intention_train,
                "object": y_object_train,
                "entities": y_entities_train
            },
            validation_data=(X_test,
            {
                "intention": y_intention_test,
                "object": y_object_test,
                "entities": y_entities_test
            }),
            batch_size=self.config['training']['batch_size'],
            epochs=self.config['training']['epochs'],
            verbose=1,
            callbacks=[early_stopping]
        )

        print("Treinamento concluído.")


    def run(self):
        """Executa o pipeline completo."""
        df = self.processing_data_for_training()
        if len(df) > 0:
            # Gera os dados tokenizados e codificados
            X, y_intention, y_object, y_entities, mlb = self.encode_training_data(df)
            
            # Passa os dados processados para o treinamento
            self.train_model(X, y_intention, y_object, y_entities, mlb)
        self.save_components()