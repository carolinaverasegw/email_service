import os
from flask import Flask, request, jsonify
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Inicializa la aplicación Flask
app = Flask(__name__)

# --- Configuración ---
# Estas variables se configurarán en Cloud Run como "variables de entorno"
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL') # Tu email verificado en SendGrid

@app.route('/send_email', methods=['POST'])
def send_email():
    """
    Endpoint para recibir una solicitud y enviar un correo.
    Espera un JSON con: {"recipient_email": "...", "subject": "...", "body": "..."}
    """
    # 1. Validar que la configuración básica exista
    if not SENDGRID_API_KEY or not SENDER_EMAIL:
        return jsonify({"error": "Configuración del servidor incompleta."}), 500

    try:
        # 2. Obtener los datos del cuerpo de la solicitud (JSON)
        data = request.get_json()
        recipient = data.get('recipient_email')
        subject = data.get('subject')
        body = data.get('body')

        # Validar que los datos necesarios fueron enviados
        if not all([recipient, subject, body]):
            return jsonify({"error": "Faltan datos en la solicitud. Se requiere 'recipient_email', 'subject' y 'body'."}), 400

        # 3. Crear el objeto del correo
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=recipient,
            subject=subject,
            html_content=f"<p>
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; }
                        .container { padding: 20px; border: 1px solid #ddd; border-radius: 8px; max-width: 600px; margin: 20px auto; }
                        .header { background-color: #f4f4f4; padding: 10px; text-align: center; }
                        .footer { font-size: 0.8em; text-align: center; color: #777; margin-top: 20px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>Notificación Automática</h2>
                        </div>
                        <p>Hola,</p>
                        <p>Este es un mensaje generado automáticamente a través de una solicitud en nuestro agente conversacional.</p>
                        <p>Este sistema automatizado facilita la comunicación y el envío de información estándar de manera eficiente.</p>
                        <p>¡Gracias por utilizar nuestros servicios!</p>
                        <div class="footer">
                            <p>Este correo fue enviado desde un sistema automatizado. Por favor, no respondas a este mensaje.</p>
                        </div>
                    </div>
                </body>
                </html>
            </p>" # Puedes usar HTML directamente aquí
        )

        # 4. Enviar el correo a través de SendGrid
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        # 5. Devolver una respuesta de éxito
        print(f"Correo enviado a {recipient}. Status: {response.status_code}")
        return jsonify({"message": f"Correo enviado exitosamente a {recipient}"}), 200

    except Exception as e:
        # Manejo de errores
        print(f"Error al enviar correo: {e}")
        return jsonify({"error": "Ocurrió un error interno al procesar la solicitud."}), 500

if __name__ == "__main__":
    # Este bloque permite ejecutar el servidor en modo de desarrollo local.
    # Cloud Run usará Gunicorn para iniciar la aplicación.
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
