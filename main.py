import os
from flask import Flask, request, jsonify
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# --- Configuración y Validación Inicial ---
# Estas variables deben estar configuradas en Cloud Run.
# Si faltan, el servicio no se iniciará y el log lo indicará claramente.
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')

# Validar al iniciar el contenedor. Si falta una variable, el log de Cloud Run mostrará este error.
if not SENDGRID_API_KEY:
    raise RuntimeError("La variable de entorno SENDGRID_API_KEY no está configurada. Por favor, añádela en la configuración de Cloud Run.")
if not SENDER_EMAIL:
    raise RuntimeError("La variable de entorno SENDER_EMAIL no está configurada. Por favor, añádela en la configuración de Cloud Run.")

# Inicializa la aplicación Flask
app = Flask(__name__)

@app.route('/send_email', methods=['POST'])
def send_email():
    """
    Endpoint para recibir una solicitud y enviar un correo.
    Espera un JSON con: {"recipient_email": "...", "subject": "...", "body": "..."}
    """
    try:
        # 1. Obtener los datos del cuerpo de la solicitud (JSON)
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibió un cuerpo JSON en la solicitud."}), 400

        recipient = data.get('recipient_email')
        subject = data.get('subject')
        body = data.get('body')

        # Validar que los datos necesarios fueron enviados
        if not all([recipient, subject, body]):
            return jsonify({"error": "Faltan datos en la solicitud. Se requiere 'recipient_email', 'subject' y 'body'."}), 400

        # 2. Crear el objeto del correo
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=recipient,
            subject=subject,
            html_content=f"<p>{body}</p>"
        )

        # 3. Enviar el correo a través de SendGrid
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        # 4. Devolver una respuesta de éxito si SendGrid responde con un código 2xx
        if 200 <= response.status_code < 300:
            print(f"Correo enviado a {recipient}. Status: {response.status_code}")
            return jsonify({"message": f"Correo enviado exitosamente a {recipient}"}), 200
        else:
            # Si SendGrid devuelve un error, lo registramos y notificamos con más detalle.
            print(f"Error de SendGrid al enviar a {recipient}. Status: {response.status_code}. Body: {response.body}")
            return jsonify({
                "error": "El proveedor de correo (SendGrid) rechazó la solicitud.",
                "sendgrid_status": response.status_code,
                "sendgrid_body": response.body.decode('utf-8')
            }), 502 # 502 Bad Gateway es apropiado para un error del servicio externo

    except Exception as e:
        # Manejo de errores inesperados
        print(f"Error inesperado al procesar la solicitud: {e}")
        return jsonify({"error": "Ocurrió un error interno inesperado."}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
