
import os
from os import path
import logging
import threading
import serial
import time
import requests
import json

import threading
import random

class Gateway(object):
    """  Grab data from serial port, join it in packet and send it to the internet """
    ## sending parameters
    last_sent_time = 0
    send_interval = 10.0
    SENDING = False
    ## initial data for registering nodes
    INIT_REGISTERS = 10
    AS_ARRAY = False
    commands = {}
    array_idx = 0
    #server_url = "http://ggizitim.enjambre.com.bo/storage/"
    #server_url = "http://a4f8d1a8.ngrok.io/storage/"
    server_url = ""
    nodes = ['default']
    request_header = {'Content-Type': 'application/json'}
    num_nodes = 0
    data_buffer = []
    def __init__(self, port='/dev/ttyACM0', baud=57600, server_url="http://2af64eb1.ngrok.io/storage/"):
        self.server_url = server_url
        logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-10s) %(message)s',)
        self.ser = self.connect(port=port)
        if self.ser == None:
            print "conexion fallida!"
        else:
            print "conectado!"
            
    def connect(self, port="/dev/ttyACM0", baud=57600):       
        try:
            ser = serial.Serial(port, baudrate=baud, timeout=1)
        except:
            return None
        finally:
            return ser
    
    def send_command(command):
        pass

    def register_nodes(self):
        i = 0
        while i < self.INIT_REGISTERS:
            #node = {}
            if self.ser.inWaiting() > 0:
                bytesToRead = self.ser.inWaiting()
                out = ""
                try:  
                    out = self.ser.readline().strip('\n')
                    out = out.strip('\r')
                    print out
                    data = out.split(' ')
                    for id in self.nodes:
                        if not (data[1] in self.nodes) and data[0] == 'node':
                            self.nodes.append(data[1])                    
                    i += 1

                except:
                    pass
        
        self.nodes.remove('default')
        print ('nodos encontrados: ', len(self.nodes), ' ids: ', self.nodes) 
        self.num_nodes = len(self.nodes)

        url = self.server_url + 'nodes'
        data = {}
        for node in self.nodes:
            data['name'] = 'test' + node
            data['area'] = 'test' if float(node) > 99 else 'real'
            data['nodeID'] = float(node)
            data['sensors'] = ['temp', 'lux', 'gas']
            r = requests.post(url, headers=self.request_header, json=data)
            if r.status_code == requests.codes.ok:
                logging.debug('registrado nodo ' + str(node))
            else:
                logging.debug('error al registrar nodo ' + str(node))

    def send_data(self):
        nodes_sent = 0
        
        while True:
            if time.time() - self.last_sent_time > self.send_interval:
                self.last_sent_time = time.time()
                self.SENDING = True
                logging.debug('Start sending data...')
                success = 0
                if self.AS_ARRAY:
                    url = self.server_url + 'array/sensordata'
                    data_dict = {'dataArray':self.data_buffer, 'idx':self.array_idx}
                    r = requests.post(url,headers=self.request_header, json=data_dict)
                    if r.status_code == requests.codes.ok:
                        logging.debug("enviado array de datos nro: " + str(self.array_idx))
                        self.array_idx += 1

                else:
                    url = self.server_url + 'sensordata'    
                    for data in self.data_buffer:
                        r = requests.post(url, headers=self.request_header, json=data)
                        if r.status_code == requests.codes.ok:
                            success += 1
                    logging.debug("registros exitosos: " + str(success) + "/" + str(len(self.data_buffer)))

                ## flush buffer
                self.data_buffer = []
                self.SENDING = False        
    
    def run(self, serial=False, online=False, as_array=False):
        """ listen and send a command to serial port for controlling 
            the robot. The commands have the following format:
                <command> <parameter1> <parameter2>
            Serial port parameters:
                - baudrate: 57600
        """
        ## create thread
        self.AS_ARRAY = as_array
        if online:
            send_th = threading.Timer(10, self.send_data)
            send_th.setDaemon(True)
            send_th.start()

        while True:
            
            if self.ser.inWaiting() > 0:
                bytesToRead = self.ser.inWaiting()
                out = ""
                #try:  
                out = self.ser.readline().strip('\n')
                out = out.strip('\r')
                #logging.debug(out)
                data = out.split(' ')
                if data[0] == 'node':
                    data_dic = {'nodeID':float(data[1]), 'dataIdx':float(data[3]), 'temp':float(data[5]), 'gas':float(data[7]), 'lux':float(data[9])}
                    if data[1] == '51':
                        logging.debug(data_dic)
                    if not self.SENDING:
                        self.data_buffer.append(data_dic)
                #except:
                #    logging.debug("failed")
                                         
    def close(self):
        self.ser.close()

if __name__ == '__main__':
    import argparse
    import time
    parser = argparse.ArgumentParser(description='gateway red de sensores.')
    parser.add_argument('-rpi', action='store_true',help='for raspberry pi hardware')
    parser.add_argument('-online', action='store_true',help='send request to server, default is false')
    parser.add_argument('-server', action='store', type=str, help='url to server')
    parser.add_argument('-asarray', action='store_true',help='send data as array')
    
    args = parser.parse_args()
    server = args.server
    if args.server:
        g = Gateway(server_url=server)
    else:
        g = Gateway()
    g.register_nodes()
    time.sleep(1)
    
    g.run(online=args.online, as_array=args.asarray)
