#!/usr/bin/env python3
"""
Script para gestionar el servidor híbrido - iniciar, parar, reiniciar
"""
import subprocess
import sys
import time
import requests
import os
import signal

def is_server_running(port=8052):
    """Verificar si el servidor está corriendo"""
    try:
        response = requests.get(f"http://127.0.0.1:{port}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def find_server_process():
    """Encontrar el proceso del servidor"""
    try:
        # En Windows usar tasklist
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if 'python.exe' in line and '8052' in line:
                parts = line.split()
                if len(parts) > 1:
                    return int(parts[1])  # PID
    except:
        pass
    return None

def stop_server():
    """Parar el servidor si está corriendo"""
    if not is_server_running():
        print("✅ Servidor no está corriendo")
        return True
    
    print("🛑 Parando servidor...")
    pid = find_server_process()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            if not is_server_running():
                print("✅ Servidor parado exitosamente")
                return True
            else:
                print("⚠️ Servidor aún corriendo, usando kill forzado")
                os.kill(pid, signal.SIGKILL)
                time.sleep(1)
                return not is_server_running()
        except:
            print("❌ Error parando servidor")
            return False
    return False

def start_server():
    """Iniciar el servidor"""
    if is_server_running():
        print("✅ Servidor ya está corriendo")
        return True
    
    print("🚀 Iniciando servidor híbrido...")
    try:
        # Iniciar servidor en background
        process = subprocess.Popen([
            sys.executable, 'hybrid_preview_server.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Esperar un momento para que inicie
        time.sleep(3)
        
        if is_server_running():
            print("✅ Servidor iniciado exitosamente en puerto 8052")
            return True
        else:
            print("❌ Error iniciando servidor")
            return False
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")
        return False

def restart_server():
    """Reiniciar el servidor"""
    print("🔄 Reiniciando servidor...")
    stop_server()
    time.sleep(1)
    return start_server()

def server_status():
    """Mostrar estado del servidor"""
    if is_server_running():
        try:
            response = requests.get("http://127.0.0.1:8052/")
            data = response.json()
            print("✅ Servidor corriendo")
            print(f"   Puerto: 8052")
            print(f"   Versión: {data['version']}")
            print(f"   Capacidades: {data['capabilities']}")
        except:
            print("⚠️ Servidor corriendo pero no responde correctamente")
    else:
        print("❌ Servidor no está corriendo")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python manage_server.py [start|stop|restart|status]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "start":
        start_server()
    elif command == "stop":
        stop_server()
    elif command == "restart":
        restart_server()
    elif command == "status":
        server_status()
    else:
        print("Comando no válido. Use: start, stop, restart, o status")
