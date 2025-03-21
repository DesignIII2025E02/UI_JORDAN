import asyncio
import random
from bleak import BleakClient, BleakError

class PrehenseurManager:
    def __init__(self, address, simulate=False):
        self.tx_charac = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'
        self.rx_charac = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'
        self.address = address
        self.client = None
        self.running = True
        self.data_callback = None
        self.log_callback = None
        self.simulate = simulate
        self.started = False
        if self.simulate:
            print("[PC] Mode simulation activé pour le prehenseur.")
            self.send_log_info("[PC] Mode simulation activé pour le prehenseur.")
            self.simlation_lines = []
            self.index_sim = 0
            self.load_prehenseur_sim()


    async def connect(self):
        if self.simulate:
            await self.run_simulation()
            return
        while self.running:
            try:
                print("[PC] Connexion au préhenseur BLE...")
                self.send_log_info("[PC] Connexion au préhenseur BLE...")
                async with BleakClient(self.address) as client:
                    self.client = client
                    print("[PC] Connecté au prehenseur!")
                    self.send_log_info("[PC] Connecté au prehenseur!")
                    await self.listen()
            except BleakError:
                print("[PC] Échec de connexion au prehenseur, nouvel essai dans 5 secondes...")
                self.send_log_info("[PC] Échec de connexion au prehenseur, nouvel essai dans 5 secondes...")
                await asyncio.sleep(5)


    def send_log_info(self, data):
        if self.log_callback:
            self.log_callback(data)


    async def listen(self):
        while self.running and (self.client and self.client.is_connected):
            try:
                if self.simulate and self.started:
                    data = self.fake_data()
                else:
                    data = await self.read_data()
                    if data and self.data_callback:
                        self.data_callback(data)
                await asyncio.sleep(1) # TODO: Modifier la lecture lorsqu'on descend pour prendre la charge_balance ? Si oui, l'indiquer dans les logs.
            except BleakError:
                print("[PC] Connexion du prehenseur perdue, tentative de reconnexion...")
                self.send_log_info("[PC] Connexion du prehenseur perdue, tentative de reconnexion...")
                break


    # region Simulation
    async def run_simulation(self):
        while self.running:
            if self.started:
                data = self.fake_data()
                if self.data_callback:
                    self.data_callback(data)
            await asyncio.sleep(1)


    def load_prehenseur_sim(self):
        with open('simulation/prehenseur_sim.txt', 'r') as file:
            self.simlation_lines = file.readlines()


    def fake_data(self):
        data = self.simlation_lines[self.index_sim].strip().split(',')
        self.send_log_info(f"[Prehenseur -> PC] (SIMULATION) Commande recu : {data}")
        self.index_sim += 1
        if self.index_sim >= len(self.simlation_lines):
            self.index_sim = 0
        print(f"[Prehenseur -> PC] (SIMULATION) {int(data[0].replace('angle=',''))}")
        if len(data) == 1:
            return {"angle": int(data[0].replace("angle=","")), "gyro_x": random.random(), "gyro_y": random.random(), "gyro_z": random.random(), 
                    "accel_x": random.random(), "accel_y": random.random(), "accel_z": random.random(),
                    "courant": random.random(), "tension": random.random(), "puissance": random.random()}
        return {"angle": 45}
    #endregion


    async def read_data(self):
        if self.client and self.client.is_connected:
            try:
                data = await self.client.read_gatt_char(self.tx_charac)
                decoded_data = data.decode()
                print(f"[Prehenseur -> PC] Données reçues : {decoded_data}")
                if decoded_data == '':
                    return None
                self.send_log_info(f"[Prehenseur -> PC] Données reçues : {decoded_data}")
                # return {"angle": int(decoded_data.split('=')[1])}
            except Exception as e:
                print(f"[Prehenseur -> PC] Erreur de lecture : {e}")
                self.send_log_info(f"[Prehenseur -> PC] Erreur de lecture : {e}")
                return None
        return {"angle": 45} # TODO: Enlever cette ligne lorsque nous allons avoir une idee des communication


    async def send_data(self, data):
        if self.client and self.client.is_connected:
            try:
                await self.client.write_gatt_char(self.rx_charac, data.encode())
                print(f"[PC -> Prehenseur] Données envoyées : {data}")
                self.send_log_info(f"[PC -> Prehenseur] Données envoyées : {data}")
            except Exception as e:
                print(f"[PC -> Prehenseur] Erreur d'envoi : {e}")
                self.send_log_info(f"[PC -> Prehenseur] Erreur d'envoi : {e}")


    def close(self):
        self.running = False


    def start_sequence(self):
        self.started = True