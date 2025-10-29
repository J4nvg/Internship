from scipy.stats import binomtest
import pandas as pd
import os


print(os.listdir('./'))


for file in os.listdir('./'):
    if not file.endswith('.csv'):
        continue
    df = pd.read_csv(file,header = 0, sep=None, engine='python')
    all_colls = list(df.columns.values)
    if 'all_hiders_found' in all_colls:
        df_new = df.drop(columns=['all_hiders_found'])
        df_new.to_csv(file,sep='\t', encoding='utf-8', header=True)

    elif 'all_found.1' in all_colls:
        df_new = df.drop(columns=['all_found.1'])
        df_new.to_csv(file,sep='\t', encoding='utf-8', header=True)

    else:
        df.to_csv(file,sep='\t', encoding='utf-8', header=True)

    # print(df,df_new)

