
import os
from os import path
import logging
import threading
import serial
import time
import requests
import json

import threading

class Gateway(object):
    """  Grab data from serial port, join it in packet and send it to the internet """
    ## sending parameters
    last_sent_time = 0
    send_interval = 10.0
    SENDING = False
    ## initial data for registering nodes
    INIT_REGISTERS = 10

    commands = {}
    #server_url = "http://ggizitim.enjambre.com.bo/storage/"
    server_url = "http://a4f8d1a8.ngrok.io/storage/"
    nodes = ['default']
    request_header = {'Content-Type': 'application/json'}
    num_nodes = 0
    data_buffer = []
    def __init__(self, port='/dev/ttyACM0', baud=57600):
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
            data['name'] = 'test'+node
            data['area'] = 'test_area'
            r = requests.post(url, headers=self.request_header, json=data)
    
    def send_data(self):
        nodes_sent = 0
        url = self.server_url + 'data'
        while True:
            if time.time() - self.last_sent_time > self.send_interval:
                self.last_sent_time = time.time()
                self.SENDING = True
                logging.debug('Start sending data...')
                success = 0
                
                #r = requests.post(url,headers=self.request_header, json=data)
                #if r.status_code == requests.codes.ok:
                #    print "datos enviados correctamente"
                
                for data in self.data_buffer:
                    r = requests.post(url, headers=self.request_header, json=data)
                    if r.status_code == requests.codes.ok:
                        success += 1
                logging.debug("registros exitosos: " + str(success) + "/" + str(len(self.data_buffer)))

                ## flush buffer
                self.data_buffer = []
                self.SENDING = False        
    
    def run(self, serial=False):
        """ listen and send a command to serial port for controlling 
            the robot. The commands have the following format:
                <command> <parameter1> <parameter2>
            Serial port parameters:
                - baudrate: 57600
        """
        ## create thread
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
                logging.debug(out)
                data = out.split(' ')
                if data[0] == 'node':
                    data_dic = {'node':float(data[1]), 'idx':float(data[3]), 'temp':float(data[5]), 'lux':float(data[7]), 'gas':0.0}
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
    parser = argparse.ArgumentParser(description='Escucha y reconoce en aymara.')
    parser.add_argument('-rpi', action='store_true',help='for raspberry pi hardware')
    parser.add_argument('-c', action='store_true',help='continuous recognition')

    args = parser.parse_args()
    g = Gateway()
    g.register_nodes()
    time.sleep(1)
    g.run()
