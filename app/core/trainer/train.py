import os
import pickle
from sklearn.preprocessing import MultiLabelBinarizer
from app.core.data.augmentation import DataAugmenter
from app.core.data.cleaner import TextCleaner
from app.core.data.tokenizer import TokenizerWrapper
from app.core.model.architectures.factory import ModelFactory
from app.core.trainer.trainer import ModelTrainer
from config import conf_model
from app.database.processing import loads_questions
from app.core.data.balancing import performing_data_balancing


class TrainingPipeline:
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
            
    def process_training_data(self,object):
        """Carrega inicialmente os dados iniciais"""
        df =  loads_questions(object)
        df_intention = df[['intention']].drop_duplicates()
        df_address = df[['intention','domain_address','domain_name' ]].drop_duplicates()

        """Faz os tratamentos de expanção e limpesa das questões"""
        if len(df) > 0:
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
    
    def save_components(self, path,name):
        """Salva o modelo e os componentes."""
        self._ensure_directory(path)
        self.model.save(os.path.join(path, f'{name}_best_model.keras'))

        with open(os.path.join(path, f'{name}_tokenizer.pkl'), 'wb') as f:
            pickle.dump(self.tokenizer, f)

        with open(os.path.join(path, f'{name}_mlb.pkl'), 'wb') as f:
            pickle.dump(self.mlb, f)

        print("\nModelo e componentes salvos com sucesso!")

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

    def run(self, object):
        """ Roda a pipeline completa de treinamento"""
        df_intention, df_address, df = self.process_training_data(object)
        
        for index,row in df_intention.iterrows():
            df_rotate = df_address[df_address['intention'] == row.intention]
            for index_address,row_address in df_rotate.iterrows():
                X, y = self.encode_training_data(df,row_address.domain_address)
                name,path = self.train_model(X, y,row_address.domain_address)
                histories, fold_results  = self.cross_validate(X, y,name,path)
            
        return {'message': 'treinamento concluído'}