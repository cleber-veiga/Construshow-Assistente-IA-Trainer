import pandas as pd
from sklearn.utils import resample

def performing_data_balancing_intention(df, target_samples=50):
    balanced_dfs = []
    intentions = df['intention'].unique()  # Agora usamos a coluna 'intention'
    
    for intention in intentions:
        intention_df = df[df['intention'] == intention]
        
        # Se tiver mais samples que o alvo, faz undersampling
        if len(intention_df) > target_samples:
            balanced_intention = resample(
                intention_df,
                replace=False,
                n_samples=target_samples,
                random_state=42
            )
        # Se tiver menos samples que o alvo, faz oversampling
        elif len(intention_df) < target_samples:
            balanced_intention = resample(
                intention_df,
                replace=True,
                n_samples=target_samples,
                random_state=42
            )
        else:
            balanced_intention = intention_df
            
        balanced_dfs.append(balanced_intention)
    
    # Combina todos os dataframes balanceados
    df_balanced = pd.concat(balanced_dfs)
    
    print("\nDistribuição das intenções após balanceamento:")
    print(df_balanced['intention'].value_counts())
    
    return df_balanced

def performing_data_balancing(df, target_samples=100):
    balanced_dfs = []
    domains = df['domain_name'].unique()
    
    for domain in domains:
        domain_df = df[df['domain_name'] == domain]
        
        # Se tiver mais samples que o alvo, faz undersampling
        if len(domain_df) > target_samples:
            balanced_domain = resample(
                domain_df,
                replace=False,
                n_samples=target_samples,
                random_state=42
            )
        # Se tiver menos samples que o alvo, faz oversampling
        elif len(domain_df) < target_samples:
            balanced_domain = resample(
                domain_df,
                replace=True,
                n_samples=target_samples,
                random_state=42
            )
        else:
            balanced_domain = domain_df
            
        balanced_dfs.append(balanced_domain)
    
    # Combina todos os dataframes balanceados
    df_balanced = pd.concat(balanced_dfs)
    
    print("\nDistribuição dos domínios após balanceamento:")
    print(df_balanced['domain_name'].value_counts())
    
    return df_balanced