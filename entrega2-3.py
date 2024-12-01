from pulp import *
import pandas as pd
import random

##Preparación de los datos

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

#Creación de las listas de operaciones y quirofanos
operaciones = df_operaciones.index.to_list()
quirofranos = df_costes.index.to_list()

#Creacción de los L_i en el diccionario L para las incompatibilidades
L = {operacion: [] for operacion in operaciones} #Inicializamos L[operacion] con []
for i in range(len(operaciones)):
    hora_inicio_i = df_operaciones.loc[operaciones[i], "Hora inicio "]
    hora_fin_i = df_operaciones.loc[operaciones[i], "Hora fin"]
    for j in range (i + 1, len(operaciones)):
        hora_inicio_j = df_operaciones.loc[operaciones[j], "Hora inicio "]
        hora_fin_j = df_operaciones.loc[operaciones[j], "Hora fin"]
        if (hora_inicio_j <= hora_inicio_i and hora_fin_j > hora_inicio_i #Si la operación j empieza antes de que acabe la operación i y acaba después de que empiece la operación i
            or hora_inicio_j < hora_fin_i and hora_fin_j >= hora_fin_i #Si la operación j empieza antes de que acabe la operación i y acaba después de que acabe la operación i
            or hora_inicio_j >= hora_inicio_i and hora_fin_j <= hora_fin_i): #Si la operación j empieza después de que empiece la operación i y acaba antes de que acabe la operación i
            L[operaciones[i]].append(operaciones[j])
            L[operaciones[j]].append(operaciones[i])

def generacion_planificacion(operaciones, L, limite_tamano = 10000, plannificaciones = [[]]):
    """
    Genera premieras planificaciónnes de operaciones en quirofanos, para que cada operació aparezca una vez

    Parametros:
        operaciones (list): Lista de operaciones
        L (dict): Diccionario de incompatibilidades
        limite_tamano (int): Número máximo de operaciones por planificación
        plannificaciones (list): Lista de planificaciones

    Returns:
        plannificaciones (list): Lista de planificaciones 
    
    """
    random.shuffle(operaciones) #Mezclamos el conjunto de las operaciones
    for i in operaciones:
        esAfectado = False
        for p in range(len(plannificaciones)):
            if esAfectado: #Si la operación ya ha sido asignada a una planificación, salimos del bucle
                break
            if plannificaciones[p] == []:
                plannificaciones[p].append(i)
                esAfectado = True
            else:
                esIncompatible = False
                for operacion in plannificaciones[p]: #Para una operación dada, verificamos que no tiene incompatibilidades con las operaciones ya asignadas a la planificación p
                    if i in L[operacion] or len(plannificaciones[p]) >= limite_tamano:
                        esIncompatible = True
                        break 
                if not esIncompatible:
                    plannificaciones[p].append(i)
                    esAfectado = True
        if not esAfectado:
            plannificaciones.append([i])
    return plannificaciones


def Modelo_unidimensional(patrones, operaciones):
    """
    Modelo unidimensional para la generación de columnas

    Parametros:
        patrones (DataFrame): DataFrame con los patrones
        operaciones (list): Lista de operaciones

    Returns:
        precio_sombra (dict): Diccionario con los precios sombra
        x_values (dict): Diccionario con los valores de x
    """
    numero_patrones = patrones.columns.to_list() #Definición del conjunto de patrones

    #Creación del modelo
    modelo = LpProblem("Asignación_quirofranos", LpMinimize)
    x = LpVariable.dicts("x", numero_patrones, lowBound=0, cat='Continuous')

    #Objetivo
    modelo += lpSum([x[i] for i in numero_patrones])

    #Resricciones
    for operacion in operaciones:
        modelo += lpSum([patrones.loc[operacion][j] * x[j] for j in numero_patrones]) >= 1

    #Ejecución
    modelo.solve(PULP_CBC_CMD(msg=False))
    precio_sombra = [constraint.pi for constraint in modelo.constraints.values()]
    precio_sombra = {operaciones[i]: precio_sombra[i] for i in range(len(operaciones))}
    x_values = {i: x[i].varValue for i in numero_patrones}
    return precio_sombra, x_values

