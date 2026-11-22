# Alertas de Telegram en n8n

El conector de Windows escucha los mensajes nuevos recibidos en grupos de una cuenta personal de Telegram. Envía el texto al webhook local de n8n. Cuando el flujo detecta una señal, el conector envía el aviso a **Mensajes guardados** con el grupo y el mensaje original.

## Archivos

- `Telegram personal - Alertas cripto.json` reproduce la última versión publicada y verificada del flujo, en formato importable por n8n.
- `detectar.js` contiene el código del nodo **Detectar y preparar alerta**. Los cambios que se hagan a este archivo se deben aplicar también al nodo y publicar desde n8n.
- `Iniciar Telegram.cmd` inicia el conector para recibir alertas. `Revisar formatos.cmd` también toma una muestra de mensajes recientes.
- `muestras-formatos.ejemplo.json` es la copia del muestreo con identificadores genéricos para los grupos.

## Instalación en otra instancia local

1. Inicia n8n en `http://localhost:5678` y asegúrate de tener Python 3.12 en Windows.
2. Importa `Telegram personal - Alertas cripto.json` como workflow.
3. En PowerShell, desde esta carpeta, ejecuta `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\Configurar webhook.ps1"` e ingresa tu API key de n8n en el prompt. Se creará la credencial **Telegram personal - acceso local** y el archivo cifrado `webhook.dpapi` para este usuario de Windows.
4. Abre el nodo **Recibir mensaje de Telegram**, selecciona esa credencial de tipo **Header Auth** y publica el flujo.
5. Abre `Iniciar Telegram.cmd` e ingresa el App ID y el App hash de tu aplicación de Telegram, disponibles en [my.telegram.org](https://my.telegram.org). En el primer inicio se pedirá el número de la cuenta personal y su código de acceso.

Mantén abierto el conector para recibir mensajes. Su sesión de Telegram y el muestreo original se guardan en `%LOCALAPPDATA%\TelegramAlertasN8n`.

## Parámetros en n8n

En el nodo **Umbral en USD**, `umbralUsd` se aplica de forma inclusiva a transferencias de exchanges y a aumentos de interés abierto reportados por exchange. `alertarSenalSinUsd` controla las alertas de ciclo que incluyen una señal explícita y no reportan un aumento en USD. Publica el flujo para aplicar cualquier cambio.
