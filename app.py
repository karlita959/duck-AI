import os
import re
import unicodedata

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# Opcional: si defines la variable de entorno ANTHROPIC_API_KEY, el agente
# responderá CUALQUIER pregunta usando la API de Claude. Si no, usa la base
# de conocimiento local de este archivo (funciona sin cuenta ni internet).
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-haiku-5-5"

SYSTEM_PROMPT = (
    "Eres un asistente experto en cuidados de animales exóticos (reptiles, aves, "
    "anfibios, mamíferos pequeños, arácnidos, peces exóticos, etc.). Responde en "
    "español, de forma clara, amable y práctica. Si el caso parece una emergencia "
    "o hay síntomas graves, recomienda acudir a un veterinario especializado en "
    "exóticos. Si te dan las gracias, responde con amabilidad."
)


def normalizar(texto):
    """Pasa a minúsculas, quita acentos y signos para comparar mejor."""
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    return f" {' '.join(texto.split())} "


# ---------------------------------------------------------------------------
# Base de conocimiento local
# ---------------------------------------------------------------------------
ESPECIES = [
    {
        "kw": ["iguana", "iguanas"],
        "resp": (
            "Cuidados de la iguana verde:\n"
            "- Terrario grande (mínimo 2 x 1 x 2 m para adultos), con mucha altura y ramas para trepar.\n"
            "- Zona de calor (basking) de 35 a 40 °C y el resto entre 26 y 30 °C.\n"
            "- Luz UVB de 10.0 a 12.0 % y foco de calor durante 12 a 14 horas al día.\n"
            "- Humedad entre 70 y 80 %, con rociado diario y un baño de agua tibia.\n"
            "- Dieta mayormente vegetal: hojas de mostaza, col rizada, nabo, flores comestibles y algo de fruta.\n"
            "- Evita la espinaca y la lechuga iceberg en exceso (bloquean el calcio).\n"
            "- Suplementa calcio con vitamina D3 unas 3 veces por semana."
        ),
    },
    {
        "kw": ["gecko", "geckos", "leopardo", "eublepharis"],
        "resp": (
            "Cuidados del gecko leopardo:\n"
            "- Terrario de unos 45 x 45 x 30 cm para un adulto.\n"
            "- Punto caliente de 30 a 32 °C y zona fría de 22 a 24 °C; sin luz UVB obligatoria.\n"
            "- Humedad baja (30 a 40 %) y un refugio húmedo para la muda.\n"
            "- Sustrato seguro: papel de cocina, toallas o baldosa. Evita la arena, puede causar impactación.\n"
            "- Dieta de insectos (grillos, cucarachas de Madagascar, gusanos de la harina) con gut load y polvo de calcio.\n"
            "- Ofrece agua en un recipiente bajo y limpio."
        ),
    },
    {
        "kw": ["tortuga", "tortugas", "galapago", "jicotea", "orejas rojas"],
        "resp": (
            "Cuidados básicos de tortugas:\n"
            "- Identifica si es acuática, semiacuática o terrestre; cada una necesita un hábitat distinto.\n"
            "- Las acuáticas necesitan agua limpia y filtrada, con una zona para asolearse fuera del agua.\n"
            "- Luz UVB y lámpara de calor para sintetizar vitamina D3 y regular su metabolismo.\n"
            "- Dieta variada: pellets de calidad, verduras de hoja verde y algo de proteína según la especie.\n"
            "- Suplementa calcio y revisa con frecuencia el caparazón por manchas, blandura o heridas.\n"
            "- Cambia parcialmente el agua cada semana y revisa la temperatura del agua."
        ),
    },
    {
        "kw": ["serpiente", "serpientes", "pitón", "piton", "python", "boa", "culebra", "colubrido"],
        "resp": (
            "Cuidados generales de serpientes exóticas:\n"
            "- El terrario debe ser seguro, con cierre firme y sin huecos por donde escapen.\n"
            "- Gradiente térmico: un lado caliente y otro frío, para que elija su temperatura.\n"
            "- Humedad según la especie (las pitones y boas suelen necesitar humedad alta en la etapa de muda).\n"
            "- Ofrece presas del tamaño adecuado (aprox. el diámetro más ancho del cuerpo) y descongeladas.\n"
            "- No alimentes con la mano para evitar mordidas por confusión.\n"
            "- Si deja de comer o regurgita, revisa temperatura y consulta a un veterinario de exóticos."
        ),
    },
    {
        "kw": ["loro", "loros", "perico", "periquito", "guacamayo", "cacatua", "agapornis", "ave", "aves", "pajaro", "canario"],
        "resp": (
            "Cuidados básicos de aves exóticas (loros, periquitos, guacamayos):\n"
            "- Jaula amplia, con perchas de distintos diámetros y juguetes para mantenerlos activos.\n"
            "- Dieta: pellets de calidad como base, más verduras, frutas y una pequeña cantidad de semillas.\n"
            "- Alimentos PROHIBIDOS: aguacate, chocolate, cafeína, alcohol, sal y comida con azúcar o grasa.\n"
            "- Luz natural o artificial de 10 a 12 horas al día y sueño de 10 a 12 horas en oscuridad.\n"
            "- Baños con rociado o agua tibia algunas veces por semana.\n"
            "- Las aves ocultan los síntomas: plumas hinchadas, sin apetito o pocas heces son señal de consulta veterinaria urgente."
        ),
    },
    {
        "kw": ["chinchilla", "chinchillas"],
        "resp": (
            "Cuidados de la chinchilla:\n"
            "- Jaula grande con repisas y mucho espacio para saltar. Temperatura ideal de 18 a 22 °C.\n"
            "- Evita el calor y la humedad: pueden sufrir golpes de calor por encima de 25 °C.\n"
            "- Dieta: heno de timothy ilimitado, pellets específicos para chinchilla y poca fruta seca como premio.\n"
            "- Baño de arena especial (polvo de pumita o arena de chinchilla) 2 o 3 veces por semana. Nunca uses agua.\n"
            "- Son muy sensibles al estrés: manipúlalas con calma y desde pequeñas."
        ),
    },
    {
        "kw": ["erizo", "erizos", "hurón", "huron", "hurones", "cobaya", "cuyo", "conejo", "conejos", "degu"],
        "resp": (
            "Cuidados de pequeños mamíferos exóticos:\n"
            "- Erizo africano: temperatura de 24 a 27 °C, jaula con buena ventilación y rueda sin barrotes. Vitaminas en el agua. Evita baños frecuentes.\n"
            "- Hurón: necesita temperatura fresca (menos de 25 °C), dieta alta en proteína para hurones y juguetes.\n"
            "- Cobayas y conejos: heno ilimitado, verduras frescas y vitamina C (en cobayas es indispensable).\n"
            "- Degu: heno, pellets para degus y poca azúcar, que les causa diabetes.\n"
            "- En todos los casos, un cambio de apetito o de heces es motivo para ir al veterinario."
        ),
    },
    {
        "kw": ["ajolote", "ajolotes", "axolotl"],
        "resp": (
            "Cuidados del ajolote mexicano:\n"
            "- Acuario de al menos 40 litros para uno, sin corriente fuerte.\n"
            "- Agua fría, entre 16 y 18 °C. No le conviene el calor (por encima de 22 °C).\n"
            "- Usa agua declorada y cambia el 20 al 30 % cada semana.\n"
            "- Sustrato de grava gruesa, no arena fina, para evitar que la trague.\n"
            "- Dieta de lombrices, larvas de mosca o pellets para carnívoros acuáticos. Alimenta cada 2 o 3 días."
        ),
    },
    {
        "kw": ["rana", "ranas", "sapo", "sapos", "anfibio", "anfibios", "pacman", "dendrobates"],
        "resp": (
            "Cuidados generales de anfibios exóticos:\n"
            "- Mantén la humedad según la especie, con rociado y sustrato húmedo, pero con buena ventilación.\n"
            "- Usa agua declorada o de osmosis para rociar y para el recipiente de agua.\n"
            "- Dieta de insectos pequeños (grillos, moscas de la fruta) con polvo de calcio.\n"
            "- Las ranas de dardo venenosas necesitan dieta específica; no las manipules sin guantes y sin lavarte las manos después.\n"
            "- Evita sustancias químicas, perfumes y jabones cerca del terrario."
        ),
    },
    {
        "kw": ["tarantula", "tarantulas", "araña", "arana", "aranas", "arañas", "arácnido", "aracnido", "escorpion", "escorpión"],
        "resp": (
            "Cuidados de arácnidos exóticos (tarántulas y escorpiones):\n"
            "- Terrario de tamaño acorde a su envergadura; prefiere mayor altura para tarántulas arborícolas.\n"
            "- Sustrato profundo para excavadoras y temperatura de 22 a 28 °C según la especie.\n"
            "- Humedad: baja en especies de desierto, moderada-alta en especies tropicales (rociando solo una parte del terrario).\n"
            "- Ofrece agua en un recipiente pequeño y estable.\n"
            "- Alimenta con insectos vivos del tamaño adecuado y retira lo que no se coma.\n"
            "- No las manipules: pueden liberar pelos urticantes o tener veneno potente."
        ),
    },
    {
        "kw": ["veterinario", "veterinaria", "enfermo", "enferma", "emergencia", "sintoma", "sintomas", "urgencia"],
        "resp": (
            "Si tu animal exótico presenta síntomas como falta de apetito, letargo, heces anormales, "
            "respiración con ruido, pérdida de peso o heridas, consulta cuanto antes a un veterinario "
            "especializado en animales exóticos. En los exóticos los síntomas suelen aparecer tarde, "
            "así que ante la duda, consulta. Anota los cambios de los últimos días para contárselos al veterinario."
        ),
    },
    {
        "kw": ["comida", "alimento", "alimentar", "dieta", "comer", "come"],
        "resp": (
            "La dieta depende completamente de la especie. Dime qué animal tienes (iguana, gecko, "
            "tortuga, loro, chinchilla, etc.) y te doy una dieta concreta, con alimentos recomendados "
            "y los que debes evitar."
        ),
    },
    {
        "kw": ["temperatura", "calor", "frio", "humedad", "terrario", "jaula", "habitat", "hábitat"],
        "resp": (
            "El hábitat es lo más importante en los exóticos: temperatura, humedad, luz y espacio. "
            "Cada especie tiene valores distintos. Dime qué animal tienes y te indico los rangos exactos "
            "de temperatura, humedad y tamaño de su terrario o jaula."
        ),
    },
]

