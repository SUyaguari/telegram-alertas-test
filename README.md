# Alertas de Telegram con n8n

El conector escucha mensajes nuevos de los grupos de tu cuenta personal de Telegram, incluidos los de personas y bots. Envía el texto al webhook local de n8n. Si una señal cumple las reglas, te avisa en **Mensajes guardados** con el nombre del grupo, los datos detectados y el mensaje original.

| Señal | Cuándo avisa |
| --- | --- |
| Entrada o salida de un exchange | Cuando el total transferido en USD alcanza el umbral. |
| Aumento de interés abierto (OI) | Cuando el aumento en USD de al menos un exchange alcanza el umbral. El aviso muestra los exchanges que lo alcanzaron. |
| Señal de ciclo | Cuando el mensaje trae una señal explícita y `alertarSenalSinUsd` está habilitado. El aviso incluye los cambios de precio y OI en porcentaje. |

## Requisitos

- Una PC con Windows, **Python 3.12** instalado y la carpeta `telegram-alertas` descargada o clonada.
- **n8n local** instalado en esa PC, configurado para usar el puerto `5678`.
- Una **cuenta personal de Telegram** que ya esté en los grupos que quieres escuchar.

## Primera instalación paso a paso

1. **Arranca n8n y comprueba Python.** Abre [http://localhost:5678](http://localhost:5678) en el navegador e inicia sesión en n8n. En CMD o PowerShell, ejecuta `py -3.12 --version`. Debe mostrar `Python 3.12.x`.
2. **Reúne las dos credenciales que vas a usar.**
   - En n8n, entra a **Settings → n8n API → Create an API key** y copia la clave. Si n8n te deja elegir permisos, incluye `credential:create`. [Guía de la API de n8n](https://docs.n8n.io/api/authentication/)
   - En [my.telegram.org](https://my.telegram.org), entra con tu cuenta personal, abre **API development tools** y copia el **App ID** y el **App hash**. Los usarás al iniciar el conector.
3. **Crea la credencial del webhook.** Elige **CMD (Símbolo del sistema)** o **PowerShell** y ejecuta el bloque correspondiente. Cambia `C:\ruta\telegram-alertas` por la ruta real de la carpeta. Si ya estás en ella, omite la primera línea.

   **CMD (Símbolo del sistema)**

   ```bat
   cd /d "C:\ruta\telegram-alertas"
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\Configurar webhook.ps1"
   ```

   **PowerShell**

   ```powershell
   Set-Location "C:\ruta\telegram-alertas"
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\Configurar webhook.ps1"
   ```

   Cuando se te pida **API key de n8n**, pega la clave que creaste en el paso 2. Espera a que aparezca **«Credencial creada: Telegram personal - acceso local»**. Haz este paso una vez por instalación.

4. **Importa y publica el flujo.** Crea un flujo en n8n. En el menú **⋯** del editor, elige **Import from File** e importa [Telegram personal - Alertas cripto.json](Telegram%20personal%20-%20Alertas%20cripto.json). Abre el nodo **Recibir mensaje de Telegram**, selecciona **Telegram personal - acceso local** como credencial **Header Auth** y pulsa **Publicar**.
5. **Inicia el conector.** Haz doble clic en [Iniciar Telegram.cmd](Iniciar%20Telegram.cmd). La primera vez prepara el entorno de Python e instala Telethon. Cuando se te pida **API ID de Telegram**, escribe el **App ID**. Después ingresa el **App hash**. Si Telegram pide iniciar sesión, escribe tu número con código de país, el código que recibas y tu contraseña de verificación en dos pasos si aplica. Deja abierta la ventana cuando veas **«Cuenta personal de Telegram conectada»**.
6. **Comprueba que llegan los avisos.** Con el umbral inicial de 20.000 USD, pide a alguien que envíe `$BREV 大额流入交易所$213K（30笔） · ETH` en un grupo de pruebas de Telegram al que pertenezcas. Deberías recibir en **Mensajes guardados** un aviso de entrada al exchange por **213.000 USD**. Si cambiaste el umbral, usa un ejemplo cuyo monto lo alcance.

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
