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

    def send_RTP(self, dir_SIP_dest):
        """
        Gestion del envio de paquetes RTP: envio el paquete al cliente
        """
        ip_puerto = dir_SIP_dest.split("@")[1]
        ip = dir_SIP_dest.split(":")[0]
        ip = ip.split("@")[1]
        puerto = dir_SIP_dest.split(":")[1]
        audio = DIC_CONFIG['audio']['path']

        # envio RTP
        paquete_RTP = ('./mp32rtp -i ' + ip + ' -p ' + puerto + ' < '
                       + audio)
        print("Enviando paquete RTP...\n")
        os.system(paquete_RTP)


    def send_ACK(self, dir_SIP_dest):

        ip_puerto = dir_SIP_dest.split("@")[1]
        ip = dir_SIP_dest.split(":")[0]
        ip = ip.split("@")[1]
        puerto = dir_SIP_dest.split(":")[1]

        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((ip, int(puerto)))

        ack = "ACK sip:" + dir_SIP_dest + " SIP/2.0\r\n"
        my_socket.send(bytes(ack, 'utf-8'))
        print("Enviado: " + ack)




    def handle(self):
        while 1:

            ip_proxy = DIC_CONFIG['regproxy']['ip']
            puerto_proxy = DIC_CONFIG['regproxy']['puerto']
            # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
            my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect((ip_proxy, int(puerto_proxy)))

            mensaje_rx = self.rfile.read()
            #controlamos el mensaje que se reenvia vacio
            if not mensaje_rx:
                break
            # Leyendo línea a línea lo que nos envía el cliente
            mensaje_rx = mensaje_rx.decode('utf-8')
            print("Recibido: " + mensaje_rx + "\n")
            METODO = mensaje_rx.split(" ")[0]

            if METODO == "INVITE":
                # envio 200 ok al proxy
                dir_SIP_dest = mensaje_rx.split("o=")[1]
                dir_SIP_dest = dir_SIP_dest.split("s=")[0][:-1]
                dir_SIP_o = mensaje_rx.split(" ")[1]
                dir_SIP_o = dir_SIP_o.split("sip:")[1]
                puerto_o_RTP = DIC_CONFIG['rtpaudio']['puerto']
                print(dir_SIP_dest, dir_SIP_o)

                respuesta = "SIP/2.0 100 Trying\r\n\r\n"
                respuesta += "SIP/2.0 180 Ring\r\n\r\n"
                respuesta += "SIP/2.0 200 OK\r\nContent-Type: "
                respuesta +=  "application/sdp\r\n\r\n"
                respuesta += "v=0\no=" + dir_SIP_o + "\nd=" + dir_SIP_dest
                respuesta += "\ns=myWOD\nt=0\nm=audio "
                respuesta += puerto_o_RTP + " RTP"
                my_socket.send(bytes(respuesta, 'utf-8'))
                print("Enviado: " + respuesta + "\n")

            if METODO == "BYE":
                print("Recibido BYE en uaserver")

            else:
                if "200 OK" in mensaje_rx:
                    # enviamos ACK al destinatario directamente
                    ip_puerto = mensaje_rx.split("o=")[1]
                    dir_SIP_dest = ip_puerto.split("d=")[0][:-1]
                    # envio ack
                    self.send_ACK(dir_SIP_dest)
                    # envio RTP
                    self.send



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