def Modelo_unidimensional_binario(patrones, operaciones):
    """
    Modelo unidimensional para la generación de columnas con las variables binarias

    Parametros:
        patrones (DataFrame): DataFrame con los patrones
        operaciones (list): Lista de operaciones

    Returns:
        precio_sombra (dict): Diccionario con los precios sombra
        x_values (dict): Diccionario con los valores de x
    """
    numero_patrones = patrones.columns.to_list() 
    modelo = LpProblem("Asignación_quirofranos", LpMinimize)
    x = LpVariable.dicts("x", numero_patrones, lowBound=0, cat='Binary') #Variables binarias
    modelo += lpSum([x[i] for i in numero_patrones])
    for operacion in operaciones:
        modelo += lpSum([patrones.loc[operacion][j] * x[j] for j in numero_patrones]) >= 1
    modelo.solve(PULP_CBC_CMD(msg=False))
    numero_quirofranos = 0
    for i in numero_patrones: #Recuperación de las planificaciones utilizadas
        if x[i].varValue != 0:
            numero_quirofranos += 1
    return numero_quirofranos


def Modelo_generador(precio_sombra, L):
    """
    Genera una nueva planificació dado los datos del modelo unidimensional

    Parametros:
        precio_sombra (dict): Diccionario con los precios sombra
        L (dict): Diccionario de incompatibilidades

    Returns:
        nuevo_patron (list): Lista con la nueva planificación
        pulp.value(modelo.objective) (float): Valor de la función objetivo
    """
    y_values = precio_sombra.keys() #Definicion del conjunto de y

    #Creación del modelo
    modelo = LpProblem("Cutting_stock_problem2", LpMaximize)
    y = LpVariable.dicts("y", y_values, lowBound = 0, cat ='Binary')
    
    #Objetivo
    modelo += lpSum([y[j]*precio_sombra[j] for j in y_values])

    #Restricciones
    for key, value in L.items():
        if value != []: #Si la lista de incompatibilidades no está vacía
            for operacion in value:
                modelo += y[key] + y[operacion] <= 1
        else: 
            modelo += y[key] == 1 #Si la variable no tiene incompatibilidades, fijamos su valor a 1 

    #Resolución
    modelo.solve(PULP_CBC_CMD(msg=False))
    nuevo_patron = [int(y[operacion].varValue) for operacion in y_values]
    return nuevo_patron, pulp.value(modelo.objective)


def column_generaction(planificaciones, operaciones, L):
    """
    Ejecución del modelo de generación de columnas

    Parametros:
        planificaciones (DataFrame): DataFrame con las planificaciones
        operaciones (list): Lista de operaciones
        L (dict): Diccionario de incompatibilidades
    
    Returns:
        numero_quirofranos (int): Número de quirofanos necesarios
    """
    bool = True #Criterio de parada
    while bool:
        precio_sombra, x = Modelo_unidimensional(planificaciones, operaciones) #Recuperación de los precios sombra y los valores de x
        nueva_columna, costo_reducido = Modelo_generador(precio_sombra, L) #Recuperación de la nueva columna y el costo reducido
        print("Nueva planificaccion calculada")
        columnas = [planificaciones[columna].tolist() for columna in planificaciones.columns] #Conjunto de las columnas
        if nueva_columna in columnas or costo_reducido <= 1: #Si la nueva columna ya existe o el costo reducido es menor o igual a 1, salimos del bucle
            bool = False
        else: #Sino, añadimos la nueva columna al DataFrame
            planificaciones[len(planificaciones.columns)] = nueva_columna
    numero_quirofranos = Modelo_unidimensional_binario(planificaciones, operaciones)
    return numero_quirofranos


## Ejecucion del modelo de generación de columnas

#Creación de un dataframe para ver las planificaciones
planificacion = generacion_planificacion(operaciones, L, 3) #Generamos una planificación inicial con 3 operaciones máximas por planificación
planificaciones = pd.DataFrame(0, index=operaciones, columns=range(len(planificacion)))
for elt in planificacion:
    for operacion in elt:
        planificaciones.at[operacion, planificacion.index(elt)] = 1
print(planificaciones)

#Ejecución de las funciones
print("Numero de quirofranos necesarios :", column_generaction(planificaciones, operaciones, L))
