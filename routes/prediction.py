from flask import Blueprint, request, render_template, redirect, flash
import os
import pandas as pd
from flask import session
import pandas as pd
from prophet import Prophet

predict = Blueprint('prediction', __name__)

@predict.route('/procesar', methods=['POST'])
def procesar():
    anio = int(request.form['anio'])
    trimestre = int(request.form['trimestre'])  # Viene como 01, 04, 07, 10

    # Guardar en sesión para la predicción
    session['anio'] = anio
    session['trimestre'] = trimestre

    # Ruta al CSV de predicciones
    path_csv = "static/data/Predicciones/PrediccionHuarazTotal.csv"

    # Verificar existencia del archivo
    if os.path.exists(path_csv):
        df_pred = pd.read_csv(path_csv, sep=";")

        # Validar si existen valores vacíos
        if df_pred.isnull().values.any():
            flash("❌ Hay valores vacíos en PrediccionHuarazTotal.csv. Revíselos antes de continuar.")
            return redirect('/Prediccion')

        # Validar si ya existe predicción para ese trimestre
        meses_trimestre = [trimestre, trimestre + 1, trimestre + 2]
        existe = df_pred[
            (df_pred['ANIO'] == anio) & (df_pred['MES'].isin(meses_trimestre))
        ]

        if not existe.empty:
            flash("❌ Ya existe una predicción para ese trimestre.")
            return redirect('/Prediccion')

    flash("✅ Proceso completado, prosiga a predecir")
    return redirect('/Prediccion')

@predict.route('/predecir', methods=['POST'])
def predecir():
    # 1. Leer año y trimestre desde sesión
    anio = session.get('anio')
    trimestre = session.get('trimestre')  # Ej: "01", "04", etc.
    if not anio or not trimestre:
        flash("❌ No se encontró año o trimestre en la sesión.")
        return redirect('/Prediccion')

    fecha_inicio = f"{anio}-{str(trimestre).zfill(2)}-01"
    fecha_inicio_dt = pd.to_datetime(fecha_inicio)

    # 2. Cargar data histórica
    df = pd.read_csv("static/data/Total_Huaraz/DataHistorica.csv", sep=";")
    df['ds'] = pd.to_datetime(df['ANIO'].astype(str) + '-' + df['MES'].astype(str).str.zfill(2) + '-01')
    df['y'] = df['CONSUMO_TOTAL_KWH']
    ultima_fecha = df['ds'].max()

    # 3. Entrenar Prophet hasta última fecha
    df_train = df[df['ds'] <= ultima_fecha][['ds', 'y']]
    
    params = {
    'changepoint_prior_scale': 0.01,
    'seasonality_prior_scale': 0.01,
    'seasonality_mode': 'multiplicative'
    }
    model = Prophet(**params)
    model.fit(df_train)

    # 4. Generar solo las 3 fechas futuras
    future_dates = pd.date_range(start=fecha_inicio_dt, periods=3, freq='MS')
    future_df = pd.DataFrame({'ds': future_dates})
    forecast = model.predict(future_df)
    pred_trimestre = forecast[['ds', 'yhat']]

    # 5. Verificar si las fechas ya existen en PrediccionHuarazTotal.csv
    pred_uno_path = "static/data/Predicciones/PrediccionHuarazTotal.csv"
    df_pred_uno = pd.read_csv(pred_uno_path, sep=";") if os.path.exists(pred_uno_path) else pd.DataFrame(columns=['ANIO', 'MES', 'PREDICCION_KWH', 'CONSUMO_REAL_KWH', 'MARGEN_ERROR(MAPE)'])

    fechas_existentes = df_pred_uno.apply(lambda row: f"{int(row['ANIO'])}-{int(row['MES']):02d}" if pd.notnull(row['ANIO']) and pd.notnull(row['MES']) else "", axis=1).tolist()

    nuevas_filas = []
    for _, row in pred_trimestre.iterrows():
        fecha_str = row['ds'].strftime('%Y-%m')
        if fecha_str in fechas_existentes:
            flash(f"⚠️ Ya existe una predicción para {fecha_str}. No se sobrescribió.")
            continue

        nuevas_filas.append({
            'ANIO': row['ds'].year,
            'MES': row['ds'].month,
            'PREDICCION_KWH': round(row['yhat'], 2),
            'CONSUMO_REAL_KWH': "",  # Vacío por ahora
            'MARGEN_ERROR(MAPE)': ""  # Vacío por ahora
        })

    if nuevas_filas:
        df_pred_uno = pd.concat([df_pred_uno, pd.DataFrame(nuevas_filas)], ignore_index=True)
        df_pred_uno.to_csv(pred_uno_path, sep=";", index=False, encoding="utf-8-sig")
        flash("✅ Predicción realizada y guardada correctamente.")
    else:
        flash("ℹ️ No se agregaron nuevas predicciones porque ya existían.")

    return redirect('/Prediccion')
