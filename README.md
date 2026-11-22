# Alertas de Telegram con n8n

El conector escucha mensajes nuevos de los grupos de tu cuenta personal de Telegram, incluidos los de personas y bots. Envía el texto al webhook local de n8n. Si una señal cumple las reglas, te avisa en **Mensajes guardados** con el nombre del grupo, los datos detectados y el mensaje original.

| Señal | Cuándo avisa |
| --- | --- |
| Entrada o salida de un exchange | Cuando el total transferido en USD alcanza el umbral. |
| Aumento de interés abierto (OI) | Cuando el aumento en USD de al menos un exchange alcanza el umbral. El aviso muestra los exchanges que lo alcanzaron. |
| Señal de ciclo | Cuando el mensaje trae una señal explícita y `alertarSenalSinUsd` está habilitado. El aviso incluye los cambios de precio y OI en porcentaje. |

## Requisitos

- Windows con PowerShell y Python 3.12 disponible mediante `py -3.12`. El lanzador crea el entorno de Python e instala Telethon la primera vez.
- n8n en ejecución en `http://localhost:5678` y una API key de n8n para configurar el webhook.
- Una cuenta personal de Telegram y el **App ID** y **App hash** de su aplicación, disponibles en [my.telegram.org](https://my.telegram.org) en **API development tools**.

## Primera instalación

1. En el editor de n8n, importa [el JSON del flujo](Telegram%20personal%20-%20Alertas%20cripto.json).
2. Abre PowerShell en esta carpeta y ejecuta el siguiente comando. Ingresa la API key de n8n cuando se te pida. El script crea la credencial **Telegram personal - acceso local** y guarda el secreto del webhook cifrado para tu usuario de Windows.

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\Configurar webhook.ps1"
   ```

3. En n8n, abre **Recibir mensaje de Telegram**, selecciona la credencial de tipo **Header Auth** que acabas de crear y pulsa **Publicar**.
4. Abre [Iniciar Telegram.cmd](Iniciar%20Telegram.cmd). Ingresa el App ID y el App hash. En el primer inicio, escribe también tu número con código de país, el código que te envíe Telegram y tu contraseña de verificación en dos pasos si aplica.

## Uso diario

- Cuando aparezca **«Cuenta personal de Telegram conectada»**, el conector está escuchando. Mantén abiertos el CMD y n8n para recibir avisos. Al cerrar el CMD se detiene la escucha.
- Para cambiar el umbral, edita `umbralUsd` en el nodo **Umbral en USD** y pulsa **Publicar**. El JSON incluye `20000`, por lo que un movimiento de exactamente 20.000 USD cumple. En el mismo nodo puedes activar o desactivar `alertarSenalSinUsd`. Puedes publicar estos cambios con el conector abierto.
- Para revisar formatos, cierra el CMD actual y abre [Revisar formatos.cmd](Revisar%20formatos.cmd). Mientras escucha mensajes nuevos, el conector revisa hasta 60 mensajes de los últimos 14 días por grupo. **«Muestra lista»** indica que terminó y guardó `muestras-formatos.json` en `%LOCALAPPDATA%\TelegramAlertasN8n`. **«Muestra parcial»** indica que guardó lo que alcanzó a revisar.

## Archivos

| Archivo | Para qué sirve |
| --- | --- |
| `Telegram personal - Alertas cripto.json` | Copia importable del flujo de n8n con el webhook, los parámetros y el filtro. |
| `detectar.js` | Código del nodo que reconoce los tres formatos, comprueba las reglas y arma el aviso. Si lo editas, aplica el cambio también al nodo de n8n, publica y sincroniza el JSON del repositorio. |
| `escuchar.py` | Inicia sesión en Telegram, recibe mensajes de grupos, consulta el webhook y envía los avisos. |
| `Iniciar Telegram.cmd` | Abre el conector en modo de escucha. |
| `Iniciar Telegram.ps1` | Prepara el entorno de Python, lee el secreto local y ejecuta el conector. |
| `Configurar webhook.ps1` | Crea la credencial en n8n y el archivo local cifrado `webhook.dpapi`. |
| `Revisar formatos.cmd` | Abre el conector con el muestreo habilitado. |
| `revisar_formatos.py` | Busca posibles formatos, agrupa ejemplos repetidos y guarda el informe local. |
| `muestras-formatos.ejemplo.json` | Copia del muestreo con nombres de grupo genéricos. |
| `.gitignore` | Excluye de Git la sesión, el secreto del webhook y el muestreo con los nombres originales. |
| `README.md` | Guía de instalación, uso y archivos del proyecto. |
