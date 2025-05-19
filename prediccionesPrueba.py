import pandas as pd
import matplotlib.pyplot as plt

# 1. Leer la data directamente (puedes pegarla desde un CSV si lo prefieres)
df = pd.read_csv("static/data/Total_Huaraz/DataHistorica.csv", sep=";")

# 2. Convertir año y mes a una sola fecha
df['ds'] = pd.to_datetime(df['ANIO'].astype(str) + '-' + df['MES'].astype(str).str.zfill(2) + '-01')

# 3. Ordenar por fecha (por si acaso)
df = df.sort_values('ds')

# 4. Graficar
plt.figure(figsize=(12, 6))
plt.plot(df['ds'], df['CONSUMO_TOTAL_KWH'], marker='o', linestyle='-', color='blue', label='Consumo mensual')

# 5. Opcional: línea suavizada para tendencia
df['rolling'] = df['CONSUMO_TOTAL_KWH'].rolling(window=3).mean()
plt.plot(df['ds'], df['rolling'], color='red', linestyle='--', label='Tendencia (media 3 meses)')

# 6. Estética
plt.title("Consumo mensual de energía - Huaraz (histórico)")
plt.xlabel("Fecha")
plt.ylabel("Consumo Total (kWh)")
plt.grid(True)
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()

# 7. Mostrar gráfico
plt.show()
