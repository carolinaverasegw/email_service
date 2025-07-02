import os
from flask import Flask, request, jsonify
from google.cloud import storage
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Inicializa la aplicación Flask
app = Flask(__name__)

# --- Configuración ---
# Estas variables se configurarán en Cloud Run como variables de entorno
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL') # El email verificado en SendGrid desde el que enviarás
BUCKET_NAME = os.environ.get('BUCKET_NAME')
TEMPLATE_FILE_NAME = os.environ.get('TEMPLATE_FILE_NAME')

# Inicializa el cliente de Google Cloud Storage
storage_client = storage.Client()

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Endpoint que recibe la llamada de Dialogflow.
    """
    try:
        # 1. Obtener el JSON de la solicitud
        req_data = request.get_json(force=True)

        # 2. Extraer el email del destinatario de los parámetros de Dialogflow
        recipient_email = req_data['queryResult']['parameters']['email']
        if not recipient_email:
            raise ValueError("El parámetro 'email' no se encontró en la solicitud.")

        # 3. Descargar la plantilla desde GCS
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(TEMPLATE_FILE_NAME)
        html_content = blob.download_as_text()

        # 4. Crear el objeto del correo
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=recipient_email,
            subject='Correo enviado desde el Agente Conversacional',
            html_content=html_content
        )

        # 5. Enviar el correo usando SendGrid
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        # Si llegamos aquí, el correo se envió con éxito (código 2xx)
        print(f"Correo enviado a {recipient_email}, status code: {response.status_code}")

        # 6. Preparar la respuesta para Dialogflow
        fulfillment_text = f"¡Listo! He enviado el correo a {recipient_email}."
        
        return jsonify({'fulfillmentText': fulfillment_text})

    except Exception as e:
        print(f"Error: {e}")
        # En caso de error, enviar una respuesta clara a Dialogflow
        error_text = "Lo siento, ha ocurrido un problema técnico y no he podido enviar el correo."
        return jsonify({'fulfillmentText': error_text})

if __name__ == "__main__":
    # Gunicorn usará esto para ejecutar la app. El puerto se define por Cloud Run.
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))