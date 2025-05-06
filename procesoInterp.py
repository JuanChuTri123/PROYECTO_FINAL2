import pandas as pd
import numpy as np
import os

# Ruta al archivo
ruta = os.path.join("static", "data", "Total_Huaraz", "DataHistorica.csv")

# Leer archivo
df = pd.read_csv(ruta, sep=";", encoding="utf-8")

# Asegurar tipo correcto
df['ANIO'] = df['ANIO'].astype(int)
df['MES'] = df['MES'].astype(int)
df['CONSUMO_TOTAL_KWH'] = pd.to_numeric(df['CONSUMO_TOTAL_KWH'], errors='coerce')

# Crear columna de fecha
df['FECHA'] = pd.to_datetime(df['ANIO'].astype(str) + '-' + df['MES'].astype(str) + '-01')
df = df.sort_values('FECHA').set_index('FECHA')

# Eliminar el registro de Mayo 2024 si existe (lo reemplazaremos)
fecha_mayo = pd.Timestamp('2024-12-01')
df = df[df.index != fecha_mayo]

# Insertar fila faltante con NaN para mayo
df.loc[fecha_mayo] = np.nan

# Reordenar
df = df.sort_index()

# Interpolar columna de consumo
df['CONSUMO_TOTAL_KWH'] = df['CONSUMO_TOTAL_KWH'].interpolate(method='linear')

# Extraer nuevamente año y mes
df['ANIO'] = df.index.year
df['MES'] = df.index.month

# Reordenar columnas
df_final = df[['ANIO', 'MES', 'CONSUMO_TOTAL_KWH']]

# Guardar actualizado
df_final.to_csv(ruta, sep=";", index=False, encoding="utf-8-sig")

print("✅ Interpolación completada y archivo actualizado.")