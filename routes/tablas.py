import pandas as pd
from flask import Blueprint, request, render_template, redirect, flash


bds = Blueprint('tablas', __name__)

@bds.route('/tablaHuaraz')
def mostrar_tabla():
    anio = request.args.get('anio')
    tabla_html = ""  # Por defecto está vacío

    if anio:  # Solo mostrar tabla si se ha seleccionado un año válido
        df = pd.read_csv("static/data/Total_Huaraz/DataHistorica.csv", sep=";")
        df = df[df['ANIO'] == int(anio)]
        tabla_html = df.to_html(index=False, classes="mi-tabla")

    return render_template('bd.html', tabla=tabla_html)