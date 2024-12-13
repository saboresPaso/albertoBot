from fastapi import FastAPI, Request, Form, Response
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()  # Carga las variables de entorno desde el archivo .env

# Configuración de API Keys
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN =  os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATS_APP")  # Número de Twilio


botAlbert = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=os.getenv("OPENAI_API_KEY")
)

# Inicializar clientes
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Historial de conversaciones
historial_conversacion = {}

# Modelo para solicitudes del cliente
class Mensaje(BaseModel):
    sender: str
    message: str

# Crear instancia de FastAPI
app = FastAPI()


# Ruta para manejar mensajes entrantes
@app.post("/webhook/")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),  # Número del remitente
    Body: str = Form(...)   # Mensaje recibido
    ):
    user_message = Body.strip()
        

    remitente = "tele"+From+""
    if remitente not in historial_conversacion:
        historial_conversacion[remitente] = []

    try:
        # Generar respuesta con OpenAI
        respuesta, historial_actualizado = generar_respuesta_openai(
            user_message, historial_conversacion[remitente]
        )
        historial_conversacion[remitente] = historial_actualizado

        # Crear la respuesta de Twilio
        twiml_response = MessagingResponse()
        twiml_response.message(respuesta)

        # Devolver la respuesta con el Content-Type correcto
        return Response(content=str(twiml_response), media_type="application/xml")
        
    except Exception as e:
        print(f"Error al procesar el mensaje: {e}")
        error_response = MessagingResponse()
        error_response.message("Hubo un problema procesando tu solicitud. Por favor, inténtalo más tarde.")
        return Response(content=str(error_response), media_type="application/xml")



# Función para generar respuestas con OpenAI
def generar_respuesta_openai(mensaje_usuario, historial):
    contexto = [
        {"role": "system", "content": 
            "Eres un asistente útil que responde preguntas de manera clara y concisa.",
        }
    ]


    # Agregar historial al contexto
    for mensaje in historial:
        contexto.append(mensaje)

    # Añadir el nuevo mensaje del usuario
    contexto.append({"role": "user", "content": mensaje_usuario})

    completion = botAlbert.chat.completions.create(
        model="gpt-4o",
        messages=contexto,
        max_tokens=500
    )


    # Obtener texto de la respuesta
    respuesta_texto = completion.choices[0].message.content.strip()

    # Añadir la respuesta al historial
    historial.append({"role": "assistant", "content": respuesta_texto})

    return respuesta_texto, historial