SOCIAL = [
    {
        "kw": ["hola", "buenas", "buenos dias", "buenas tardes", "buenas noches", "hey", "que tal", "saludos"],
        "resp": (
            "¡Hola! Soy tu asistente de cuidados de animales exóticos. Puedes preguntarme sobre "
            "iguanas, geckos, tortugas, serpientes, loros, chinchillas, erizos, ajolotes, ranas, "
            "tarántulas y más. ¿En qué te ayudo?"
        ),
    },
    {
        "kw": ["gracias", "muchas gracias", "te agradezco", "mil gracias", "thank you", "thanks", "gracias por tu ayuda"],
        "resp": "¡De nada! Me alegra poder ayudarte. Si tienes otra duda sobre tu animal exótico, aquí estoy. 🦎",
    },
    {
        "kw": ["adios", "chao", "bye", "hasta luego", "nos vemos", "hasta pronto", "despedida", "me voy", "hasta la vista"],
        "resp": "¡Hasta luego! Cuida mucho a tu mascota exótica y vuelve cuando quieras. 🦜",
    },
    {
        "kw": ["como estas", "que haces", "quien eres", "que eres", "tu nombre"],
        "resp": (
            "Soy un asistente virtual especializado en el cuidado de animales exóticos. "
            "Estoy listo para responder tus dudas sobre alimentación, hábitat, salud y comportamiento."
        ),
    },
]

