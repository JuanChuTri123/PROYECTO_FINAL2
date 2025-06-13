from flask import render_template, request, Blueprint
import pandas as pd
import io
import datetime
import matplotlib.pyplot as plt
from flask import send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import cm
import numpy as np
from matplotlib.patches import Wedge
import textwrap

report = Blueprint('reportes', __name__)

@report.route("/generar_reporte", methods=["POST"])
def generar_reporte():
    anio = int(request.form["anio"])
    df = pd.read_csv("static/data/Predicciones/PrediccionHuarazTotal.csv", sep=";")

    # Filtrar por año y eliminar filas con datos faltantes
    df_filtrado = df[(df["ANIO"] == anio) & df["CONSUMO_REAL_KWH"].notna() & df["PREDICCION_KWH"].notna()]

    # Clasificar MAPE
    def clasificar_mape(mape):
        if mape <= 5:
            return "Excelente precisión"
        elif mape <= 10:
            return "Aceptable"
        elif mape <= 20:
            return "Regular"
        else:
            return "Bajísima precisión"

    df_filtrado["CLASIFICACION"] = df_filtrado["MARGEN_ERROR(MAPE)"].apply(clasificar_mape)

    registros = df_filtrado.to_dict(orient="records")
    return render_template("reportes.html", registros=registros, anio=anio)

