import serial
import time
import struct


class STM32Manager:
    def __init__(self, port=None, baudrate=115200, simulate=False):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.running = True
        self.data_callback = None
        self.log_callback = None
        self.simulate = simulate
        self.recovery = False
        self.started = False
        self.counter = 0
        if self.simulate:
            print("[PC] Mode simulation activé pour le STM32.")
            self.send_log_info("[PC] Mode simulation activé pour le STM32.")
            self.simlation_lines = []
            self.index_sim = 0
            self.load_stm32_sim()
        else:
            self.listen()


    def connect(self):
        if self.simulate:
            self.run_simulation()
            return
        while self.running:
            try:
                print("[PC] Connexion au STM32...")
                self.send_log_info("[PC] Connexion au STM32...")
                self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
                print("[PC] Connecté au STM32!")
                self.send_log_info("[PC] Connecté au STM32!")
                self.listen()
            except serial.SerialException:
                print("[PC] Échec de connexion au STM32, nouvel essai dans 5 secondes...")
                self.send_log_info("[PC] Échec de connexion au STM32, nouvel essai dans 5 secondes...")
                time.sleep(5)


    def send_log_info(self, data):
        if self.log_callback:
            self.log_callback(data)


    def listen(self):
        while self.running and (self.serial_conn or self.simulate):
            try:
                if self.simulate and self.started:
                    data = self.fake_data()
                else:
                    line = self.serial_conn.readline().decode().strip()
                    data = self.parse_data(line) if line else {}
                    if data and self.data_callback:
                        self.data_callback(data)
                # TODO: Trouver la bonne vitesse selon le baudrate et log seulement 1 fois seconde.
                time.sleep(0.01) # Augmentation de la vitesse, sinon le buffer se remplie trop vite
            except serial.SerialException:
                print("[PC] Connexion perdue avec le STM32, tentative de reconnexion...")
                self.send_log_info("[PC] Connexion perdue avec le STM32, tentative de reconnexion...")
                self.serial_conn = None
                break


    # region Simulation
    def run_simulation(self):
        while self.running:
            if self.started:
                data = self.fake_data()
                if self.data_callback:
                    self.data_callback(data)
            time.sleep(1)


    def load_stm32_sim(self):
        with open('simulation/stm32_sim.txt', 'r') as file:
            self.simlation_lines = file.readlines()


    def fake_data(self):
        line = self.simlation_lines[self.index_sim].strip()
        self.send_log_info(f"[STM32 -> PC] (SIMULATION) Commande recu : {line}")
        data = line.split(',')
        self.index_sim += 1
        if self.index_sim >= len(self.simlation_lines):
            self.index_sim = 0
        if len(data) == 1:
            print("[STM32 -> PC] " + line)
            return {"etat_stm": 1}
        elif len(data) == 2:
            print("[STM32 -> PC] " + line)
            return {"etat_stm": 1, "charge_balance": int(data[1].replace('charge_balance=',''))}
        else:
            print("[STM32 -> PC] " + line)
            return {"x": int(data[0].replace('x=','')), "y": int(data[1].replace('y=','')), "charge_balance": int(data[2].replace('charge_balance=',''))}
    # endregion


    # TODO: Une fois qu'on aura mis au clair la communication avec le STM32, on devra mettre a jour cette partie
    def parse_data(self, line):
        data = line.split(",")
        
        self.counter += 1
        print(line)
        self.send_log_info(line)
        if data[0] in ["moving","waiting"]:
            result = {'etat_stm': data[0]}
            for part in data[1:]:
                key, value = part.split('=')
                try:
                    if '.' in value:
                        result[key] = float(value)*10
                    else:
                        result[key] = int(value)
                except ValueError:
                    result[key] = value
                
            return result
        return None


    def send_command(self, command):
        if self.simulate:
            print(f"[PC -> STM32] (SIMULATION) Commande envoyée : {command}")
            self.send_log_info(f"[PC -> STM32] (SIMULATION) Commande envoyée : {command}")
        elif self.serial_conn and self.serial_conn.is_open:
            command_bytes = command.encode('utf-8')
            data_length = len(command_bytes)
            # Pack the length as a single byte
            header = struct.pack('B', data_length)
            packet = header + command_bytes
            # Print debug info separately
            print(f"[Python] Data length: {data_length}")
            print(f"[Python] Command bytes: {command_bytes}")
            self.send_log_info(f"[PC -> STM32] Commande envoyée : {command}")
            # Send the packet
            self.serial_conn.write(packet)
            # Optional delay for stability
            time.sleep(0.1)
        else:
            print("[PC -> STM32] Impossible d'envoyer la commande, non connecté.")
            self.send_log_info("[PC -> STM32] Impossible d'envoyer la commande, non connecté.")


    def close(self):
        self.running = False
        if self.serial_conn:
            self.serial_conn.close()


    def start_sequence(self):
        self.started = True