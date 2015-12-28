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
import hashlib
import socket


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


    def check_client(self, dir_SIP, nonce, response_rx):
        """
        Calculamos response_proxy y lo comparamos con response_rx
        """
        # vamos al fichero de passwords y obtenemos el passwd asociado a
        # la dir_SIP que queremos comprobar
        path = DIC_CONFIG['database']['passwdpath']
        fich = open(path, 'r')
        lineas = fich.readlines()
        encontrado = False
        # buscamos al usuario en fichero passwords
        for linea in lineas:
            if dir_SIP in linea:
                password = linea.split("passwd: ")[1][:-1]
                encontrado = True

        if encontrado == True:
            #calculamos response
            m = hashlib.md5()
            m.update(bytes(password, 'utf-8') + bytes(nonce, 'utf-8'))
            response_proxy = m.hexdigest()

            if response_proxy == response_rx:
                # cliente admitido
                admitido = True
                print("* Usuario autenticado: " + dir_SIP + "\n")
            else:
                admitido = False
        else:
            admitido = False
        return admitido


    def send_to_uaserver(self, mensaje, ip_uaserver, puerto_uaserver):

        # Creamos el socket, y lo atamos a un servidor/puerto del uaserver_dest
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((ip_uaserver, int(puerto_uaserver)))

        # enviamos el mensaje al ua_server_destino
        my_socket.send(bytes(mensaje, 'utf-8'))

    #def send_to_uaclient(self, mensaje, ip_uaclient, puerto_uaclient)


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
            """
            REGISTER
            """
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
                    nonce = mensaje_rx.split('"')[3]
                    response_rx = mensaje_rx.split('"')[1]
                    find = proxy.check_client(dir_SIP_c, nonce, response_rx)

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
                # RECIBIDO INVITE
                # extraigo dir_SIP_destino
                dir_SIP_dest = mensaje_rx.split(" ")[1]
                ip_dest = dir_SIP_dest.split("@")[1]
                ip_dest = ip_dest.split(":")[0]
                puerto_dest = dir_SIP_dest.split(":")[2]
                # extraigo ip y puerto origen del INVITE
                corte = mensaje_rx.split("o=")[1]
                corte = corte.split("s")[0]
                ip_puerto = corte.split("@")[1]
                ip_o = ip_puerto.split(":")[0]
                puerto_o = ip_puerto.split(":")[1][:-1]
                proxy.add_log(mensaje_rx, ip_o, puerto_o, 1, 0)
                # debo enviar al uaserver deseado
                mensaje_tx = mensaje_rx
                proxy.send_to_uaserver(mensaje_tx, ip_dest, puerto_dest)
                proxy.add_log(mensaje_tx, ip_dest, puerto_dest, 0, 0)

                # espero a recibir confirmacion del INVITE



            elif tipo_mensaje == "BYE":
                # extraigo dir_SIP_dest
                dir_SIP_dest = mensaje_rx.split(":")[1]
                ip_dest = dir_SIP_dest.split("@")[1]
                puerto_dest = mensaje_rx.split(":")[2]
                puerto_dest = puerto_dest.split(" ")[0]
                # extraigo ip y puerto origen del INVITE
                corte = mensaje_rx.split("o=")[1]
                corte = corte.split("s")[0]
                ip_puerto = corte.split("@")[1]
                ip_o = ip_puerto.split(":")[0]
                puerto_o = ip_puerto.split(":")[1]
                proxy.add_log(mensaje_rx, ip_o, puerto_o, 1, 0)
                # debo enviar al uaserver deseado
                mensaje_tx = mensaje_rx
                proxy.send_to_uaserver(mensaje_tx, ip_dest, puerto_dest)
                proxy.add_log(mensaje_tx, ip_dest, puerto_dest, 0, 0)


            else:

                if "200 OK" in mensaje_rx:

                    print("*Recibido 200 OK")
                    # recibida confirmacion del destinatario del INVITE
                    proxy.add_log(mensaje_rx, 0, 0, 0, 1)
                    # extraigo info del nuevo destinatario
                    dir_SIP_dest = mensaje_rx.split("d=")[1]
                    dir_SIP_dest = dir_SIP_dest.split("s=")[0][:-1]
                    ip_puerto = dir_SIP_dest.split("@")[1]
                    ip_dest = ip_puerto.split(":")[0]
                    puerto_dest = ip_puerto.split(":")[1]

                    # reenvio en 200 OK al uaclient que envió el INVITE
                    proxy.send_to_uaserver(mensaje_rx, ip_dest, puerto_dest)
                    #self.wfile.write(bytes(mensaje_rx, 'utf-8'))
                    proxy.add_log(mensaje_rx, ip_dest, puerto_dest, 0, 0)

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
