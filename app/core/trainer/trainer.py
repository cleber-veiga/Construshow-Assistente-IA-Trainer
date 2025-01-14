from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from sklearn.model_selection import KFold
import numpy as np
import os

class ModelTrainer:
    def __init__(self, config, path,name):
        self.config = config
        self.path = path
        self.name = name
        self.callbacks = self._create_callbacks()
        os.makedirs('mod/app/models/saved', exist_ok=True)

    def _create_callbacks(self):
        return [
            EarlyStopping(
                monitor='val_loss',
                patience=self.config['early_stopping_patience'],
                restore_best_weights=True
            ),
            ModelCheckpoint(
                os.path.join(self.path, f'{self.name}_best_model.keras'),
                monitor='val_loss',
                save_best_only=True
            ),
            ReduceLROnPlateau(
                monitor='val_loss',  # Métrica monitorada
                factor=0.5,          # Fator de redução da taxa de aprendizado
                patience=2,          # Número de épocas sem melhora antes de reduzir
                min_lr=1e-6          # Limite inferior para a taxa de aprendizado
            )
        ]

    def train_with_validation(self, model, X, y):
        return model.fit(
            X, y,
            batch_size=self.config['batch_size'],
            epochs=self.config['epochs'],
            validation_split=self.config['validation_split'],
            callbacks=self.callbacks
        )

    def train_with_cross_validation(self, model_factory, X, y, class_weight=None, n_splits=2):
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        histories = []
        fold_results = []

        # Converter X e y para arrays numpy se não forem
        X = np.array(X)
        y = np.array(y)

        for fold, (train_idx, val_idx) in enumerate(kf.split(X)):
            print(f'\nFold {fold + 1}/{n_splits}')

            # Separar dados de treino e validação
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            # Mostrar tamanho dos conjuntos
            print(f"Tamanho do conjunto de treino: {len(X_train)}")
            print(f"Tamanho do conjunto de validação: {len(X_val)}")
            print(f"Shape dos dados de treino: {X_train.shape}")
            print(f"Shape dos dados de validação: {X_val.shape}")

            # Criar novo modelo para cada fold
            model = model_factory(self.config)

            # Treinar modelo
            history = model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                batch_size=self.config['batch_size'],
                epochs=self.config['epochs'],
                callbacks=self.callbacks,
                class_weight=class_weight,  # Adiciona class_weight aqui
                verbose=1
            )

            histories.append(history)

            # Avaliar modelo no conjunto de validação
            results = model.evaluate(X_val, y_val, verbose=0)
            metrics = {name: value for name, value in zip(model.metrics_names, results)}

            val_loss = metrics.get('loss', None)
            val_accuracy = metrics.get('accuracy', None)
            val_auc = metrics.get('auc', None)

            print(f"\nResultados do Fold {fold + 1}:")
            print(f"Validation Loss: {val_loss:.4f}")
            if val_accuracy is not None:
                print(f"Validation Accuracy: {val_accuracy:.4f}")
            if val_auc is not None:
                print(f"Validation AUC: {val_auc:.4f}")

            fold_results.append(metrics)

        return histories, fold_results
