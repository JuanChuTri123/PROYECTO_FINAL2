from flask import Blueprint, render_template, request
import pandas as pd
import plotly.express as px

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard', methods=['GET'])
def consumo_dashboard():
    df = pd.read_csv("static/data/Total_Huaraz/DataHistorica.csv", sep=";")
    df['CONSUMO_MWH'] = df['CONSUMO_TOTAL_KWH'] / 1000  # Escalar a MWh

    anios = list(range(2022, 2031))
    anio_seleccionado = request.args.get('anio', default=2025, type=int)

    df_filtrado = df[df['ANIO'] == anio_seleccionado]

    fig = px.line(
        df_filtrado,
        x='MES',
        y='CONSUMO_MWH',
        title=f'Consumo mensual en {anio_seleccionado} (MWh)',
        markers=True,
        labels={'MES': 'Mes', 'CONSUMO_MWH': 'Consumo (MWh)'},
        template='plotly_dark'
    )
    fig.update_layout(xaxis=dict(tickmode='linear'))

    grafico_html = fig.to_html(full_html=False)

    return render_template('dashboard.html',
                           grafico_html=grafico_html,
                           anios=anios,
                           anio_seleccionado=anio_seleccionado)
