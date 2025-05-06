from flask import Flask, render_template
from routes.rutas_sidebar import sidebar  # importa el blueprint
from routes.upload import upload_bp  # Importamos el blueprint de subida
from routes.prediction import predict  # Importamos el blueprint de subida

app = Flask(__name__)

# Clave secreta para poder usar mensajes flash (como notificaciones de error o éxito)
app.secret_key = 'clave_super_secreta'

# Registro de blueprint
app.register_blueprint(sidebar)

# Registramos el blueprint para que Flask reconozca las rutas definidas en upload.py
app.register_blueprint(upload_bp)

# Registro de blueprint para las predicciones y su debido procesoo
app.register_blueprint(predict)

if __name__=="__main__":
    app.run(
        debug=True,
        port=5054
)