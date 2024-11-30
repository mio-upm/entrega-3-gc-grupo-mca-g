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

# Selección de las operaciones de Cardiología Pediátrica, Cirugía Cardíaca Pediátrica, Cirugía Cardiovascular, Cirugía General y del Aparato Digestivo
especialidades = [
    "Cardiología Pediátrica", 
    "Cirugía Cardíaca Pediátrica", 
    "Cirugía Cardiovascular", 
    "Cirugía General y del Aparato Digestivo"
]
df_operaciones = df_operaciones[df_operaciones['Especialidad quirúrgica'].isin(especialidades)]
df_costes = df_costes[df_costes.columns.intersection(df_operaciones.index)]
# df_operaciones = df_operaciones[df_operaciones["Especialidad quirúrgica"] == "Cardiología Pediátrica"]
# df_costes = df_costes[df_costes.columns.intersection(df_operaciones.index)]

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

def generacion_planificacion(operaciones, L):
    plannificaciones = [[]]
    for i in operaciones:
        esAfectado = False
        for p in range(len(plannificaciones)):
            if esAfectado:
                break
            if plannificaciones[p] == []:
                plannificaciones[p].append(i)
                esAfectado = True
            else:
                esIncompatible = False
                for operacion in plannificaciones[p]:
                    if i in L[operacion]:
                        esIncompatible = True
                        break 
                if not esIncompatible:
                    plannificaciones[p].append(i)
                    esAfectado = True
        if not esAfectado:
            plannificaciones.append([i])
    return plannificaciones
                   
# print(len(generacion_planificacion(operaciones, L)))

A = generacion_planificacion(operaciones, L)

def B(i,k):
    if i in k :
        return 1
    else :
        return 0

def C_chapeau(k) :
    n = len(quirofranos)
    s = 0
    for i in range (n) :
        s = s + df_costes.loc[quirofranos[i]][k]
    return s / n

print(C_chapeau("OP-68"))

def C(k) :
    s = 0
    for i in operaciones :
        s = s + B[(i,k)] * C_chapeau(i)
    return s

model = LpProblem("Set_covering", LpMinimize)

y = LpVariable.dicts("y", [k for k in A], cat ='Binary')

model += lpSum ([y[k]*C(k) for k in A])

for i in operaciones :
    model += lpSum([y[k]*B(i,k) for k in A]) >= 1
