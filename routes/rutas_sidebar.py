from flask import Blueprint, render_template, request
import pandas as pd
import os

# Crear el blueprint
sidebar = Blueprint('sidebar', __name__)

# Definir rutas
@sidebar.route('/')
def index():
    return render_template('base.html')

@sidebar.route('/manual')
def manual():
    return render_template('manual.html')

@sidebar.route('/subir-archivo')
def subir_archivo():
    pred_path = "static/data/Predicciones/PrediccionHuarazTotal.csv"
    puede_subir = False
    meses_faltantes = []

    if os.path.exists(pred_path):
        df = pd.read_csv(pred_path, sep=";")

        if not df.empty and df['CONSUMO_REAL_KWH'].isnull().any():
            puede_subir = True

            # Filtrar filas sin consumo real
            sin_consumo = df[df['CONSUMO_REAL_KWH'].isnull()]

            # Convertir a lista de tuplas (AÑO, MES)
            meses_faltantes = [
                (int(row['ANIO']), int(row['MES'])) for _, row in sin_consumo.iterrows()
            ]

            # Ordenar por año y mes
            meses_faltantes.sort()

    return render_template('subir-archivo.html', puede_subir=puede_subir, meses_faltantes=meses_faltantes)

@sidebar.route('/BaseDatos')
def bd():
    return render_template('bd.html')

@sidebar.route('/Prediccion')
def predicciones():
    anio = request.args.get('anio', type=int)
    tabla_html = ""

    pred_path = "static/data/Predicciones/PrediccionHuarazTotal.csv"
    if os.path.exists(pred_path) and anio:
        df = pd.read_csv(pred_path, sep=";")
        df = df[df['ANIO'] == anio]
        tabla_html = df.to_html(index=False, classes="tabla-predicciones")

    return render_template("predicciones.html", tabla=tabla_html, anio=anio)

@sidebar.route('/Reportes')
def reportes():
    return render_template('reportes.html')