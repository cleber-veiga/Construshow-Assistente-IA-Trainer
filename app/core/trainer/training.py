import os
import pickle
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import make_pipeline
from sklearn.metrics import classification_report
from sklearn.preprocessing import MultiLabelBinarizer
import spacy
from app.core.data.augmentation import DataAugmenter, DataAugmenterIntention
from app.core.data.balancing import performing_data_balancing, performing_data_balancing_intention
from app.core.data.cleaner import TextCleaner
from app.core.data.tokenizer import TokenizerWrapper
from app.core.model.architectures.factory import ModelFactory
from app.core.trainer.trainer import ModelTrainer
from config import conf_model
from app.database.processing import loads_entity_questions_training, loads_questions_all

class TrainingManangerPipeline:
    def __init__(self):
        self.tokenizer = None
        self.mlb = None
        self.model = None
        self.history = None
        self.config = conf_model.get_all()

    def _ensure_directory(self, path):
        """Garante que o diretório exista."""
        if not os.path.exists(path):
            os.makedirs(path)
            
    def save_components(self, path,name):
        """Salva o modelo e os componentes."""
        self._ensure_directory(path)
        self.model.save(os.path.join(path, f'{name}_best_model.keras'))

        with open(os.path.join(path, f'{name}_tokenizer.pkl'), 'wb') as f:
            pickle.dump(self.tokenizer, f)

        with open(os.path.join(path, f'{name}_mlb.pkl'), 'wb') as f:
            pickle.dump(self.mlb, f)

        print("\nModelo e componentes salvos com sucesso!")

    def process_training_data(self):
        """Carrega inicialmente os dados iniciais"""
        df =  loads_questions_all()
        df_intention = df[['intention']].drop_duplicates()
        df_address = df[['intention','domain_address','domain_name' ]].drop_duplicates()

        """Faz os tratamentos de expanção e limpesa das questões"""
        if df is not None and len(df) > 0:
            df_balanced = performing_data_balancing(df, self.config['processing']['target_samples'])

            augmenter = DataAugmenter(max_variations_per_question=self.config['processing']['max_variations'])
            expanded_df = augmenter.expand_dataset(df_balanced)

            cleaner = TextCleaner(self.config['processing']['cleaning'])
            expanded_df['question'] = expanded_df['question'].apply(cleaner.clean_text)
            
            cleaner.generate_word_replacements()
        return df_intention, df_address,expanded_df

    def encode_training_data(self, df, domain_address):
        df_filtered = df[df['domain_address'] == domain_address]
        
        """Tokeniza e codifica os dados de treinamento."""
        self.tokenizer = TokenizerWrapper(self.config['processing'])
        X = self.tokenizer.fit_transform(df_filtered['question'])

        self.mlb = MultiLabelBinarizer()
        df_filtered['domain_name'] = df_filtered['domain_name'].apply(lambda x: [x])
        y = self.mlb.fit_transform(df_filtered['domain_name'])

        print("Classes reconhecidas:", self.mlb.classes_)

        return X, y
    
    def train_model(self, X, y,domain_address):
        """Cria e treina o modelo."""
        self.model = ModelFactory.create_model(
            model_type="multilabel",
            config=self.config['model']
        )

        self.history = self.model.fit(
            X, y,
            batch_size=self.config['training']['batch_size'],
            epochs=self.config['training']['epochs'],
            validation_split=self.config['training']['validation_split'],
            verbose=1
        )

        name = domain_address.replace('/', '_')
        path = 'mod/app/models/saved/' + domain_address + '/'
        self.save_components(path,name)

        return name,path
    
    def cross_validate(self, X, y,name,path):
        trainer = ModelTrainer(self.config['training'],path,name)

        def model_factory_wrapped(_):
            return ModelFactory.create_model(
                model_type="multilabel",
                config=self.config['model']
            )

        return trainer.train_with_cross_validation(model_factory=model_factory_wrapped, X=X, y=y)
    
    def run(self):
        """ Roda a pipeline completa de treinamento"""
        df_intention, df_address, df = self.process_training_data()
        
        for index,row in df_intention.iterrows():
            df_rotate = df_address[df_address['intention'] == row.intention]
            for index_address,row_address in df_rotate.iterrows():
                X, y = self.encode_training_data(df,row_address.domain_address)
                name,path = self.train_model(X, y,row_address.domain_address)
                histories, fold_results  = self.cross_validate(X, y,name,path)
            
        return {'message': 'treinamento concluído'}

class TrainingIntentionManangerPipeline:
    def __init__(self):
        self.model = None
        self.config = conf_model.get_all()
        self.nlp = spacy.load('mod/app/models/pt_core_news_md-3.8.0')

    def processing_data_for_training(self):
        """Processa e prepara os dados para treinamento."""
        # Carregar os dados de treinamento
        df = loads_entity_questions_training()
        df = df[['question','intention']]

        if df is not None and len(df) > 0:
            df_balanced = performing_data_balancing_intention(df, self.config['processing']['target_samples'])

            augmenter = DataAugmenterIntention()
            expanded_df = augmenter.expand_dataset(df_balanced)

            cleaner = TextCleaner(self.config['processing']['cleaning'])
            expanded_df['question'] = expanded_df['question'].apply(cleaner.clean_text)

            return expanded_df

        return df

    def train_model(self,df):
        X_train, X_test, y_train, y_test = train_test_split(
            df["question"], df["intention"], test_size=0.2, random_state=42
        )

        self.model = make_pipeline(
            TfidfVectorizer(max_features=10000),
            SGDClassifier(loss="log_loss", random_state=42)
        )

        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        print(classification_report(y_test, y_pred))

    def save_components(self):
        """Salva o modelo e os componentes."""
        joblib.dump(self.model, "mod/app/models/saved/model_predicting_intentions.joblib")

        print("\nModelo salvo com sucesso!")

    def run(self):
        """Executa o pipeline completo."""
        df = self.processing_data_for_training()

        if df is not None and len(df) > 0:
            self.train_model(df)
            self.save_components()