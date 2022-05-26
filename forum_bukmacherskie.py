import pandas as pd


read_file = pd.read_excel('typerzy.xlsx')
read_file.to_csv('typerzy.csv', index=None, header=True)

df = pd.read_csv('typerzy.csv', delimiter=',')
print(df)
