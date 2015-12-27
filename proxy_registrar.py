#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import sys
import time
import xml.etree.ElementTree as ET
import random



def get_configuracion(fichero):
    """
    Extraigo los datos del fichero de configuracion
    """
    dicc = {}
    tree = ET.parse(F_CONFIG)
    root = tree.getroot()
    for child in root:
        clave =child.tag
        valor = child.attrib
        dicc[clave] = valor
    return dicc

try:
    if len(sys.argv) != 2:
        raise IndexError
    F_CONFIG = sys.argv[1]
    DIC_CONFIG = get_configuracion(F_CONFIG)

except IndexError:
    print("Usage: python proxy_registrar.py config")


class Proxy_Server():
    """
    Clase del Servidor Proxy
    """

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


    def add_user(self, dir, t_exp):
        path = DIC_CONFIG['database']['path']
        hora = str(time.strftime("%Y%m%d%H%M%S", time.gmtime()))
        fich = open(path, "a")
        info_user = dir + " - " + hora + " - " + t_exp
        fich.write(info_user + "\n")
        print("***usuario guardado en database")


class UDP_Server(socketserver.DatagramRequestHandler):
    """
    Clase del Servidor UDP
    """

    def handle(self):
        proxy = Proxy_Server()

        while 1:

            line = self.rfile.read()
            if not line:
                break
            mensaje_rx = line.decode('utf-8')
            tipo_mensaje = mensaje_rx.split(' ')[0]
            # extraido info del cliente que me envia los mensajes
            corte = mensaje_rx.split(":")[1]
            ip_c = corte.split("@")[1]
            corte = mensaje_rx.split(":")[2]
            puerto_c = corte.split(" ")[0]
            dir_SIP_c = mensaje_rx.split(":")[1] + ":" + puerto_c

            if tipo_mensaje == "REGISTER":
                # RECIBIDO register
                proxy.add_log(mensaje_rx, ip_c, puerto_c, 1, 0)

                if not "response" in mensaje_rx:
                    # solicitamos el response para autenticar
                    respuesta = "SIP/2.0 401 Unauthorized \r\nWWW Authenticate: "
                    nonce = str(random.randint(0, 100000000000000))
                    respuesta += 'nonce="' + nonce + '"'
                    self.wfile.write(bytes(respuesta, 'utf-8'))
                    # enviada respuesta
                    proxy.add_log(respuesta, ip_c, puerto_c, 0, 0)
                else:
                    # hemos recibido el response, comprobamos autenticidad
                    print("* Debemos comprobar autenticidad del cliente\n")
                    # *** de momento suponemos que se acepta al cliente!

                    # proxy.find_client(pasw, nonce, response)
                    find = True
                    if find == True:
                        # usuario aceptado
                        respuesta = "SIP/2.0 200 OK\r\n"
                        respuesta += "Content-Type: application/sdp"
                        #guardamos al ususario en database
                        t_exp = mensaje_rx.split("Expires: ")[1]
                        t_exp = t_exp.split("\r")[0]
                        proxy.add_user(dir_SIP_c, t_exp)
                    else:
                        # usuario NO aceptado
                        respuesta = "SIP/2.0 404 User Not Found\r\n\r\n"
                    # ENVIAMOS respuesta tras comprobar la autenticidad del usuario
                    proxy.add_log(respuesta, ip_c, puerto_c, 0, 0)
                    self.wfile.write(bytes(respuesta, 'utf-8'))


            elif tipo_mensaje == "INVITE":
                # traza
                print("Recibido " + mensaje_rx)

            elif tipo_mensaje == "BYE":
                # traza
                print("Recibido " + mensaje_rx)
            else:
                respuesta = "SIP/2.0 405 Method Not Allowed\r\n\r\n"
                self.wfile.write(bytes(respuesta, 'utf-8'))
                # ENVIO mensaje
                proxy.add_log(respuesta, ip_c, puerto_c, 0, 0)






if __name__ == "__main__":
    # Creamos servidor de eco y escuchamos
    ip_server = DIC_CONFIG['server']['ip']
    puerto_server = DIC_CONFIG['server']['puerto']
    server_name = DIC_CONFIG['server']['name']
    serv_proxy = Proxy_Server()

    serv = socketserver.UDPServer((ip_server, int(puerto_server)), UDP_Server)
    otros = "Server " + server_name + " listening at port " + str(puerto_server)
    otros += "..."
    serv_proxy.add_log(otros, 0, 0, 0, 1)

    serv.serve_forever()
