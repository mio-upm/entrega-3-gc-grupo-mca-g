from pulp import *
from math import floor


def Modelo_unidimensional(patrones):
    f = [1, 2, 3, 4]
    fd = [97, 610, 395, 211] 
    numero_patrones = [i for i in range(1, len(patrones)+1)]

    modelo = LpProblem("Cutting_stock_problem", LpMinimize)
    x = LpVariable.dicts("x", numero_patrones, lowBound=0, cat='Continuous')

    modelo += lpSum([x[i] for i in numero_patrones])
    for i in f:
        modelo += lpSum([patrones[j-1][i-1] * x[j] for j in numero_patrones]) >= fd[i-1]

    modelo.solve(PULP_CBC_CMD(msg=False))
    shadow_prices = [constraint.pi for constraint in modelo.constraints.values()]
    shadow_prices = {i: shadow_prices[i-1] for i in f}
    x_values = {i: x[i].varValue for i in numero_patrones}
    print(LpStatus[modelo.status])
    print(value(modelo.objective))
    print(x_values)
    print(shadow_prices)
    return shadow_prices, x_values


def Modelo_generador(datos):
    W = 100
    wf = {1: 45, 2: 36, 3: 31, 4: 14}

    y_values = datos.keys()
    modelo = LpProblem("Cutting_stock_problem2", LpMaximize)
    y = LpVariable.dicts("y", y_values, lowBound = 0, cat ='Integer')

    modelo += lpSum([y[j]*datos[j] for j in y_values])
    modelo += lpSum([wf[j]*y[j] for j in y_values]) <= W 

    modelo.solve(PULP_CBC_CMD(msg=False))
    nuevo_patron = [int(y[i].varValue) for i in y_values]
    return nuevo_patron, value(modelo.objective)


def column_generaction():
    patrones = [[0, 1, 0, 0],
            [0, 2, 0, 0],
            [0, 0, 3, 0],
            [0, 0, 0, 7]]
    bool = True
    while bool:
        shadow_prices, x = Modelo_unidimensional(patrones)
        nuevo_patron, costo_reducido = Modelo_generador(shadow_prices)
        if nuevo_patron in patrones or costo_reducido <= 1:
            bool = False
        else:
            patrones.append(nuevo_patron)
    finales = {i:0 for i in range(len(patrones[0]))}
    for i in range(len(x)):
        for j in range(len(patrones[0])):
            finales[j] += floor(x[i+1])*patrones[i][j]
    return finales
        
# print(column_generaction())
patrones = [[0, 1, 0, 0],
            [0, 2, 0, 0],
            [0, 0, 3, 0],
            [0, 0, 0, 7]]
    
print(Modelo_unidimensional(patrones))