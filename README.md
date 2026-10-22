# Asistente de cuidados de animales exóticos

Agente de chat hecho con HTML, CSS, JavaScript y Python (Flask).

## Estructura

```
agente-exoticos/
├── app.py                  # Servidor y lógica del agente (Python)
├── requirements.txt        # Dependencias
├── templates/
│   └── index.html          # Interfaz
└── static/
    ├── css/style.css       # Estilos
    └── js/script.js        # Lógica del chat (JavaScript)
```

## Cómo correrlo

1. Crea y activa un entorno virtual:

   ```bash
   python -m venv venv
   source venv/bin/activate      # En Windows: venv\Scripts\activate
   ```

2. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Inicia el servidor:

   ```bash
   python app.py
   ```

4. Abre en el navegador: http://127.0.0.1:5000

## Modos de respuesta

- **Sin API key:** responde con la base de conocimiento local incluida en `app.py` (iguanas, geckos, tortugas, serpientes, aves, chinchillas, erizos, ajolotes, ranas, arácnidos, etc.), además de saludos, gracias y despedidas.
- **Con API key de Claude:** responde cualquier pregunta. Para activarlo:

  ```bash
  export ANTHROPIC_API_KEY="tu_clave"        # macOS / Linux
  set ANTHROPIC_API_KEY=tu_clave             # Windows (CMD)
  ```

  Si la API falla, el agente usa automáticamente la base local.

## Subir a GitHub

```bash
git init
echo "venv/" > .gitignore
echo "__pycache__/" >> .gitignore
git add .
git commit -m "Agente de cuidados de animales exóticos"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/agente-exoticos.git
git push -u origin main
```

Nunca subas tu API key al repositorio.

## Aviso

Esta herramienta da orientación general. Ante síntomas o emergencias, consulta siempre a un veterinario especializado en animales exóticos.
