const chat = document.getElementById("chat");
const formulario = document.getElementById("formulario");
const entrada = document.getElementById("entrada");
const boton = document.getElementById("enviar");

function agregarMensaje(texto, tipo) {
  const div = document.createElement("div");
  div.className = `mensaje ${tipo}`;
  div.textContent = texto; // textContent evita inyección de HTML
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

async function enviarPregunta(texto) {
  agregarMensaje(texto, "usuario");
  boton.disabled = true;

  const escribiendo = agregarMensaje("Escribiendo...", "bot escribiendo");

  try {
    const respuesta = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: texto }),
    });

    const datos = await respuesta.json();
    escribiendo.remove();
    agregarMensaje(datos.reply || "No recibí respuesta. Intenta de nuevo.", "bot");
  } catch (error) {
    escribiendo.remove();
    agregarMensaje(
      "Hubo un problema de conexión con el servidor. Revisa que app.py esté corriendo.",
      "bot"
    );
    console.error(error);
  } finally {
    boton.disabled = false;
    entrada.focus();
  }
}

formulario.addEventListener("submit", (evento) => {
  evento.preventDefault();
  const texto = entrada.value.trim();
  if (!texto) return;
  entrada.value = "";
  enviarPregunta(texto);
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => enviarPregunta(chip.textContent));
});
