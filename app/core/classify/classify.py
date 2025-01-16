import pickle
from tensorflow.keras.models import load_model
from app.core.data.cleaner import TextCleaner

def classifier(message,domain,config):
    try:

        # Carrega modelo e componentes
        model, tokenizer, mlb = load_components(domain)
        
        cleaner = TextCleaner(config)
        message = cleaner.clean_text(message)

        if message:
            # Processa e classifica
            domains, trust = predict_domain(
                message,
                tokenizer,
                model,
                mlb,
                confidence_threshold=0.6
            )
        return message, domains, trust, mlb  # Retorna mlb também

    except Exception as e:
        return f"\nErro: {str(e)}"

def load_components(domain):
    try:
        domain_split = domain.split('/')
        domain_convert = f'{domain_split[0]}_{domain_split[1]}_{domain_split[2]}'

        # Carrega o modelo
        model = load_model(f'mod/app/models/saved/{domain}/{domain_convert}_best_model.keras')
    
        # Carrega o tokenizer
        with open(f'mod/app/models/saved/{domain}/{domain_convert}_tokenizer.pkl', 'rb') as f:
            tokenizer = pickle.load(f)
        
        # Carrega o MultiLabelBinarizer
        with open(f'mod/app/models/saved/{domain}/{domain_convert}_mlb.pkl', 'rb') as f:
            mlb = pickle.load(f)
        
        return model, tokenizer, mlb
    except Exception as e:
       print(f"\nErro ao carregar componentes: {str(e)}")
       return None, None, None


def predict_domain(text, tokenizer, model, mlb, confidence_threshold=0.6):
    
    sequence = tokenizer.transform([text])
    
    predictions = model.predict(sequence, verbose=0)[0]

    selected_domains = [
        domain for domain, prob in zip(mlb.classes_, predictions)
        if prob >= 0.6
    ]
    
    return selected_domains, predictions
