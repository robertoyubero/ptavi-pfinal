# !/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""
import socketserver
import socket
import sys
import os
import xml.etree.ElementTree as ET
import time


def get_configuracion(fichero):
    """
    Extraigo los datos del fichero de configuracion
    """
    dicc = {}
    tree = ET.parse(fichero)
    root = tree.getroot()
    for child in root:
        clave = child.tag
        valor = child.attrib
        dicc[clave] = valor
    return dicc

# comprobamos la entrada por teclado
DIR_DEST_RTP = ""
PUERTO_DEST_RTP = ""
try:
    if len(sys.argv) != 2:
        raise IndexError
    F_CONFIG = sys.argv[1]
    DIC_CONFIG = get_configuracion(F_CONFIG)

except IndexError:
    print("Usage: python server.py IP port audio_file")


class UA_Server():

    def add_log(self, contenido, ip, puerto, bool_recibido, bool_otros):

        path = DIC_CONFIG['log']['path']
        if bool_recibido == 1:
            tipo_log = "Received from " + ip + ":" + puerto + " "
            print("-----" + tipo_log + "\n" + contenido + "\n")
        elif bool_recibido == 0 and bool_otros == 0:
            tipo_log = "Send to " + ip + ":" + puerto + " "
            print("-----" + tipo_log + "\n" + contenido + "\n")
        elif bool_otros == 1:
            tipo_log = ""
            print("-----" + contenido + "\n")
        else:
            print("Argumentos recibidos por add_log mal puestos")

        tipo_log += contenido
        hora = str(time.strftime("%Y%m%d%H%M%S", time.gmtime()))
        log_contenido = tipo_log.split('\r\n')
        ' '.join(log_contenido)
        fich = open(path, "a")
        fich.write(hora + ' ' + log_contenido[0] + "\n")

    def send_RTP(self, dir_SIP_dest, p_RTP_dest):
        """
        Gestion del envio de paquetes RTP: envio el paquete al cliente
        """
        ip = dir_SIP_dest
        audio = DIC_CONFIG['audio']['path']
        audio = audio.split("/")[-1]

        mensaje_rtp = "Enviando paquete RTP a " + ip + " " + p_RTP_dest + "\n"
        self.add_log(mensaje_rtp, 0, 0, 0, 1)
        # envio RTP
        paquete_RTP = ('./mp32rtp -i ' + ip + ' -p ' + p_RTP_dest + ' < '
                       + audio)
        os.system(paquete_RTP)


class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Clase servidor
    """
    def handle(self):

        ip_proxy = DIC_CONFIG['regproxy']['ip']
        puerto_proxy = DIC_CONFIG['regproxy']['puerto']
        my_ip = DIC_CONFIG['uaserver']['ip']
        my_puerto = DIC_CONFIG['uaserver']['puerto']
        my_name = DIC_CONFIG['account']['username']
        my_dir_SIP = my_name + "@" + my_ip + ":" + my_puerto
        server = UA_Server()
        global PUERTO_DEST_RTP

        while 1:
            line = self.rfile.read()
            # controlamos el mensaje que se reenvia vacio
            if not line:
                break

            mensaje_rx = line.decode('utf-8')
            METODO = mensaje_rx.split(" ")[0]

            if METODO == "INVITE":
                # extraigo el puerto RTP para el envio
                puerto_dest = mensaje_rx.split("m=")[1]
                PUERTO_DEST_RTP = puerto_dest.split(" ")[1]
                server.add_log(mensaje_rx, ip_proxy, puerto_proxy, 1, 0)
                # envio 200 ok al proxy
                dir_SIP_o = mensaje_rx.split(" ")[1]
                dir_SIP_o = dir_SIP_o.split("sip:")[1]
                puerto_o_RTP = DIC_CONFIG['rtpaudio']['puerto']

                respuesta = "SIP/2.0 100 Trying\r\n\r\n"
                respuesta += "SIP/2.0 180 Ring\r\n\r\n"
                respuesta += "SIP/2.0 200 OK\r\nContent-Type: "
                respuesta += "application/sdp\r\n\r\n"
                respuesta += "v=0\no=" + dir_SIP_o
                respuesta += "\ns=myWOD\nt=0\nm=audio "
                respuesta += puerto_o_RTP + " RTP"
                # self.send_to_proxy(respuesta)
                self.wfile.write(bytes(respuesta, 'utf-8'))
                server.add_log(respuesta, ip_proxy, puerto_proxy, 0, 0)

            elif METODO == "BYE":
                print("Recibido: " + mensaje_rx + "\n")
                puerto_o_RTP = DIC_CONFIG['rtpaudio']['puerto']

                # debo enviar el 200 OK
                respuesta = "SIP/2.0 200 OK\r\nContent-Type: "
                respuesta += "application/sdp\r\n\r\n"
                respuesta += "o=" + my_dir_SIP + "\r\n"

                # envio el 200 OK
                self.wfile.write(bytes(respuesta, 'utf-8'))
                server.add_log(respuesta, ip_proxy, puerto_proxy, 0, 0)

                fin = "Connection Finished"
                server.add_log(fin, 0, 0, 0, 1)

            elif METODO == "ACK":
                dir_sip_dest = mensaje_rx.split(":")[1]
                server.add_log(mensaje_rx, ip_proxy, puerto_proxy, 1, 0)
                mensaje_rtp = "Sending RTP to " + dir_sip_dest + ":"
                mensaje_rtp += PUERTO_DEST_RTP
                server.send_RTP(dir_sip_dest, PUERTO_DEST_RTP)

            else:
                print("Recibido mensaje no esperado: " + mensaje_rx)


if __name__ == "__main__":

    uaserver = UA_Server()
    ip_server = DIC_CONFIG['uaserver']['ip']
    puerto_server = DIC_CONFIG['uaserver']['puerto']
    # Nos atamos a puerto de uaserver
    serv = socketserver.UDPServer((ip_server, int(puerto_server)), EchoHandler)
    otros = "Listening..."
    uaserver.add_log(otros, 0, 0, 0, 1)
    print("\n")
    serv.serve_forever()