RESPUESTA_POR_DEFECTO = (
    "No tengo una respuesta específica para eso en mi base de conocimiento local. "
    "Intenta mencionar el nombre del animal (por ejemplo: iguana, gecko, loro, chinchilla) y "
    "tu pregunta concreta (alimentación, temperatura, salud, etc.). "
    "Para respuestas a cualquier tema, configura la variable ANTHROPIC_API_KEY."
)


def puntuar(texto_norm, entradas):
    """Devuelve la entrada con más palabras clave encontradas (o None)."""
    mejor, mejor_puntaje = None, 0
    for entrada in entradas:
        puntaje = sum(1 for kw in entrada["kw"] if f" {normalizar(kw).strip()} " in texto_norm)
        if puntaje > mejor_puntaje:
            mejor, mejor_puntaje = entrada, puntaje
    return mejor


def responder_local(mensaje):
    texto = normalizar(mensaje)

    especie = puntuar(texto, ESPECIES)
    if especie:
        return especie["resp"]

    social = puntuar(texto, SOCIAL)
    if social:
        return social["resp"]

    return RESPUESTA_POR_DEFECTO


def responder_con_claude(mensaje):
    cabeceras = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    cuerpo = {
        "model": MODEL,
        "max_tokens": 800,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": mensaje}],
    }
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=cabeceras,
        json=cuerpo,
        timeout=30,
    )
    r.raise_for_status()
    partes = [b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text"]
    return "".join(partes).strip()


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    datos = request.get_json(silent=True) or {}
    mensaje = (datos.get("message") or "").strip()

    if not mensaje:
        return jsonify({"reply": "Escribe una pregunta, por favor."}), 400

    if ANTHROPIC_API_KEY:
        try:
            return jsonify({"reply": responder_con_claude(mensaje)})
        except Exception as error:  # si la API falla, usamos la base local
            print(f"Error con la API de Claude: {error}")

    return jsonify({"reply": responder_local(mensaje)})


if __name__ == "__main__":
    app.run(debug=True)