@report.route("/descargar_reporte/<int:anio>/<int:mes>", methods=["GET"])
def descargar_reporte(anio, mes):
    df = pd.read_csv("static/data/Predicciones/PrediccionHuarazTotal.csv", sep=";")
    df = df[(df["ANIO"] == anio) & (df["MES"] == mes)]
    df = df.dropna(subset=["PREDICCION_KWH", "CONSUMO_REAL_KWH", "MARGEN_ERROR(MAPE)"])

    if df.empty:
        return "No hay datos completos para este mes", 404

    fila = df.iloc[0]
    mes_nombre = datetime.date(1900, mes, 1).strftime("%B")

    # Clasificación del MAPE
    mape = fila["MARGEN_ERROR(MAPE)"]

    if mape <= 5:
        clasificacion = "Excelente precisión"
        conclusion = (
            "La predicción muestra un grado de exactitud sobresaliente. Este nivel de precisión es confiable para la planificación energética y la toma de decisiones estratégicas."
        )
    elif mape <= 10:
        clasificacion = "Aceptable"
        conclusion = (
            "La predicción es razonablemente confiable, con un margen de error aceptable. Puede utilizarse en decisiones operativas con cierta seguridad."
        )
    elif mape <= 20:
        clasificacion = "Regular"
        conclusion = (
            "El modelo presenta un nivel de error considerable. Se recomienda precaución al usar estas predicciones, especialmente para decisiones críticas. Este tipo de margen de error puede deber a temas administrativos o relacionado con la subida de los datos de este mes."
        )
    else:
        clasificacion = "Bajísima precisión"
        conclusion = (
            "La predicción difiere mucho del consumo real, lo que limita su confiabilidad. Es necesario revisar los datos subidos o en caso extremo verificar el modelo predictivo utilizado."
        )


    # Comparación con flecha
    pred = fila["PREDICCION_KWH"]
    real = fila["CONSUMO_REAL_KWH"]
    diferencia = abs(pred - real)

    if diferencia < 0.01 * real:
        comparacion_icono = (
            "La predicción se encuentra prácticamente alineada con el valor real de consumo, "
        )
    elif pred > real:
        comparacion_icono = (
            "La predicción supera al valor real registrado, lo que sugiere una sobreestimación del consumo. "
        )
    else:
        comparacion_icono = (
            "La predicción es inferior al consumo real observado, indicando una subestimación. "
        )
    # Crear gráfico gauge
    def generar_gauge_mape(mape):
        fig, ax = plt.subplots(figsize=(6, 3), subplot_kw={'aspect': 'equal'})
        ax.axis('off')

        # Rango de MAPE y colores (4 rangos)
        sectores = [
            (0, 5, 'lime', 'Excelente'),
            (5, 10, 'yellow', 'Aceptable'),
            (10, 20, 'orange', 'Regular'),
            (20, 100, 'red', 'Bajísima')
        ]

        for start, end, color, label in sectores:
            theta1 = (start / 100) * 180
            theta2 = (end / 100) * 180
            wedge = Wedge(center=(0, 0), r=1, theta1=theta1, theta2=theta2,
                        facecolor=color, edgecolor='white')
            ax.add_patch(wedge)

            # Etiquetas
            theta = (theta1 + theta2) / 2
            x = 1.15 * np.cos(np.radians(theta))
            y = 1.15 * np.sin(np.radians(theta))
            ax.text(x, y, label, ha='center', va='center', fontsize=8)

        # Aguja del MAPE
        mape_angle = (min(mape, 100) / 100) * 180
        x = 0.9 * np.cos(np.radians(mape_angle))
        y = 0.9 * np.sin(np.radians(mape_angle))
        ax.plot([0, x], [0, y], color='black', lw=3)

        # Texto central
        ax.text(0, -0.2, f"MAPE: {mape:.2f}%", ha='center', fontsize=12, fontweight='bold')

        # Guardar a buffer
        buffer_img = io.BytesIO()
        plt.savefig(buffer_img, format='PNG', bbox_inches='tight', transparent=True)
        plt.close()
        buffer_img.seek(0)
        return buffer_img

    buffer_img = generar_gauge_mape(mape)

    # Crear PDF
    buffer_pdf = io.BytesIO()
    c = canvas.Canvas(buffer_pdf, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    titulo = f"Reporte de Predicción de Consumo Energético – {anio}"
    c.setFont("Helvetica-Bold", 14)
    titulo_ancho = c.stringWidth(titulo, "Helvetica-Bold", 14)
    c.drawString((width - titulo_ancho) / 2, height - 2 * cm, titulo)

    c.setFont("Helvetica", 11)
    c.drawString(2 * cm, height - 3 * cm, f"Fecha de generación: {datetime.date.today()}")
    c.drawString(2 * cm, height - 3.7 * cm, "Ciudad/Zona: Huaraz")
    c.drawString(2 * cm, height - 4.4 * cm, f"Datos analizados: Predicciones vs Consumo Real – {mes_nombre}")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, height - 6 * cm, "Datos:")
    c.setFont("Helvetica", 11)
    c.drawString(2 * cm, height - 6.7 * cm, f"Predicción: {pred:.2f} kWh")
    c.drawString(2 * cm, height - 7.4 * cm, f"Consumo Real: {real:.2f} kWh")
    c.drawString(2 * cm, height - 8.1 * cm, f"MAPE: {mape:.2f}%")
    c.drawString(2 * cm, height - 8.8 * cm, f"Clasificación: {clasificacion}")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, height - 10.2 * cm, "Comparación:")
    c.setFont("Helvetica", 12)
    c.drawString(2 * cm, height - 11 * cm, comparacion_icono)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, height - 13 * cm, "Conclusión:")
    c.setFont("Helvetica", 11)
    text_obj = c.beginText(2 * cm, height - 14 * cm)
    wrapped_lines = textwrap.wrap(conclusion, width=95)  # ajusta el ancho según tu fuente/tamaño
    for line in wrapped_lines:
        text_obj.textLine(line)
    c.drawText(text_obj)

    # Subtítulo gráfico
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, height - 17 * cm, "Gráfico de precisión:")

    # Agregar gráfico más arriba
    img_reader = ImageReader(buffer_img)
    c.drawImage(img_reader, 6 * cm, height - 24 * cm, width=10 * cm, height=6 * cm,
                preserveAspectRatio=True, mask='auto')

    c.showPage()
    c.save()
    buffer_pdf.seek(0)

    return send_file(buffer_pdf, download_name=f"reporte_{anio}_{mes}.pdf", as_attachment=True)