from flask import Blueprint, request, render_template, redirect, flash
import os
import pandas as pd
from flask import session
import pandas as pd
from prophet import Prophet

upload_bp = Blueprint('upload', __name__)

@upload_bp.route("/upload", methods=["POST"])
def upload_csv():
    try:
        # Verificamos si se ha subido el archivo
        if 'archivo_csv' not in request.files:
            flash("❌ No se ha subido ningún archivo", "danger")
            return redirect("/subir-archivo")

        file = request.files['archivo_csv']

        if file.filename == "":
            flash("❌ No se ha seleccionado ningún archivo", "danger")
            return redirect("/subir-archivo")

        # Verificamos que el archivo sea CSV
        if not file.filename.lower().endswith(".csv"):
            flash("❌ Solo se permiten archivos con extensión .csv", "danger")
            return redirect("/subir-archivo")
        
        # Intenta leer el archivo con diferentes codificaciones
        encodings = ['utf-8-sig', 'latin1', 'ISO-8859-1']
        contenido_inicial = None
        encoding_usado = None

        for enc in encodings:
            try:
                file.stream.seek(0)
                contenido_inicial = file.read().decode(enc)
                encoding_usado = enc
                break
            except UnicodeDecodeError:
                continue

        if contenido_inicial is None:
            flash("❌ No se pudo leer el archivo con codificación válida (utf-8, latin1, ISO-8859-1)", "danger")
            return redirect("/subir-archivo")

        # Detectamos si el separador es ; o ,
        delimitador = ";" if ";" in contenido_inicial.splitlines()[0] else ","

        # Leer con pandas
        file.stream.seek(0)
        df = pd.read_csv(file, sep=delimitador, encoding=encoding_usado)

        # Validar columnas necesarias
        columnas_requeridas = {"PROVINCIA", "DISTRITO", "CONSUMO"}
        columnas_archivo = set(df.columns.str.upper().str.strip())

        print("🔍 Columnas detectadas:", columnas_archivo)

        if not columnas_requeridas.issubset(columnas_archivo):
            flash("❌ El archivo debe tener las columnas: PROVINCIA, DISTRITO, CONSUMO", "danger")
            return redirect("/subir-archivo")

        # Normalizamos nombres de columnas
        df.columns = df.columns.str.upper().str.strip()

        # Filtramos solo las columnas necesarias
        columnas_requeridas = ["PROVINCIA", "DISTRITO", "CONSUMO"]
        df_temporal = df[columnas_requeridas]

        # Guardamos el DataFrame como archivo temporal correctamente separado
        ruta_temporal = os.path.join("static", "data", "DataTemporal.csv")
        df_temporal.to_csv(ruta_temporal, index=False, sep=";", encoding="utf-8-sig")

        # Si pasa la validación, puedes guardar el archivo o continuar procesamiento
        # Verifica si ya existe el registro en DataHistorica.csv
    
        # 🗓️ Obtener año y mes del formulario
        anio = str(request.form.get('anio')).strip()
        mes = str(int(request.form.get('mes'))).strip()  
           
        # 2. Obtener año y mes del formulario
        session["anio"] = anio
        session["mes"] = mes
        
        ruta_historica = os.path.join("static", "data", "Total_Huaraz", "DataHistorica.csv")

        if os.path.exists(ruta_historica):
            try:
                df_hist = pd.read_csv(ruta_historica, sep=";", encoding="utf-8")
                
                # Aseguramos que las columnas sean tipo str sin ceros a la izquierda
                df_hist['ANIO'] = df_hist['ANIO'].astype(str).str.strip()
                df_hist['MES'] = df_hist['MES'].astype(str).str.strip().str.lstrip('0')

                # Verificación de si ya existe ese año y mes
                existe = ((df_hist['ANIO'] == anio) & (df_hist['MES'] == mes)).any()
            
                if existe:
                    flash("⚠️ El archivo con ese año y mes ya existe. Si continúa lo reemplazará!", "warning")
                else:
                    flash("✅ Todo correcto, proceda a guardar!", "success")

            except Exception as e:
                flash(f"⚠️ No se pudo leer DataHistorica.csv: {str(e)}", "warning")
        else:
            flash("⚠️ No se encontró el archivo 'DataHistorica.csv'.", "danger")

        return redirect("/subir-archivo")
   
    except Exception as e:
        flash(f"❌ Error al procesar el archivo: {str(e)}", "danger")
        return redirect("/subir-archivo")

