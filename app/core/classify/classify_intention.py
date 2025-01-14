import pickle
import numpy as np
from tensorflow.keras.models import load_model
from app.core.data.cleaner import TextCleaner
from app.core.data.tokenizer import TokenizerWrapperIntention


def classifier_intention(message, config):
    """
    Classifica uma mensagem com base no modelo treinado, com prints para debug.
    """
    model, tokenizer, mlb, intention_encoder, object_encoder = load_components()

    if not all([model, tokenizer, mlb, intention_encoder, object_encoder]):
        print("Falha ao carregar os componentes necessários para a classificação.")
        return {"error": "Falha ao carregar os componentes necessários para a classificação."}

    try:
        # Limpa e tokeniza a mensagem
        cleaner = TextCleaner(config)
        cleaned_message = cleaner.clean_text(message)
        
        sequence = tokenizer.transform([cleaned_message])

        # Realiza a predição
        predictions = model.predict(sequence, verbose=0)

        # Decodifica as previsões
        # Intenção
        intention_prediction_index = np.argmax(predictions[0])  # Predição de 'intention'
        intention_prediction = intention_encoder.inverse_transform([intention_prediction_index])[0]

        # Objeto
        object_prediction_index = np.argmax(predictions[1])  # Predição de 'object'
        object_prediction = object_encoder.inverse_transform([object_prediction_index])[0]

        # Entidades
        entities_prediction = [
            entity.replace('"', '').replace("'", "").strip().strip('[').strip(']')
            for entity, prob in zip(mlb.classes_, predictions[2][0])
            if prob >= 0.6  # Limiar de confiança
        ]

        return {
            "message": message,
            "intention": intention_prediction,
            "object": object_prediction,
            "entities": entities_prediction,
        }

    except Exception as e:
        print(f"Erro durante a classificação: {str(e)}")
        return {"error": f"Erro durante a classificação: {str(e)}"}



def load_components():
    """
    Carrega o modelo treinado e seus componentes.
    """
    try:
        # Carrega o modelo
        model = load_model("mod/app/models/saved/intention_best_model.keras")

        # Carrega o tokenizer
        with open("mod/app/models/saved/intention_tokenizer.pkl", "rb") as f:
            tokenizer = pickle.load(f)

        # Carrega o MultiLabelBinarizer
        with open("mod/app/models/saved/intention_mlb.pkl", "rb") as f:
            mlb = pickle.load(f)

        # Carrega os encoders de intenção e objeto
        with open("mod/app/models/saved/intention_encoder.pkl", "rb") as f:
            intention_encoder = pickle.load(f)

        with open("mod/app/models/saved/object_encoder.pkl", "rb") as f:
            object_encoder = pickle.load(f)

        return model, tokenizer, mlb, intention_encoder, object_encoder

    except Exception as e:
        print(f"Erro ao carregar componentes: {str(e)}")
        return None, None, None, None, None