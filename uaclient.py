#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
import xml.etree.ElementTree as ET
import time
import hashlib


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

"""
Comprobamos entrada correcta
"""
metodos = ["REGISTER", "INVITE", "BYE"]
try:
    if len(sys.argv) > 4:
        raise IndexError
    F_CONFIG = sys.argv[1]
    # creo un diccionario con la configuracion
    DIC_CONFIG = get_configuracion(F_CONFIG)
    METODO = sys.argv[2]
    if len(sys.argv) == 4:
        OPCION = sys.argv[3]

except IndexError:
    print("Usage: python uaclient.py config method option")


class Cliente():

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


    """
    def get_peticion(self, tipo_peticion):
        if tipo_peticion in self.metodos_sip:
            return tipo_peticion
        else:
            print("Tipo de petición no aceptada")
    """

if __name__ == "__main__":

    cliente = Cliente()
    # informacion del servidor Proxy_Registrar
    ip_proxy = DIC_CONFIG['regproxy']['ip']
    puerto_proxy = DIC_CONFIG['regproxy']['puerto']

    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((ip_proxy, int(puerto_proxy)))


    # formo la peticion SIP
    user = DIC_CONFIG['account']['username']
    ip_user = DIC_CONFIG['uaserver']['ip']
    puerto_ua = DIC_CONFIG['uaserver']['puerto']
    dir_SIP = user + '@' + ip_user + ":" + puerto_ua
    passwd = DIC_CONFIG['account']['passwd']

    """------------
    >> REGISTER
    ------------"""
    if METODO == 'REGISTER':
        t_exp = 'Expires: ' + OPCION
        peticion = (METODO + ' sip:' + dir_SIP + ' SIP/2.0' + '\r\n' + t_exp)
        my_socket.send(bytes(peticion, 'utf-8'))
        # ENVIADA peticion
        print("\n")
        cliente.add_log(peticion, ip_proxy, puerto_proxy, 0, 0)

        try:
            # espero a recibir la PRIMERA respuesta del REGISTER
            respuesta = my_socket.recv(1024)
            respuesta = respuesta.decode('utf-8')
            codigo = int(respuesta.split('SIP/2.0 ')[-1][0:3])
            # RECIBIDA respuesta
            cliente.add_log(respuesta, ip_proxy, puerto_proxy, 1, 0)

            # Unauthorized
            if codigo == 401:
                # creo response y lo envio
                nonce = respuesta.split('"')[1]
                mc = hashlib.md5()
                mc.update(bytes(passwd, 'utf-8') + bytes(nonce, 'utf-8'))
                response = mc.hexdigest()
                respuesta = METODO + ' sip:' + dir_SIP + ' SIP/2.0' + '\r\n' + t_exp
                respuesta += '\r\nAuthorization: response="' + response
                respuesta += '" nonce="' + nonce + '"'
                my_socket.send(bytes(respuesta, 'utf-8'))
                # ENVIADA respuesta
                cliente.add_log(respuesta, ip_proxy, puerto_proxy, 0, 0)
            elif codigo == 400:
                # "Peticion mal formada"
                cliente.add(respuesta, 0, 0, 0, 1)
                my_socket.close()
            elif codigo == 405:
                # "Method not allowed"
                cliente.add(respuesta, 0, 0, 0, 1)
                my_socket.close()
            else:
                otros = "Codigo de respuesta no esperado: " + str(codigo)
                cliente.add(otros, 0, 0, 0, 1)
                my_socket.close()

            #espero a recibir la SEGUNDA respuesta del REGISTER
            respuesta = my_socket.recv(1024)
            respuesta = respuesta.decode('utf-8')
            codigo = int(respuesta.split('SIP/2.0 ')[-1][0:3])
            if codigo == 200:
                # RECIBIDA respuesta
                cliente.add_log(respuesta, ip_proxy, puerto_proxy, 1, 0)
                my_socket.close()
            elif codigo == 404:
                # RECIBIDA respuesta
                cliente.add_log(respuesta, ip_proxy, puerto_proxy, 1, 0)
                my_socket.close()
            else:
                otros = "Codigo de respuesta no esperado: " + str(codigo)
                cliente.add(otros, 0, 0, 0, 1)
                my_socket.close()


        except ConnectionRefusedError:
            # traza
            otros = "ERROR: No server listening at " + ip_proxy + ":"
            otros += puerto_proxy
            cliente.add_log(otros, 0, 0, 0, 1)

    elif METODO == "INVITE":
        pass
    elif METODO == "BYE":
        pass
    else:
        peticion = (METODO + ' sip:' + dir_SIP + ' SIP/2.0' + '\r\n')
        my_socket.send(bytes(peticion, 'utf-8'))
        # ENVIADA peticion con metodo desconocido
        cliente.add_log(peticion, ip_proxy, puerto_proxy, 0, 0)
        respuesta = my_socket.recv(1024)
        respuesta = respuesta.decode('utf-8')
        cliente.add_log(respuesta, 0, 0, 0, 1)
        my_socket.close()


    # Cerramos todo
    my_socket.close()


"""
    elif METODO == "INVITE":
        #envio INVITE
        peticion = (peticion + ' sip:' + dir_SIP + ' SIP/2.0' + '\r\n')
        my_socket.send(bytes(peticion, 'utf-8'))
        print("\nEnviado: " + peticion)

        #espero a recibir la aceptacion del INVITE
        respuesta = my_socket.recv(1024)
        respuesta = respuesta.decode('utf-8')
        codigo = int(respuesta.split('SIP/2.0 ')[-1][0:3])

        if codigo != 200:
            #mi peticion ha sido denegada
            print(respuesta)
            # Cerramos conexion
            my_socket.close()
        else:
            print('Recibido:')
            print(respuesta)
            #envio ACK para comenzar a recibir RTP
            peticion_ACK = ('ACK sip:' + dir_SIP + ' SIP/2.0' + '\r\n')
            my_socket.send(bytes(peticion_ACK, 'utf-8'))
            print('Enviado: ' + peticion_ACK)
        my_socket.close()

    elif METODO == "BYE":
        #envio BYE
        peticion_BYE = (peticion + ' sip:' + dir_SIP + ' SIP/2.0' + '\r\n')
        my_socket.send(bytes(peticion_BYE, 'utf-8'))
        print('Enviado: ' + peticion_BYE)
        #espero la respuesta...
        respuesta = my_socket.recv(1024)
        print("Recibido: " + respuesta.decode('utf-8'))
        print("Cerramos la sesion SIP\n")
        my_socket.close()
    else:
        print('Intento de envio de: ' + peticion)
        my_socket.close()


"""
