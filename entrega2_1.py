from pulp import *
import pandas as pd

## Definición de los parametros del problema

fichero_operaciones = "241204_datos_operaciones_programadas copy.xlsx"
fichero_costes = "241204_costes.xlsx"

df_operaciones = pd.read_excel(fichero_operaciones, index_col=0)
df_costes = pd.read_excel(fichero_costes, index_col=0)
df_operaciones.index = df_operaciones.index.str[9:]
df_costes.index = df_costes.index.str[0] + "-" + df_costes.index.str[10:]
df_costes.columns = df_costes.columns.str[9:]

operaciones = df_operaciones.index.to_list()
quirofranos = df_costes.index.to_list()

def L_i (ope) :
    L=[]
    a = df_operaciones.loc[ope, "Hora inicio "]
    b = df_operaciones.loc[ope, "Hora fin"]
    for i in operaciones :
        if df_operaciones.loc[i, "Hora inicio "] <= a and df_operaciones.loc[i, "Hora fin"] > a and df_operaciones.loc[i, "Hora fin"] <= b :
            L.append(i)
        elif df_operaciones.loc[i, "Hora inicio "] <= a and df_operaciones.loc[i, "Hora fin"] >= b :
            L.append(i)
        elif df_operaciones.loc[i, "Hora inicio "] >= a and df_operaciones.loc[i, "Hora fin"] <= b : 
            L.append(i)
        elif df_operaciones.loc[i, "Hora inicio "] >= a and df_operaciones.loc[i, "Hora inicio "] < b and df_operaciones.loc[i, "Hora fin"] >= b :
            L.append(i)
    L.remove(ope)        
    return L

## Modelo en Pulp

model = LpProblem("Affectacion_operaciones", LpMinimize)

x = LpVariable.dicts("x", [(i,j) for i in operaciones for j in quirofranos], cat ='Binary')

# Objetivo

model += lpSum([df_costes.loc[j, i]*x[(i,j)] for i in operaciones for j in quirofranos])

# Restricción 1

for i in operaciones:
    model += lpSum(x[(i,j)] for j in quirofranos) >= 1

# Restricción 2

for i in operaciones :
    for j in quirofranos : 
        A = L_i(i)
        model += lpSum([x[(h, j)] + x[(i,j)] for h in A]) <= 1

model.solve()
print(LpStatus[model.status])

