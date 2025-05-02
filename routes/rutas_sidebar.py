from flask import Blueprint, render_template

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
    return render_template('subir-archivo.html')

@sidebar.route('/BaseDatos')
def bd():
    return render_template('bd.html')

@sidebar.route('/Prediccion')
def predicciones():
    return render_template('predicciones.html')

@sidebar.route('/Reportes')
def reportes():
    return render_template('reportes.html')