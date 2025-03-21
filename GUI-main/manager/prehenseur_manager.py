import asyncio
from bleak import discover 
from bleak import BleakClient
from bleak import BleakScanner
import time
import threading
import os, sys
import struct

ACTIVATE_ELECTRO_MAGNET = 3  
DEACTIVATE_ELECTRO_MAGNET = 4 

#Classe d'exemple pour communiquer avec un dispositif BLE        
class PrehenseurManager:

    def __init__(self, p_name):
        self._devices = []
        self._packets_to_send = []
        self._m_client = 0
        self._m_BLE_Thread = 0
        self._tx_charac = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'
        self._rx_charac = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'
        self._connected = False
        self._request_deconnection = False
        self.device_name = p_name
        self.data_callback = lambda data: None
        self.log_callback = lambda data: None
        self.started = False
        self.prehenseur_data = {"x": 0, "y": 0, "z": 0, "v_x": 0, "v_y": 0, "v_z": 0, "angle": 0, "charge_balance": 0, "etat_stm": 0, "destination": (0, 0),
                             "gyro_x": 0, "gyro_y": 0, "gyro_z": 0, "accel_x": 0, "accel_y": 0, "accel_z": 0, "courant": 0, "tension": 0, "puissance": 0}
    
    def __del__(self):
        self.disconnect()

#----------Public methods----------

    def startBLE_Thread(self):
        if self._m_BLE_Thread == 0:
            self._m_BLE_Thread = threading.Thread(target=self.__connect_to_BLEbetween_callback)
            self._m_BLE_Thread.start()
        elif not self._m_BLE_Thread.is_alive():
            self._m_BLE_Thread = threading.Thread(target=self.__connect_to_BLEbetween_callback)
            self._m_BLE_Thread.start()

    def disconnect(self):
        if self._connected:
            self._request_deconnection = True
            self._m_BLE_Thread.join()
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.__disconnected_callback())
            self._request_deconnection = False
    
    def activateElectroMagnet(self):
        data_to_send = [ACTIVATE_ELECTRO_MAGNET]
        self.__sendDataPacket(data_to_send)
    

    def deactivateElectroMagnet(self):
        data_to_send = [DEACTIVATE_ELECTRO_MAGNET]
        self.__sendDataPacket(data_to_send)   

    def get_data(self):
        """  Retourne les données actuelles du préhenseur """
        return self.prehenseur_data 

    
#----------End public methods----------

#----------Private methods----------

    #Fonction pour envoyer un paquet de données via BLE. Une transmission maximale contient 227 bytes.
    def __sendDataPacket(self, p_data):
        self._packets_to_send.append(bytes(p_data))

    #Fonction qui stocke tous les dispositifs BLE détectés. Ne pas modifier.
    async def __scan(self):
        self._devices = []
        dev = await BleakScanner.discover()
        for i in range(0,len(dev)):
            self._devices.append(dev[i])

    #Cette fonction est appellée lorsque des données sont reçus par BLE. "p_data" est un bytearray.
   
    def __callback(self, sender, p_data):
        """ Fonction exécutée lorsqu'on reçoit des données du préhenseur. """
        try:
            if len(p_data) == 12:  # 3 floats de 4 octets = 12 octets
                courant, tension, proximite = struct.unpack('fff', p_data)
                self.prehenseur_data = {
                "x": self.prehenseur_data.get("x", 0),
                "y": self.prehenseur_data.get("y", 0),
                "z": self.prehenseur_data.get("z", 0),
                "v_x": self.prehenseur_data.get("v_x", 0),
                "v_y": self.prehenseur_data.get("v_y", 0),
                "v_z": self.prehenseur_data.get("v_z", 0),
                "angle": self.prehenseur_data.get("angle", 0),
                "charge_balance": self.prehenseur_data.get("charge_balance", 0),
                "etat_stm": self.prehenseur_data.get("etat_stm", 0),
                "destination": self.prehenseur_data.get("destination", (0, 0)),
                "gyro_x": self.prehenseur_data.get("gyro_x", 0),
                "gyro_y": self.prehenseur_data.get("gyro_y", 0),
                "gyro_z": self.prehenseur_data.get("gyro_z", 0),
                "accel_x": self.prehenseur_data.get("accel_x", 0),
                "accel_y": self.prehenseur_data.get("accel_y", 0),
                "accel_z": self.prehenseur_data.get("accel_z", 0),
                "courant": round(courant, 2),
                "tension": round(tension, 2),
                "proximite": round(proximite, 2),
                "puissance": round(courant * tension, 2)
            }
                if self.data_callback is not None:
                    self.data_callback(self.prehenseur_data)
                    print(f"🔹 Courant: {courant:.2f} A | Tension: {tension:.2f} V | Proximité: {proximite:.2f} cm")
                    self.send_log_info(f"🔹 Courant: {courant:.2f} A | Tension: {tension:.2f} V | Proximité: {proximite:.2f} cm")
            else:
                print("Données reçues (brutes) :", p_data)
                
        except struct.error as e:
            print(f"Erreur de décodage des données : {e}")
            self.send_log_info("Erreur de décodage des données")
    #Cette fonction déconnecte le dispositif BLE
    async def __disconnected_callback(self):
        if self._m_client != 0:
            try:
                await self._m_client.disconnect()
                print("Deconnected")
            except:
                pass
    
    #Fonction qui vérifie si un dispositif BLE possédant le bon nom est a proximité ("p_name" dans le constructeur). Ne pas modifier.
    def __connect_to_BLEbetween_callback(self):
        print("BLE device scan in progress... Please wait.") 
        self.send_log_info("BLE device scan in progress... Please wait.")
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.__scan())
        index = -1
        if len(self._devices) == 0:
            print('No BLE device detected')
            self.send_log_info('No BLE device detected')

        else:
            for i in range(0, len(self._devices), 1):
                if self.device_name == self._devices[i].name:
                    print("Device: " + self.device_name + " found!")
                    self.send_log_info("Device: " + self.device_name + " found!")
                    index = i
                    break   
        if index >= 0:
            loop.run_until_complete(self.__connect_to_BLE(self._devices[index].address, loop))
        else:
            print("Unable to connect")
            self.send_log_info("Unable to connect")
        loop.close()
        

    #Fonction qui se connecte au dispositifs BLE et qui attend et transmet des données. Ne pas modifier.
    async def __connect_to_BLE(self, address, loop):
        
        async with BleakClient(address, loop=loop) as client:          
            if (not client.is_connected):
                raise "client not connected"
                self.send_log_info("client not connected")

            self._m_client = client
            services = client.services
            service_found = False
            for ser in services:
                if ser.description == 'Nordic UART Service':
                    print('Connected')
                    print('Ready to receive commands')
                    self.send_log_info('Ready to receive commands')
                    self._connected = True
                    service_found = True
                    
                    while not(self._request_deconnection):
                        await self._m_client.start_notify(self._tx_charac, self.__callback)
                        await asyncio.sleep(0.01)
                        await self._m_client.stop_notify(self._tx_charac)
                        while len(self._packets_to_send) > 0:
                            await self._m_client.write_gatt_char(self._rx_charac, self._packets_to_send.pop(0))
                        time.sleep(0.01)

                    self._connected = False
                    return
            if service_found == False:
                print('Wrong device, BLE service not found, please retry')
                self.send_log_info('Wrong device, BLE service not found, please retry')
    

    def close(self):
        self.running = False


    def start_sequence(self):
        self.started = True
    
    def send_log_info(self, data):
        if self.log_callback:
            self.log_callback(data)

    def send_log_info(self, data):
            if self.log_callback:
                self.log_callback(data)