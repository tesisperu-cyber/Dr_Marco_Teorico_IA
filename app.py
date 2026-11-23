import os
from typing import Any

import requests
import streamlit as st

from config import APP_NAME, APP_VERSION, BRAND
from modules.contenidos import UNIDADES, obtener_unidad

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
APP_URL = os.getenv("APP_URL", "http://localhost:8501")

st.set_page_config(
    page_title=f"{APP_NAME} {APP_VERSION}",
    page_icon="📚",
    layout="wide",
)


@st.cache_data(ttl=1800, show_spinner=False)
def get_free_chat_models() -> list[dict[str, str]]:
    """Consulta el catálogo público y devuelve modelos de texto con entrada/salida gratuitas."""
    response = requests.get(OPENROUTER_MODELS_URL, timeout=30)
    response.raise_for_status()
    free_models: list[dict[str, str]] = []

    for model in response.json().get("data", []):
        pricing = model.get("pricing") or {}
        try:
            prompt_price = float(pricing.get("prompt", "inf"))
            completion_price = float(pricing.get("completion", "inf"))
        except (TypeError, ValueError):
            continue

        architecture = model.get("architecture") or {}
        modality = str(architecture.get("modality") or "").lower()
        input_modalities = architecture.get("input_modalities") or []
        output_modalities = architecture.get("output_modalities") or []

        text_compatible = (
            not modality or "text" in modality
        ) and (
            not input_modalities or "text" in input_modalities
        ) and (
            not output_modalities or "text" in output_modalities
        )

        model_id = model.get("id")
        if (
            model_id
            and prompt_price == 0
            and completion_price == 0
            and text_compatible
        ):
            free_models.append({
                "id": model_id,
                "name": model.get("name") or model_id,
            })

    return sorted(free_models, key=lambda item: item["name"].lower())


def load_system_prompt() -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt")
    try:
        with open(prompt_path, "r", encoding="utf-8") as file:
            return file.read().strip()
    except OSError:
        return (
            "Eres Dr. Marco Teórico, profesor y tutor científico. "
            "Explica con rigor, claridad y ejemplos. No inventes fuentes, autores, "
            "DOI ni referencias. Distingue hechos, interpretaciones y controversias. "
            "Reconoce tus límites y promueve la validación humana."
        )


