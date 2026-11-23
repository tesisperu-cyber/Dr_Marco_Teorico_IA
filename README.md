# Dr. Marco Teórico v1.1

**CREACIONES PYBOT**  
Asistente pedagógico para comprender y desarrollar los fundamentos científicos, filosóficos y metodológicos de la investigación.

## 1. Qué incorpora esta versión

- Interfaz web desarrollada con Streamlit.
- Unidades introductorias de aprendizaje con contenidos pedagógicos locales.
- Conversación con Dr. Marco Teórico mediante OpenRouter.
- Campo de entrada para la clave API.
- Consulta dinámica del catálogo público de OpenRouter.
- Filtro de modelos con precio de entrada y salida igual a cero y compatibilidad de texto.
- Selector para cambiar el modelo durante la sesión.
- Reintento automático con otros modelos gratuitos detectados si falla el seleccionado.
- El contexto de la unidad elegida se incorpora a las instrucciones de la conversación.

## 2. Qué no incorpora todavía

- No integra RAG bibliográfico ni búsqueda en bases científicas.
- No verifica automáticamente DOI, citas ni referencias.
- No tiene memoria persistente entre sesiones.
- La clave introducida en el panel se utiliza durante la sesión; no se escribe en el repositorio.

La disponibilidad, límites y condiciones de los modelos gratuitos dependen de OpenRouter y pueden cambiar. Un precio cero en el catálogo no garantiza disponibilidad permanente ni calidad de las respuestas.

## 3. Requisitos

- Python 3.10 o superior.
- pip.
- Conexión a Internet.
- Una clave API de OpenRouter para activar la conversación generativa.

## 4. Instalación en Windows

Abre una terminal en la carpeta del proyecto y ejecuta:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Si PowerShell impide activar el entorno:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

La aplicación se abrirá normalmente en `http://localhost:8501`.

## 5. Configurar OpenRouter

1. Entra en https://openrouter.ai/ y crea o utiliza tu cuenta.
2. Crea una clave API desde https://openrouter.ai/keys.
3. Abre Dr. Marco Teórico.
4. En el panel lateral, pega la clave en **Clave API de OpenRouter**.
5. Se consultará el catálogo y aparecerá el selector de modelos gratuitos de texto.
6. Para volver a consultar el catálogo, pulsa **Actualizar catálogo gratuito**.

La clave se introduce como campo protegido y no se guarda en archivos del proyecto. No la publiques en GitHub, notebooks ni capturas de pantalla.

### Streamlit Community Cloud

También puedes guardar la clave en `Settings → Secrets`:

```toml
OPENROUTER_API_KEY = "tu_clave"
```

La aplicación lee ese secreto al iniciar la sesión. No subas el archivo de secretos al repositorio.

## 6. Estructura

```text
Dr_Marco_Teorico_v1_GitHub/
├── README.md
├── app.py
├── config.py
├── requirements.txt
├── .gitignore
├── prompts/
│   └── system_prompt.txt
└── modules/
    └── contenidos.py
```

## 7. Principios de rigor

- No inventar autores, obras, citas, DOI ni referencias.
- Diferenciar hechos, interpretaciones, hipótesis y controversias.
- No elegir automáticamente un paradigma por el solo hecho de que el estudio sea cuantitativo, cualitativo o mixto.
- Explicar las razones de las decisiones metodológicas.
- Reconocer límites y solicitar validación humana.
- Distinguir entre detectar un problema, proponer una corrección y ejecutar una corrección.

## 8. Próximas etapas posibles

La integración de recuperación bibliográfica (RAG), conectores a fuentes científicas, memoria y evaluación automatizada se desarrollará en etapas posteriores. Cada capacidad deberá probarse y documentarse antes de presentarse como disponible.

## 9. Licencia

Proyecto en desarrollo. Añade una licencia antes de distribuirlo públicamente si deseas establecer condiciones formales de reutilización.
