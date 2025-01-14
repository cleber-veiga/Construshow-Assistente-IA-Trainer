import tensorflow as tf
from tensorflow.keras.models import Model,Sequential
from tensorflow.keras.layers import Input, Embedding, Conv1D, MaxPooling1D, Bidirectional, GRU, Dense, Dropout, LayerNormalization,LSTM

class ModelFactory:
    @staticmethod
    def create_model(model_type: str, config: dict):
        """
        Cria o modelo com base no tipo e na configuração fornecida.

        Args:
            model_type (str): Tipo do modelo ("multilabel").
            config (dict): Configurações do modelo (hiperparâmetros).

        Returns:
            tf.keras.Model: Modelo compilado.
        """
        if model_type == "multilabel":
            return ModelFactory._create_multilabel_model(config)
        
        elif model_type == "intention":
            return ModelFactory._create_multilabel_model_intention(config)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

    @staticmethod
    def _create_multilabel_model(config):
        model = Sequential([
            Embedding(
                input_dim=config['vocab_size'],
                output_dim=config['embedding_dim'],
                input_length=config['max_length']
            ),
            Conv1D(64, 5, activation='relu', padding='same'),
            MaxPooling1D(2),
            Bidirectional(LSTM(32, return_sequences=True, recurrent_dropout=0.2)),
            Bidirectional(LSTM(16, recurrent_dropout=0.2)),
            LayerNormalization(),  # Estabiliza o aprendizado
            Dense(config['dense_units'], activation='relu'),
            Dropout(config['dropout_rate']),
            Dense(config['dense_units'] // 2, activation='relu'),
            Dropout(config['dropout_rate']),
            Dense(config['num_classes'], activation='sigmoid')  # Multirrótulo
        ])

        model.build(input_shape=(None, config['max_length']))
        print(model.summary())

        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',  # Multirrótulo
            metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
        )

        return model
    
    @staticmethod
    def _create_multilabel_model_intention(config):
        """
        Cria o modelo com múltiplas saídas para classificação.

        Args:
            config (dict): Configurações do modelo.

        Returns:
            tf.keras.Model: Modelo compilado.
        """
        # Entrada
        input_layer = Input(shape=(config['max_length'],), name="input")

        # Embedding + Convolution + GRU
        embedding = Embedding(
            input_dim=config['vocab_size'],
            output_dim=config['embedding_dim'],
            input_length=config['max_length']
        )(input_layer)

        conv1d = Conv1D(
            filters=config['filters'],
            kernel_size=config['kernel_size'],
            activation='relu',
            padding='same'
        )(embedding)

        pooling = MaxPooling1D(pool_size=2)(conv1d)

        gru = Bidirectional(
            GRU(
                config['lstm_units'],
                return_sequences=True,
                recurrent_dropout=config['recurrent_dropout']
            )
        )(pooling)

        gru_output = Bidirectional(
            GRU(
                config['lstm_units'],
                recurrent_dropout=config['recurrent_dropout']
            )
        )(gru)

        normalized = LayerNormalization()(gru_output)

        # Camadas densas compartilhadas
        dense_shared = Dense(config['dense_units'], activation='relu')(normalized)
        dropout_shared = Dropout(config['dropout_rate'])(dense_shared)

        # Saídas específicas
        intention_output = Dense(
            config['num_intentions'], activation='softmax', name='intention'
        )(dropout_shared)

        object_output = Dense(
            config['num_objects'], activation='softmax', name='object'
        )(dropout_shared)

        entities_output = Dense(
            config['num_entities'], activation='sigmoid', name='entities'
        )(dropout_shared)

        # Modelo
        model = Model(
            inputs=input_layer,
            outputs=[intention_output, object_output, entities_output]
        )

        # Compilação do modelo
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=config['learning_rate']),
            loss={
                'intention': 'sparse_categorical_crossentropy',
                'object': 'sparse_categorical_crossentropy',
                'entities': 'binary_crossentropy'
            },
            metrics={
                'intention': 'accuracy',
                'object': 'accuracy',
                'entities': 'accuracy'
            }
        )

        model.summary()
        return model
