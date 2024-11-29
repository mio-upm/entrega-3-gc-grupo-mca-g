from pulp import *
import pandas as pd

fichier_excel = "241204_datos_operaciones_programadas.xlsx"
df = pd.read_excel(fichier_excel, index_col= 0)
operaciones = df.index.tolist()

print(df)

fichier_excel_2 = "241204_costes.xlsx"
df_2 = pd.read_excel(fichier_excel_2, index_col=0)
quirofanos = df_2.iloc[:, 0]

df['Hora inicio'] = pd.to_datetime(df['Hora inicio'])
df['Hora fin'] = pd.to_datetime(df['Hora fin'])

print (df.loc['20241204 OP-159', 'Hora inicio'])


model = LpProblem("Affectacion_operaciones", LpMinimize)

x = LpVariable.dicts("x", [(i,j) for i in operaciones for j in quirofanos], cat ='Binary')

model += lpSum([df_2.loc[i,j]*x[(i,j)] for i in quirofanos for j in operaciones])

for i in operaciones:
    model += lpSum(x[(i,j)] for j in quirofanos) >= 1

for i in operaciones :
    L=[]

    L.append()

    for h in L : 
        model += lpSum([x[(h,j)]+x[(i,j)] for i in operaciones for j in quirofanos])