# asr_config_saver.py

import pandas as pd
from netmiko import ConnectHandler
import argparse
from datetime import datetime
import re
import os
import netmiko
import logging
import concurrent.futures 

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s',
    handlers=[
        logging.FileHandler("asr_automation.log"), 
        logging.StreamHandler() 
    ]
)


def process_single_device(device, moment, chg_number, current_date):
    hostname = device.get('hostname')
    ip = device.get('ip')
    username = device.get('username')
    password = device.get('password')

    logging.info(f"--- Iniciando procesamiento para {hostname} ({ip}) ---")

    device_params = {
        'device_type': 'cisco_ios',
        'host': ip,
        'username': username,
        'password': password,
        'port': 22,
        'secret': password,
        'global_delay_factor': 0.5, 
    }

    net_connect = None
    try:
        net_connect = ConnectHandler(**device_params)
        logging.info(f"Conexión exitosa a {hostname} ({ip}).")

        config_filename = f"/flash/{hostname}_{current_date}_{moment}_{chg_number}.cfg"
        command_1 = f"save configuration {config_filename} -r -n"

        logging.info(f"Ejecutando: '{command_1}' en {hostname}")
        output_command_1 = net_connect.send_command_timing(command_1, delay_factor=40)
        logging.info(f"Salida de comando 1 en {hostname}:\n{output_command_1}")

        if "Configuration saved to" in output_command_1 or "Saving configuration" in output_command_1:
            logging.info(f"Configuración guardada exitosamente en {config_filename} en {hostname}.")
        else:
            logging.warning(f"Advertencia: No se pudo confirmar que la configuración se guardó en {hostname}.")
            device['config_save_warning'] = True 
        device['output_save_config'] = output_command_1

        logging.info(f"Ejecutando: 'show boot' en {hostname}")
        output_show_boot = net_connect.send_command("show boot")
        logging.info(f"Salida de 'show boot' en {hostname}:\n{output_show_boot}")

        boot_priorities = []
        matches = re.findall(r'boot system priority (\d+)', output_show_boot, re.IGNORECASE)

        if matches:
            for priority_str in matches:
                boot_priorities.append(int(priority_str))
            lowest_priority = min(boot_priorities)
            logging.info(f"El system priority más bajo encontrado en {hostname} es: {lowest_priority}")
        else:
            lowest_priority = None
            logging.warning(f"No se encontraron 'boot system priority' en la salida de 'show boot' en {hostname}.")

        device['lowest_priority'] = lowest_priority
        device['output_show_boot'] = output_show_boot

        logging.info(f"Ejecutando: 'show version' en {hostname}")
        output_show_version = net_connect.send_command("show version")
        logging.info(f"Salida de 'show version' en {hostname}:\n{output_show_version}")
        device['output_show_version'] = output_show_version

        boot_image = None
        match = re.search(r'Boot Image:\s+(.+)', output_show_version, re.IGNORECASE)
        if match:
            boot_image = match.group(1).strip()
            logging.info(f"Boot Image encontrado en {hostname}: {boot_image}")
        else:
            logging.warning(f"No se encontró 'Boot Image:' en la salida de 'show version' en {hostname}.")
        device['boot_image'] = boot_image

        if lowest_priority is not None and boot_image:
            sp = lowest_priority - 1
            boot_cmd = f'boot system priority {sp} image {boot_image} config {config_filename}'
            logging.info(f"Entrando a modo configuración y aplicando nuevo boot system en {hostname}: {boot_cmd}")
            commands = [
                'config',
                boot_cmd,
                'end'
            ]
            output_config = ""
            for cmd in commands:
                logging.info(f"Ejecutando: '{cmd}' en {hostname}")
                output = net_connect.send_command_timing(cmd, delay_factor=2)
                logging.info(f"Salida de '{cmd}' en {hostname}:\n{output}")
                output_config += f"\n{output}"

            device['boot_cmd_applied'] = boot_cmd
            device['output_boot_cmd'] = output_config

            logging.info(f"Ejecutando: 'show boot' final para verificar cambios en {hostname}...")
            output_show_boot_final = net_connect.send_command("show boot")
            logging.info(f"Salida de 'show boot' final en {hostname}:\n{output_show_boot_final}")
            device['output_show_boot_final'] = output_show_boot_final
        else:
            logging.warning(f"No se puede aplicar el nuevo boot system en {hostname}: faltan lowest_priority o boot_image.")
            device['boot_cmd_not_applied'] = True

        logging.info(f"Ejecutando: 'autoconfirm' en {hostname}")
        output_autoconfirm = net_connect.send_command_timing("autoconfirm", delay_factor=2)
        logging.info(f"Salida de 'autoconfirm' en {hostname}:\n{output_autoconfirm}")
        device['output_autoconfirm'] = output_autoconfirm

        logging.info(f"Ejecutando: 'filesystem synchronize all' en {hostname}")
        output_filesystem_sync = net_connect.send_command_timing("filesystem synchronize all", delay_factor=180)
        logging.info(f"Salida de 'filesystem synchronize all' en {hostname}:\n{output_filesystem_sync}")
        device['output_filesystem_sync'] = output_filesystem_sync

        device['error'] = False
        logging.info(f"--- Procesamiento completado para {hostname} ({ip}) ---")

    except netmiko.NetmikoTimeoutException as e:
        logging.error(f"Timeout de Netmiko al conectar o ejecutar comando en {hostname} ({ip}): {e}")
        device['error'] = True
        device['error_message'] = f"Timeout de Netmiko: {e}"
    except netmiko.NetmikoAuthenticationException as e:
        logging.error(f"Fallo de autenticación en {hostname} ({ip}): {e}")
        device['error'] = True
        device['error_message'] = f"Fallo de autenticación: {e}"
    except Exception as e:
        logging.error(f"Error inesperado al conectar o procesar {hostname} ({ip}): {e}", exc_info=True)
        device['error'] = True
        device['error_message'] = f"Error inesperado: {e}"
    finally:
        if net_connect:
            net_connect.disconnect()
            logging.info(f"Desconectado de {hostname} ({ip}).")
    return device 

