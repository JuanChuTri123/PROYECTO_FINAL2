import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt

# 1. Cargar datos
df = pd.read_csv("static/data/Total_Huaraz/DataHistorica.csv", sep=";")

# 2. Preparar columnas para Prophet
df['ds'] = pd.to_datetime(df['ANIO'].astype(str) + '-' + df['MES'].astype(str).str.zfill(2) + '-01')
df['y'] = df['CONSUMO_TOTAL_KWH']

# 3. Filtrar solo hasta diciembre 2024 para entrenamiento
df_train = df[df['ds'] <= '2024-12-01'][['ds', 'y']]

# 4. Crear y ajustar modelo Prophet
model = Prophet()
model.fit(df_train)

# 5. Generar predicciones para 3 meses futuros (enero, febrero, marzo 2025)
future = model.make_future_dataframe(periods=3, freq='MS')
forecast = model.predict(future)

# 6. Extraer solo las predicciones nuevas
pred_trimestre = forecast[forecast['ds'] >= '2025-01-01'][['ds', 'yhat']].head(3)

# 7. Mostrar y guardar resultados
print("📈 Predicciones Enero - Marzo 2025:")
print(pred_trimestre)

pred_trimestre.to_csv("static/data/Prediccion_Huaraz_Trimestre_2025.csv", index=False, encoding="utf-8-sig")

import numpy as np

# Suponiendo que ya tienes:
# pred_trimestre con las predicciones
# df con los valores reales (incluye enero a marzo 2025)

# 1. Filtrar reales
reales = df[df['ds'].between('2025-01-01', '2025-03-01')][['ds', 'y']].reset_index(drop=True)

# 2. Asegurar orden y unir con predicciones
comparacion = pred_trimestre.copy()
comparacion = comparacion.rename(columns={'yhat': 'y_pred'})
comparacion['y_real'] = reales['y']

# 3. Calcular MAE y MAPE
comparacion['error_abs'] = np.abs(comparacion['y_pred'] - comparacion['y_real'])
comparacion['error_pct'] = comparacion['error_abs'] / comparacion['y_real'] * 100

mae = comparacion['error_abs'].mean()
mape = comparacion['error_pct'].mean()

print(f"MAE: {mae:.2f} kWh")
print(f"MAPE: {mape:.2f}%")
