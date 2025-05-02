from flask import Blueprint, request, render_template, redirect, flash
import os
import pandas as pd
from flask import session


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
                
                # Depuración: mostrar lo que estás comparando
                print("Formulario:", anio, mes)
                print("CSV únicos ANIO:", df_hist['ANIO'].unique())
                print("CSV únicos MES:", df_hist['MES'].unique())

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
        if not os.path.exists(ruta_csv):
            flash("❌ No se encontró el archivo para filtrar", "danger")
            return redirect("/subir-archivo")

        df = pd.read_csv(ruta_csv, sep=";", encoding="utf-8")

        if 'PROVINCIA' not in df.columns or 'DISTRITO' not in df.columns or 'CONSUMO' not in df.columns:
            flash("❌ El archivo no contiene las columnas necesarias (PROVINCIA, DISTRITO, CONSUMO)", "danger")
            return redirect("/subir-archivo")

        df_filtrado = df[df["PROVINCIA"].str.upper().str.strip() == "HUARAZ"]

        if df_filtrado.empty:
            flash("❌ No se encontraron registros para la provincia Huaraz", "danger")
            return redirect("/subir-archivo")

        # Guardar archivo filtrado
        ruta_filtrada = os.path.join("static", "data", "DataFiltrada.csv")
        df_filtrado.to_csv(ruta_filtrada, index=False, sep=";")

        # Obtener año y mes de sesión
        anio = session.get("anio")
        mes = session.get("mes")
        if not anio or not mes:
            flash("⚠️ No se pudo recuperar año y mes de la sesión", "warning")
            return redirect("/subir-archivo")
    
         # --- Parte: guardar en DataHistorica.csv ---
        consumo_total = df_filtrado["CONSUMO"].sum()

        ruta_historica = os.path.join("static", "data", "Total_Huaraz", "DataHistorica.csv")

        if os.path.exists(ruta_historica):
            df_historica = pd.read_csv(ruta_historica, sep=";", encoding="utf-8")
        else:
            df_historica = pd.DataFrame(columns=["ANIO", "MES", "CONSUMO_TOTAL_KWH"])

        # Eliminar si ya existe
        df_historica = df_historica[~((df_historica["ANIO"].astype(str) == anio) & (df_historica["MES"].astype(str) == mes))]

        # Agregar nuevo registro
        df_historica = pd.concat([
            df_historica,
            pd.DataFrame([{"ANIO": anio, "MES": mes, "CONSUMO_TOTAL_KWH": consumo_total}])
        ], ignore_index=True)

        df_historica.to_csv(ruta_historica, sep=";", index=False, encoding="utf-8-sig")
        # flash("✅ Consumo total guardado en DataHistorica.csv", "success")

            # --- Parte: guardar en archivos de distritos ---
        distritos = [
            "Cochabamba", "Colcabamba", "Huanchay", "Huaraz", "Independencia", "Jangas",
            "La Libertad", "Olleros", "Pampas Grande", "Pariacoto", "Pira", "Tarica"
        ]

        for distrito in distritos:
            # Filtra el DataFrame para ese distrito
            consumo_distrito = df_filtrado[
                df_filtrado["DISTRITO"].str.upper().str.strip() == distrito.upper()
            ]["CONSUMO"].sum()

            # Ruta del archivo CSV del distrito
            ruta_distrito = os.path.join("static", "data", "Distritos", f"{distrito}.csv")

            # Si existe, lo leemos, si no, lo creamos vacío
            if os.path.exists(ruta_distrito):
                df_distrito = pd.read_csv(ruta_distrito, sep=";", encoding="utf-8")
            else:
                df_distrito = pd.DataFrame(columns=["ANIO", "MES", "CONSUMO_TOTAL_KWH"])

            # Eliminar cualquier registro del mismo año y mes
            df_distrito = df_distrito[
                ~((df_distrito["ANIO"].astype(str) == anio) & (df_distrito["MES"].astype(str) == mes))
            ]

            # Agregar nuevo registro
            nueva_fila = {
                "ANIO": anio,
                "MES": mes,
                "CONSUMO_TOTAL_KWH": consumo_distrito
            }
            df_distrito = pd.concat([df_distrito, pd.DataFrame([nueva_fila])], ignore_index=True)

            # Guardar de nuevo
            df_distrito.to_csv(ruta_distrito, sep=";", index=False, encoding="utf-8-sig")
            print(f"[{distrito}] -> Consumo: {consumo_distrito}")
            print(f"Guardado en: {ruta_distrito}")
            
            if os.path.exists(ruta_filtrada):
                os.remove(ruta_filtrada)

            ruta_temporal = os.path.join("static", "data", "DataTemporal.csv")
            if os.path.exists(ruta_temporal):
                os.remove(ruta_temporal)
                
        flash("✅ Datos correctamente", "success")
        return redirect("/subir-archivo")

    except Exception as e:
        flash(f"❌ Error al filtrar y guardar datos: {str(e)}", "danger")
        return redirect("/subir-archivo")
