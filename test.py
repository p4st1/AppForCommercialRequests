import pandas as pd

df = pd.read_csv('data/2.csv', header=None, sep=';') 

for row in range(len(df[0])):
    for col in df:
        print(df[col][row])