@upload_bp.route("/filtrar", methods=["POST"])
def filtrar_datos():
    try:
        ruta_csv = os.path.join("static", "data", "DataTemporal.csv")
        
        df = pd.read_csv(ruta_csv, sep=";", encoding="utf-8")
        df_huaraz = df[df["PROVINCIA"].str.upper().str.strip() == "HUARAZ"]

        if df_huaraz.empty:
            flash("❌ No se encontraron registros para las provincias Huaraz", "danger")
            return redirect("/subir-archivo")

        anio = session.get("anio")
        mes = session.get("mes")
        if not anio or not mes:
            flash("⚠️ No se pudo recuperar año y mes de la sesión", "warning")
            return redirect("/subir-archivo")

        # Guardar DataHistorica para Huaraz
        if not df_huaraz.empty:
            consumo_total_huaraz = df_huaraz["CONSUMO"].sum()
            ruta_huaraz = os.path.join("static", "data", "Total_Huaraz", "DataHistorica.csv")

            if os.path.exists(ruta_huaraz):
                df_hist_huaraz = pd.read_csv(ruta_huaraz, sep=";", encoding="utf-8")
            else:
                df_hist_huaraz = pd.DataFrame(columns=["ANIO", "MES", "CONSUMO_TOTAL_KWH"])

            df_hist_huaraz = df_hist_huaraz[
                ~((df_hist_huaraz["ANIO"].astype(str) == anio) & (df_hist_huaraz["MES"].astype(str) == mes))
            ]

            df_hist_huaraz = pd.concat([
                df_hist_huaraz,
                pd.DataFrame([{"ANIO": anio, "MES": mes, "CONSUMO_TOTAL_KWH": consumo_total_huaraz}])
            ], ignore_index=True)

            df_hist_huaraz["ANIO"] = df_hist_huaraz["ANIO"].astype(int)
            df_hist_huaraz["MES"] = df_hist_huaraz["MES"].astype(int)
            df_hist_huaraz = df_hist_huaraz.sort_values(by=["ANIO", "MES"])
            df_hist_huaraz.to_csv(ruta_huaraz, sep=";", index=False, encoding="utf-8-sig")

        # Guardar archivos de distritos (solo Huaraz)
        # if not df_huaraz.empty:
        #     distritos = [
        #         "Cochabamba", "Colcabamba", "Huanchay", "Huaraz", "Independencia", "Jangas",
        #         "La Libertad", "Olleros", "Pampas Grande", "Pariacoto", "Pira", "Tarica"
        #     ]

        #     for distrito in distritos:
        #         consumo_distrito = df_huaraz[
        #             df_huaraz["DISTRITO"].str.upper().str.strip() == distrito.upper()
        #         ]["CONSUMO"].sum()

        #         ruta_distrito = os.path.join("static", "data", "Distritos", f"{distrito}.csv")

        #         if os.path.exists(ruta_distrito):
        #             df_distrito = pd.read_csv(ruta_distrito, sep=";", encoding="utf-8")
        #         else:
        #             df_distrito = pd.DataFrame(columns=["ANIO", "MES", "CONSUMO_TOTAL_KWH"])

        #         df_distrito = df_distrito[
        #             ~((df_distrito["ANIO"].astype(str) == anio) & (df_distrito["MES"].astype(str) == mes))
        #         ]

        #         nueva_fila = {
        #             "ANIO": anio,
        #             "MES": mes,
        #             "CONSUMO_TOTAL_KWH": consumo_distrito
        #         }

        #         df_distrito = pd.concat([df_distrito, pd.DataFrame([nueva_fila])], ignore_index=True)
        #         df_distrito["ANIO"] = df_distrito["ANIO"].astype(int)
        #         df_distrito["MES"] = df_distrito["MES"].astype(int)
        #         df_distrito = df_distrito.sort_values(by=["ANIO", "MES"])
        #         df_distrito.to_csv(ruta_distrito, sep=";", index=False, encoding="utf-8-sig")
        #         print(f"[{distrito}] -> Consumo: {consumo_distrito}")
        #         print(f"Guardado en: {ruta_distrito}")

        # Actualizar PrediccionHuarazTotal.csv con el consumo real y MAPE
        pred_uno_path = os.path.join("static", "data", "Predicciones", "PrediccionHuarazTotal.csv")
        if os.path.exists(pred_uno_path):
            df_pred_uno = pd.read_csv(pred_uno_path, sep=";", encoding="utf-8")

            if "CONSUMO_REAL_KWH" not in df_pred_uno.columns:
                df_pred_uno["CONSUMO_REAL_KWH"] = None
            if "MARGEN_ERROR(MAPE)" not in df_pred_uno.columns:
                df_pred_uno["MARGEN_ERROR(MAPE)"] = None

            fila_idx = df_pred_uno[
                (df_pred_uno["ANIO"].astype(str) == str(anio)) &
                (df_pred_uno["MES"].astype(int) == int(mes))
            ].index

            if not fila_idx.empty:
                idx = fila_idx[0]
                try:
                    predicho = float(df_pred_uno.loc[idx, "PREDICCION_KWH"])
                    real = float(consumo_total_huaraz)
                    if real > 0:
                        mape = abs((real - predicho) / real) * 100
                        df_pred_uno.at[idx, "CONSUMO_REAL_KWH"] = real
                        df_pred_uno.at[idx, "MARGEN_ERROR(MAPE)"] = round(mape, 2)
                        df_pred_uno.to_csv(pred_uno_path, sep=";", index=False, encoding="utf-8-sig")
                        flash(f"✅ Se subió correctamente el consumo real!!", "success")
                    else:
                        flash("⚠️ El consumo real es cero, no se puede calcular el MAPE", "warning")
                except Exception as e:
                    flash(f"⚠️ Error al calcular MAPE: {str(e)}", "warning")
            else:
                flash("⚠️ No se encontró una predicción previa para este mes", "warning")

        # Eliminar archivos temporales
        for temp_path in ["DataFiltrada.csv", "DataTemporal.csv"]:
            ruta_temp = os.path.join("static", "data", temp_path)
            if os.path.exists(ruta_temp):
                os.remove(ruta_temp)

        flash("✅ Datos procesados y guardados correctamente", "success")
        return redirect("/subir-archivo")

    except Exception as e:
        flash(f"❌ Error al filtrar y guardar datos: {str(e)}", "danger")
        return redirect("/subir-archivo")

