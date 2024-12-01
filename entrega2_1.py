from pulp import *
import pandas as pd

## Definición de los parametros del problema

fichero_operaciones = "241204_datos_operaciones_programadas copy.xlsx"
fichero_costes = "241204_costes.xlsx"

df_operaciones = pd.read_excel(fichero_operaciones, index_col=0)
df_costes = pd.read_excel(fichero_costes, index_col=0)

#Simplificación de los nombres de las columnas y líneas
df_operaciones.index = df_operaciones.index.str[9:]
df_costes.index = df_costes.index.str[0] + "-" + df_costes.index.str[10:]
df_costes.columns = df_costes.columns.str[9:]

#Conversión de la horas a formato de 24 horas
df_operaciones['Hora inicio '] = pd.to_datetime(df_operaciones['Hora inicio '], format='%I:%M %p', errors='coerce').dt.strftime('%H:%M')
df_operaciones['Hora fin'] = pd.to_datetime(df_operaciones['Hora fin'], format='%I:%M %p', errors='coerce').dt.strftime('%H:%M')

#Selección de las operaciones de Cardiología Pediátrica
df_operaciones = df_operaciones[df_operaciones["Especialidad quirúrgica"] == "Cardiología Pediátrica"]
df_costes = df_costes[df_costes.columns.intersection(df_operaciones.index)]

#Creación de las listas de operaciones y quirofanos
operaciones = df_operaciones.index.to_list()
quirofranos = df_costes.index.to_list()

#Creacción de los L_i en el diccionario L
L = {operacion: [] for operacion in operaciones}
for i in range(len(operaciones)):
    hora_inicio_i = df_operaciones.loc[operaciones[i], "Hora inicio "]
    hora_fin_i = df_operaciones.loc[operaciones[i], "Hora fin"]
    for j in range (i + 1, len(operaciones)):
        hora_inicio_j = df_operaciones.loc[operaciones[j], "Hora inicio "]
        hora_fin_j = df_operaciones.loc[operaciones[j], "Hora fin"]
        if (hora_inicio_j <= hora_inicio_i and hora_fin_j >= hora_inicio_i #Si la operación j empieza antes de que acabe la operación i y acaba después de que empiece la operación i
            or hora_inicio_j <= hora_fin_i and hora_fin_j >= hora_fin_i #Si la operación j empieza antes de que acabe la operación i y acaba después de que acabe la operación i
            or hora_inicio_j >= hora_inicio_i and hora_fin_j <= hora_fin_i): #Si la operación j empieza después de que empiece la operación i y acaba antes de que acabe la operación i
            L[operaciones[i]].append(operaciones[j])
            L[operaciones[j]].append(operaciones[i])
print(L)
            
## Modelo en Pulp

model = LpProblem("Affectacion_operaciones", LpMinimize)
x = LpVariable.dicts("x", [(i,j) for i in operaciones for j in quirofranos], cat ='Binary')

# Objetivo
model += lpSum([df_costes.loc[j, i]*x[(i,j)] for i in operaciones for j in quirofranos])

# Restricción 1
for i in operaciones:
    model += lpSum(x[(i,j)] for j in quirofranos) >= 1

# Restricción 2
for i in operaciones:
    for j in quirofranos: 
        model += lpSum([x[(h, j)] for h in L[i]]) + x[(i,j)] <= 1

model.solve(PULP_CBC_CMD(msg=False))
print(LpStatus[model.status])
print(value(model.objective))
for j in quirofranos: 
    for i in operaciones: 
        if x[(i,j)].varValue == 1: 
            print (i, j)