def call_openrouter(
    api_key: str,
    messages: list[dict[str, str]],
    model_id: str,
) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": APP_URL,
        "X-Title": APP_NAME,
    }
    payload = {
        "model": model_id,
        "messages": messages,
        "temperature": 0.35,
    }
    response = requests.post(
        OPENROUTER_CHAT_URL,
        headers=headers,
        json=payload,
        timeout=90,
    )
    if not response.ok:
        detail = response.text[:1200]
        raise RuntimeError(f"OpenRouter respondió HTTP {response.status_code}: {detail}")

    data: dict[str, Any] = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"OpenRouter no devolvió opciones de respuesta: {data}")
    content = choices[0].get("message", {}).get("content", "")
    if isinstance(content, list):
        # Algunos proveedores devuelven contenido en bloques.
        content = "\n".join(
            block.get("text", "") for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("El modelo devolvió una respuesta vacía.")
    return content.strip()


def chat_with_fallback(
    api_key: str,
    messages: list[dict[str, str]],
    selected_model: str,
    model_ids: list[str],
) -> tuple[str, str, list[str]]:
    """Prueba primero el modelo elegido y luego otras opciones gratuitas detectadas."""
    ordered_models = [selected_model] + [
        model_id for model_id in model_ids if model_id != selected_model
    ]
    errors: list[str] = []
    for model_id in ordered_models:
        try:
            answer = call_openrouter(api_key, messages, model_id)
            return answer, model_id, errors
        except Exception as exc:
            errors.append(f"{model_id}: {exc}")
    raise RuntimeError(
        "No se pudo obtener respuesta con los modelos gratuitos detectados. "
        + " | ".join(errors[:4])
    )


def build_unit_context(selection: str) -> str:
    unit = obtener_unidad(selection)
    parts = [
        f"UNIDAD ACTUAL: {unit.get('titulo', selection)}",
        f"OBJETIVO: {unit.get('objetivo', '')}",
        f"EXPLICACIÓN LOCAL: {unit.get('explicacion', '')}",
        "IDEAS CLAVE: " + "; ".join(unit.get("ideas_clave", [])),
        f"PREGUNTA SOCRÁTICA: {unit.get('pregunta', '')}",
        f"ACTIVIDAD: {unit.get('actividad', '')}",
    ]
    return "\n".join(part for part in parts if part)


# ---------------- Sidebar: configuration ----------------
with st.sidebar:
    st.header("Configuración")
    secret_key = ""
    try:
        secret_key = st.secrets.get("OPENROUTER_API_KEY", "")
    except Exception:
        pass

    api_key = st.text_input(
        "Clave API de OpenRouter",
        value=secret_key or os.getenv("OPENROUTER_API_KEY", ""),
        type="password",
        help="La clave se utiliza en esta sesión. No la compartas ni la subas a GitHub.",
    )
    st.caption("Los modelos se consultan dinámicamente desde el catálogo de OpenRouter.")

    if st.button("Actualizar catálogo gratuito", use_container_width=True):
        get_free_chat_models.clear()
        st.session_state.pop("openrouter_models", None)
        st.rerun()

    models: list[dict[str, str]] = []
    model_ids: list[str] = []
    selected_model = None

    if api_key:
        try:
            models = get_free_chat_models()
            model_ids = [model["id"] for model in models]
            if models:
                labels = {
                    model["id"]: f'{model["name"]} — {model["id"]}'
                    for model in models
                }
                previous = st.session_state.get("marco_selected_model")
                index = model_ids.index(previous) if previous in model_ids else 0
                selected_model = st.selectbox(
                    "Modelo inicial",
                    options=model_ids,
                    index=index,
                    format_func=lambda model_id: labels.get(model_id, model_id),
                    key="marco_selected_model",
                )
                st.success(f"{len(models)} modelos gratuitos de texto detectados.")
            else:
                st.warning("No se detectaron modelos gratuitos compatibles en este momento.")
        except requests.RequestException as exc:
            st.error(f"No se pudo consultar el catálogo de OpenRouter: {exc}")
        except Exception as exc:
            st.error(f"No se pudo procesar el catálogo: {exc}")
    else:
        st.info("Introduce tu clave API para consultar el catálogo y activar la profesora IA.")

    st.divider()
    st.header("Ruta de aprendizaje")
    opciones = list(UNIDADES.keys())
    seleccion = st.radio("Selecciona una unidad", opciones, key="marco_unidad")

    st.divider()
    st.caption("La clave no se guarda en el repositorio. En Streamlit Cloud puedes usar Secrets.")


# ---------------- Main interface ----------------
st.title(f"📚 {APP_NAME}")
st.caption(f"{BRAND} · Versión {APP_VERSION}")
st.markdown(
    "Un espacio de aprendizaje para comprender los fundamentos científicos, "
    "filosóficos y metodológicos de la investigación."
)

unidad = obtener_unidad(seleccion)
st.subheader(unidad["titulo"])
st.write(unidad["objetivo"])

tab_chat, tab1, tab2, tab3, tab_about = st.tabs(
    ["💬 Conversar con Dr. Marco", "📖 Aprender", "💭 Reflexionar", "✍️ Practicar", "ℹ️ Acerca de"]
)

with tab_chat:
    st.subheader("Conversa con tu profesor")
    st.write(
        "Pregunta por fundamentos científicos, paradigmas, metodología, "
        "conceptos, constructos, teorías o decisiones de investigación."
    )
    if "marco_messages" not in st.session_state:
        st.session_state.marco_messages = []

    for message in st.session_state.marco_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input(
        "Por ejemplo: explícame la diferencia entre epistemología y metodología..."
    )
    if prompt:
        st.session_state.marco_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        unit_context = build_unit_context(seleccion)
        system_message = (
            load_system_prompt()
            + "\n\nCONTEXTO PEDAGÓGICO LOCAL DE LA UNIDAD SELECCIONADA:\n"
            + unit_context
            + "\n\nUsa este contexto cuando sea pertinente. No afirmes que consultaste "
              "bases bibliográficas ni que verificaste referencias si no lo hiciste. "
              "La aplicación aún no integra RAG bibliográfico."
        )
        conversation = [{"role": "system", "content": system_message}]
        conversation.extend(st.session_state.marco_messages[-12:])

        with st.chat_message("assistant"):
            if not api_key:
                answer = (
                    "Para conversar con Dr. Marco Teórico, introduce tu clave de "
                    "OpenRouter en el panel lateral. Los contenidos de aprendizaje "
                    "locales siguen disponibles."
                )
                st.info(answer)
            elif not selected_model or not model_ids:
                answer = (
                    "No hay modelos gratuitos de texto disponibles en el catálogo "
                    "consultado. Actualiza el catálogo o inténtalo más tarde."
                )
                st.warning(answer)
            else:
                with st.spinner("Dr. Marco Teórico está preparando la explicación..."):
                    try:
                        answer, used_model, errors = chat_with_fallback(
                            api_key, conversation, selected_model, model_ids
                        )
                        st.caption(f"Modelo utilizado: {used_model}")
                        if errors:
                            st.caption(
                                f"Se activó el respaldo automático tras "
                                f"{len(errors)} intento(s) fallido(s)."
                            )
                        st.markdown(answer)
                    except Exception as exc:
                        answer = f"No fue posible obtener una respuesta. Detalle: {exc}"
                        st.error(answer)
            st.session_state.marco_messages.append(
                {"role": "assistant", "content": answer}
            )

with tab1:
    st.markdown("### Explicación")
    st.write(unidad["explicacion"])
    st.markdown("### Ideas clave")
    for idea in unidad["ideas_clave"]:
        st.markdown(f"- {idea}")

with tab2:
    st.markdown("### Pregunta socrática")
    st.write(unidad["pregunta"])
    respuesta = st.text_area(
        "Escribe tu reflexión",
        key=f"reflexion_{seleccion}",
        height=150,
        placeholder="Explica tu razonamiento con tus propias palabras...",
    )
    if st.button("Mostrar orientación para reflexionar", key=f"orientar_{seleccion}"):
        st.info(unidad["orientacion"])
        if respuesta.strip():
            st.success("Tu reflexión quedó escrita en esta sesión. No se guarda de forma permanente.")

with tab3:
    st.markdown("### Actividad")
    st.write(unidad["actividad"])
    respuesta_practica = st.text_area(
        "Desarrolla tu respuesta",
        key=f"practica_{seleccion}",
        height=180,
        placeholder="Desarrolla la actividad paso a paso...",
    )
    if st.button("Ver criterios de autoevaluación", key=f"criterios_{seleccion}"):
        st.markdown("**Comprueba tu respuesta:**")
        for criterio in unidad["criterios"]:
            st.markdown(f"- [ ] {criterio}")
        if respuesta_practica.strip():
            st.caption("La respuesta permanece únicamente durante esta sesión; aún no hay almacenamiento persistente.")

with tab_about:
    st.markdown("### Alcance de esta versión")
    st.write(
        "La aplicación integra contenidos pedagógicos locales y conversación generativa "
        "mediante OpenRouter cuando se proporciona una clave API válida."
    )
    st.write(
        "Todavía no integra RAG bibliográfico, búsqueda en bases científicas ni memoria "
        "persistente. Las referencias y afirmaciones específicas deben verificarse "
        "con fuentes primarias."
    )

st.divider()
st.markdown(
    "**Principio de trabajo:** comprender antes de redactar; justificar las decisiones; "
    "verificar las fuentes; mantener la validación humana."
)
st.caption(
    "La conexión con OpenRouter habilita respuestas generativas. No equivale a una "
    "conexión con bases bibliográficas ni verifica automáticamente las referencias."
)
