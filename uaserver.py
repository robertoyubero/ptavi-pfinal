#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""
import socketserver
import socket
import sys
import os
import xml.etree.ElementTree as ET




def get_configuracion(fichero):
    """
    Extraigo los datos del fichero de configuracion
    """
    dicc = {}
    tree = ET.parse(fichero)
    root = tree.getroot()
    for child in root:
        clave =child.tag
        valor = child.attrib
        dicc[clave] = valor
    return dicc

#comprobamos la entrada por teclado
try:
    if len(sys.argv) != 2:
        raise IndexError
    F_CONFIG = sys.argv[1]
    DIC_CONFIG = get_configuracion(F_CONFIG)

except IndexError:
    print("Usage: python server.py IP port audio_file")


class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Clase servidor
    """
    metodos_sip = ["INVITE", "ACK", "BYE"]

    def envio_RTP(self):
        """
        Gestion del envio de paquetes RTP: envio el paquete al cliente
        """
        # envio RTP
        paquete_RTP = ('./mp32rtp -i ' + IP_DESTINO + ' -p 23032 < '
                       + FICHERO)
        print("Enviando paquete RTP...\n")
        os.system(paquete_RTP)
        return (FICHERO)

    def setcode_200(self):
        """
        Enviamos peticion aceptada
        """
        respuesta = ('SIP/2.0 100 Trying\r\n\r\nSIP/2.0 180 Ring\r\n\r\n' +
                     'SIP/2.0 200 OK\r\n\r\n')
        return respuesta

    def setcode_400(self):
        """
        La peticion NO fue aceptada por estar mal formada
        """
        respuesta = ('SIP/2.0 400 Bad Request\r\n\r\n')
        return respuesta

    def setcode_405(self):
        """
        El método de la peticion no esta permitido
        """
        respuesta = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
        return respuesta


    def handle(self):
        while 1:

            print("waiting...")
            line = self.rfile.read()
            #controlamos el mensaje que se reenvia vacio
            if not line:
                break
            # Leyendo línea a línea lo que nos envía el cliente
            line = line.decode('utf-8')
            print(line)


            """
            #extraigo: tipo_peticion, dir_SIP_cliente_ y dir_IP_cliente
            peticion_cliente = line.split(' sip:')[0]
            recorte = line.split(":")[-1]
            dir_SIP_cliente = recorte.split(" SIP/2.0")[0]
            IP_cliente = dir_SIP_cliente.split('@')[-1]

            print("Recibido: " + line.split('\r')[0] + '\n')
            respuesta = b''
            if peticion_cliente == 'INVITE':
                respuesta = self.setcode_200()
                self.wfile.write(bytes(respuesta, 'utf-8'))

            elif peticion_cliente == 'BYE':
                #le devuelvo 200OK
                respuesta = 'SIP/2.0 200 OK\r\n\r\n'
                self.wfile.write(bytes(respuesta, 'utf-8'))
                print(dir_SIP_cliente + " ha cerrado la conexion\n")

            elif peticion_cliente == 'ACK':
                #envio el paquete RTP, e imprimo que lo he enviado
                respuesta = self.envio_RTP()
                self.wfile.write(bytes(respuesta, 'utf-8'))

            else:
                #metodo no admitido
                respuesta = self.setcode_405()
                self.wfile.write(bytes(respuesta, 'utf-8'))
            """

if __name__ == "__main__":


    ip_server = DIC_CONFIG['uaserver']['ip']
    puerto_server = DIC_CONFIG['uaserver']['puerto']
    # Nos atamos a puerto de uaserver
    serv = socketserver.UDPServer((ip_server, int(puerto_server)), EchoHandler)
    print("Listening...\n")
    serv.serve_forever()
