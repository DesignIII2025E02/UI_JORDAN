import asyncio
import threading
from manager.stm32_manager import STM32Manager
from manager.prehenseur_manager import PrehenseurManager

class DataManager:
    def __init__(self, port=None, baud=115200, simulate_stm=False, simulate_prehenseur=False, dev_mode=False):
        # Initialise les 2 managers
        self.stm32 = STM32Manager(port=port, baudrate=baud, simulate=simulate_stm)
        self.prehenseur = PrehenseurManager("DesignIII_Exx")
        
        # Créer les callback pour mettre a jours les données
        self.stm32.data_callback = self.process_stm32_data
        self.prehenseur.data_callback = self.process_prehenseur_data
        # Créer les callback pour mettre a jours le logs
        self.stm32.log_callback = self.process_stm32_log
        self.prehenseur.log_callback = self.process_prehenseur_log

        # Initialiser le dictionnaire des données avec des valeur par defaut
        self.current_data = {"x": 0, "y": 0, "z": 0, "v_x": 0, "v_y": 0, "v_z": 0, "angle": 0, "charge_balance": 0, "etat_stm": 0, "destination": (0, 0),
                             "gyro_x": 0, "gyro_y": 0, "gyro_z": 0, "accel_x": 0, "accel_y": 0, "accel_z": 0, "courant": 0, "tension": 0, "puissance": 0}
        self.current_logs = []
        self.current_stm32_log = []
        self.current_prehenseur_log = []
        # Créer les chemins a suivre
        self.map_origin_to_pickup = []
        self.map_pickup_to_dropoff = []

        # Comme on commence a 0,0 le premier point est deja compter
        self.index_path1 = 1

        # Comme le dernier point du path1 est le premier du path2, le point est deja compter
        self.index_path2 = 1

        # Permet de valider si nous somme a la fin du chemin
        self.max_index_path1 = 0
        self.max_index_path2 = 0

        # Permet de savoir si on commence le path2
        self.path1_completed = False

        # Permet de naviger entre pick-up et drop-off
        self.reverse_path = False
        self.started = False
        # Affiche les widgets pour envoyer des commandes
        self.dev_mode = dev_mode
        
        self.electro_count = 0
    # Permet de commencer la séquance
    def start_sequence(self):
        # Déclanche la lecture du UART et BLE
        self.stm32.start_sequence()
        self.prehenseur.start_sequence()

        # Obtenir la prochaine destination de la grue
        next_position = self.map_origin_to_pickup[self.index_path1]
        command_log = f"{int(next_position[0]), int(next_position[1])}"
        self.current_data["destination"] = command_log
        command = "destination,"+ str(float(next_position[0])/10) + "," + str(float(next_position[0])/10) +  "," + str(float(next_position[1])/10)
        self.started = True
        # Envoyer la commande au STM32
        self.stm32.send_command(command)
        self.index_path1 += 1


    # Permet de mettre a jour le premier chemin et son max_index
    def update_path1(self, path1):
        self.map_origin_to_pickup = path1
        # La facon que le waitAndSend fonctionne, nous ne devons pas mettre le -1
        self.max_index_path1 = len(self.map_origin_to_pickup)
        

    # Permet de mettre a jour le deuxieme chemin et son max_index
    def update_path2(self, path2):
        self.map_pickup_to_dropoff = path2
        self.max_index_path2 = len(self.map_pickup_to_dropoff) - 1

    # Mettre a jour le dictionnaire selon les data du STM32
    def process_stm32_data(self, data):
        self.current_data.update(data)
        # Lorsque le STM32 entre dans un certain etat, nous pouvons le faire attendre une instruction
        if data.get("etat_stm") == "waiting" and self.started:
            if self.path1_completed and self.index_path2 == self.max_index_path2 + 1:
                
                None
            else:
                command = ""
                # Si nous avons deja atteind le pick-up, on change pour le path2
                if self.index_path1 == self.max_index_path1:
                        self.path1_completed = True
                if not self.path1_completed:
                    next_position = self.map_origin_to_pickup[self.index_path1]
                    self.index_path1 += 1
                    command_path = f"{int(next_position[0]), int(next_position[1])}"
                    self.current_data["destination"] = command_path
                    command = "destination,"+ str(float(next_position[0])/10) + "," + str(float(next_position[0])/10) +  "," + str(float(next_position[1])/10)
                    self.stm32.send_command(command)
                else:
                    # TODO: Dans cette partie nous devons gerer le pick-up et drop-off
                    next_position = self.map_pickup_to_dropoff[self.index_path2]
                    if not self.reverse_path:
                        self.index_path2 += 1
                    else:
                        self.index_path2 -= 1
                    # lorsque la grue est au debut ou a fin du chemin, on inverse
                    if self.index_path2 == 0 or self.index_path2 == self.max_index_path2:
                        self.reverse_path = not self.reverse_path
                    command_path = f"{int(next_position[0]), int(next_position[1])}"
                    self.current_data["destination"] = command_path
                    command = "destination,"+ str(float(next_position[0])/10) + "," + str(float(next_position[0])/10) +  "," + str(float(next_position[1])/10)
                    self.stm32.send_command(command)
        elif data.get("etat_stm") == "moving":
            None
        else:
            None
            
            #print("[DataManager] Attente du préhenseur avant d'envoyer une coordonnée...")
            #asyncio.run(self.wait_and_send())


    # Mettre a jour le dictionnaire selon les data du Préhenseur
    def process_prehenseur_data(self, data):
        # Définir les clés qui doivent être mises à jour
        self.prehenseur.deactivateElectroMagnet()
        allowed_keys = {
            "courant", "tension", "puissance", "proximite",  # valeurs issues du paquet BLE
            "x", "y", "z", "v_x", "v_y", "v_z", "angle", 
            "charge_balance", "destination", "gyro_x", "gyro_y", "gyro_z", 
            "accel_x", "accel_y", "accel_z"
        }
        # Mettre à jour seulement les clés autorisées
        for key, value in data.items():
            if key in allowed_keys:
                self.current_data[key] = value


    # Mettre a jour la liste de commande envoyer et recu avec le prehenseur
    def process_prehenseur_log(self, log):
        self.current_logs.append(log)
        self.current_prehenseur_log.append(log)


    # Mettre a jour la liste de commande envoyer et recu avec le STM32
    def process_stm32_log(self, log):
        self.current_logs.append(log)
        self.current_stm32_log.append(log)
        

    # Si le STM32 est dans une certaine etat
    async def wait_and_send(self):
        # Ici, on attend que l'angle du Préhenseur soit de 0
        while self.current_data["angle"] > 0:
            if self.stm32.recovery:
                break
            await asyncio.sleep(0.5)
        # Selon son etat (waiting, recovery, ...)
        # TODO: Définir la machine d'état du STM32 pour mieux identifier sont fonctionnement
        if not self.stm32.recovery:
            command = ""
            # Si nous avons deja atteind le pick-up, on change pour le path2
            if self.index_path1 == self.max_index_path1:
                    self.path1_completed = True
            if not self.path1_completed:
                next_position = self.map_origin_to_pickup[self.index_path1]
                self.index_path1 += 1
                command = f"{int(next_position[0]), int(next_position[1])}"  
            else:
                # TODO: Dans cette partie nous devons gerer le pick-up et drop-off
                next_position = self.map_pickup_to_dropoff[self.index_path2]
                if not self.reverse_path:
                    self.index_path2 += 1
                else:
                    self.index_path2 -= 1
                # lorsque la grue est au debut ou a fin du chemin, on inverse
                if self.index_path2 == 0 or self.index_path2 == self.max_index_path2:
                    self.reverse_path = not self.reverse_path
                command = f"{int(next_position[0]), int(next_position[1])}"
            self.current_data["destination"] = command
            self.stm32.send_command(command)


    # Envoie la commande pour positionner a Homing
    def position_origin(self):
        self.current_data["destination"] = '(0, 0)'


    # Start les thread pour le prehenseur et le stm32
    def start(self):
        stm32_thread = threading.Thread(target=self.stm32.connect, daemon=True)
        stm32_thread.start()
        self.prehenseur.startBLE_Thread()


    def run_prehenseur_async(self):
        self.prehenseur.data_callback = self.process_prehenseur_data
       


    def stop(self):
        self.stm32.close()
        self.prehenseur.close()


    # Permet d'envoyer au stm32 des commande en dev_mode
    def send_command_stm(self, command):
        self.stm32.send_command(command)


    # Permet d'envoyer au prehenseur des commande en dev_mode
    def send_command_prehenseur(self, command):
        if isinstance(command, str):  # Si la commande est une chaîne de caractères
            asyncio.run(self.prehenseur.__sendDataPacket(command))
        elif isinstance(command, int):  # Si la commande est un nombre (électroaimant)
            if command == 3:
                self.prehenseur.activateElectroMagnet()
            elif command == 4:
                self.prehenseur.deactivateElectroMagnet()