def main():
    parser = argparse.ArgumentParser(description="Automatiza el guardado de configuración y actualización de boot en ASR5500.")
    parser.add_argument("moment", choices=["BEFORE", "AFTER"], help="Momento del cambio: BEFORE o AFTER")
    parser.add_argument("chg_number", type=str, help="Número del cambio (ej. CHG0001234)")
    parser.add_argument("excel_file", type=str, help="Ruta al archivo Excel con los datos de conexión")

    args = parser.parse_args()

    moment = args.moment
    chg_number = args.chg_number
    excel_file = args.excel_file

    logging.info(f"Momento del cambio: {moment}")
    logging.info(f"Número del cambio: {chg_number}")
    logging.info(f"Archivo Excel: {excel_file}\n")

    
    try:
        df = pd.read_excel(excel_file)
        devices_from_excel = df.to_dict(orient='records')
        logging.info(f"Se han cargado {len(devices_from_excel)} dispositivos del archivo Excel.")

    except FileNotFoundError:
        logging.error(f"Error: El archivo Excel '{excel_file}' no se encontró.")
        return
    except Exception as e:
        logging.error(f"Error al leer el archivo Excel: {e}", exc_info=True)
        return

    current_date = datetime.now().strftime("%Y%m%d")
    final_devices_results = [] 

    max_workers = 10
    logging.info(f"Iniciando procesamiento concurrente con {max_workers} hilos...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_device = {
            executor.submit(process_single_device, device, moment, chg_number, current_date): device
            for device in devices_from_excel
        }

        for future in concurrent.futures.as_completed(future_to_device):
            original_device = future_to_device[future] 
            hostname = original_device.get('hostname', 'Desconocido')
            ip = original_device.get('ip', 'Desconocida')

            try:
                result_device = future.result()
                final_devices_results.append(result_device)
                logging.info(f"Resultados obtenidos para {hostname} ({ip}).")
            except Exception as exc:
                
                logging.error(f'{hostname} ({ip}) generó una excepción durante el procesamiento concurrente: {exc}', exc_info=True)
                original_device['error'] = True
                original_device['error_message'] = f"Excepción en hilo principal: {exc}"
                final_devices_results.append(original_device) 

    logging.info("Todos los dispositivos han sido procesados (o intentados).")

    
    html_rows = ""
    
    for device in final_devices_results:
        hostname = device.get('hostname', 'N/A')
        ip = device.get('ip', 'N/A')
        output_show_boot_final = device.get('output_show_boot_final', 'No ejecutado o error.')
        output_filesystem_sync = device.get('output_filesystem_sync', 'No ejecutado o error.')
        error_message = device.get('error_message', '')

        status_color = "red" if device.get('error') else "black"
        status_text = "ERROR" if device.get('error') else "OK"
        if device.get('config_save_warning'):
            status_text += " (Advertencia al guardar config)"
            status_color = "orange"
        if device.get('boot_cmd_not_applied'):
            status_text += " (Boot cmd no aplicado)"
            status_color = "orange"


        html_rows += f"""
        <tr>
            <td>{hostname}</td>
            <td>{ip}</td>
            <td style="color:{status_color};"><b>{status_text}</b><br>{error_message}</td>
            <td><pre>{output_show_boot_final}</pre></td>
            <td><pre>{output_filesystem_sync}</pre></td>
        </tr>
        """
    
    resumen_cells = ""
    for device in final_devices_results:
        hostname = device.get('hostname', 'SinNombre')
        error = device.get('error', False)
        color = "#c6efce" if not error else "#ffc7ce"  
        resumen_cells += f'<td style="background-color:{color}; font-weight:bold; text-align:center;">{hostname}</td>'
    tabla_resumen = f"""
    <h2>Resumen General</h2>
    <table class="resumen-table">
        <tr>{resumen_cells}</tr>
    </table>
    <br>
    """
    
    html_content = f"""<!DOCTYPE html>      
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Reporte de Cambios ASR</title>
        <style>
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; vertical-align: top;}}
            th {{ background-color: #f2f2f2; }}
            pre {{ white-space: pre-wrap; word-break: break-all; margin: 0; }}
            /* Clase para la tabla resumen */
            .resumen-table, .resumen-table td {{
                border-width: 3px !important;
                border-style: solid;
                border-color: #333;
            }}
        </style>
    </head>
    <body>
        {tabla_resumen}
        <h2>Reporte Detallado de Cambios ASR</h2>
        <table>
            <tr>
                <th>Hostname</th>
                <th>IP</th>
                <th>Estado/Errores</th>
                <th>Show Boot Final Output</th>
                <th>Filesystem Sync Output</th>
            </tr>
            {html_rows}
        </table>
    </body>
    </html>
    """

    report_filename = f"reporte_asr_{current_date}_{chg_number}.html"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    logging.info(f"\nReporte HTML generado exitosamente: {report_filename}")
    logging.info(f"Logs detallados guardados en: asr_automation.log")


if __name__ == "__main__":
    main()