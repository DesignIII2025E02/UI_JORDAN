import matplotlib.pyplot as plt
import pandas as pd
import math
import heapq
import time
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QPushButton, QSizePolicy, QApplication, QGridLayout, QLineEdit, QDialog, QTabWidget, QListView
from PyQt5.QtCore import QTimer, QFile, QTextStream, Qt, QStringListModel
from PyQt5.QtGui import QPixmap
from window.multiple_command_dialog import MultipleCommandDialog


class LivePlot(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.charge_balance_succes_pixmap = QPixmap("image/rondelle_verte.png")
        self.charge_balance_empty_pixmap = QPixmap("image/rondelle_vide.png")
        self.max_x = 700
        self.max_y = 700
        self.theme = 0
        self.file_name = ""
        file_dark = QFile("theme/dark.qss")
        file_dark.open(QFile.ReadOnly | QFile.Text)
        self.stream_dark = QTextStream(file_dark)
        file_light = QFile("theme/light.qss")
        file_light.open(QFile.ReadOnly | QFile.Text)
        self.stream_light = QTextStream(file_light)
        self.path1_labels = [] # Path1 est le chemin de l'origine vers la pick-ip
        self.path2_labels = [] # path2 est le chemin du picl-up vers le drop-off
        self.init_ui()


    # Créer l'interface graphique
    def init_ui(self):
        # Créer le layout initial vertical
        layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignTop)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        #left_widget.setMinimumWidth(400)

        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignTop)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        #right_widget.setMinimumWidth(400)

        # Créer le layout pour le bouton de theme
        layout_theme = QHBoxLayout()
        self.btn_theme = QPushButton("Light/dark", self)
        self.btn_theme.clicked.connect(self.toggle_stylesheet)
        self.btn_theme.setGeometry(200, 150, 100, 40) 
        layout_theme.addWidget(self.btn_theme)
        left_layout.addLayout(layout_theme)        

        # Créer le layout pour les boutons
        layout_btn = QHBoxLayout()
        self.btn_load_csv = QPushButton("Ouvrir une carte", self)
        self.btn_load_csv.clicked.connect(self.load_csv)
        self.btn_starting_position = QPushButton("Mettre a (0, 0)", self)
        self.btn_starting_position.clicked.connect(self.set_starting_position)
        self.btn_start = QPushButton("Commencer", self)
        self.btn_start.clicked.connect(self.start_sequence)
        self.btn_start.setDisabled(True)
        layout_btn.addWidget(self.btn_starting_position)
        layout_btn.addWidget(self.btn_load_csv)
        layout_btn.addWidget(self.btn_start)
        left_layout.addLayout(layout_btn)

        # Créer le layout principal pour les données du préhenseur
        prehenseur_layout = QVBoxLayout()
        prehenseur_layout.setAlignment(Qt.AlignTop)
        self.title_prehenseur = QLabel("Valeurs Prehenseur")
        self.title_prehenseur.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.title_prehenseur.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.title_prehenseur.setAlignment(Qt.AlignCenter)
        prehenseur_layout.addWidget(self.title_prehenseur)

        # Créer un layout horizontal pour les deux colonnes
        columns_layout = QHBoxLayout()
        # Première colonne
        value_data_gyro_layout = QVBoxLayout()
        value_data_gyro_layout.setAlignment(Qt.AlignTop)
        self.label_prehenseur_gyro_x = QLabel("Gyro X: 0")
        self.label_prehenseur_gyro_y = QLabel("Gyro Y: 0")
        self.label_prehenseur_gyro_z = QLabel("Gyro Z: 0")
        value_data_gyro_layout.addWidget(self.label_prehenseur_gyro_x)
        value_data_gyro_layout.addWidget(self.label_prehenseur_gyro_y)
        value_data_gyro_layout.addWidget(self.label_prehenseur_gyro_z)
        # Deuxième colonne
        value_data_accel_layout = QVBoxLayout()
        value_data_accel_layout.setAlignment(Qt.AlignTop)
        self.label_prehenseur_accel_x = QLabel("Accel X: 0")
        self.label_prehenseur_accel_y = QLabel("Accel Y: 0")
        self.label_prehenseur_accel_z = QLabel("Accel Z: 0")
        value_data_accel_layout.addWidget(self.label_prehenseur_accel_x)
        value_data_accel_layout.addWidget(self.label_prehenseur_accel_y)
        value_data_accel_layout.addWidget(self.label_prehenseur_accel_z)
        # Troiseme colonne
        value_data_battery_layout = QVBoxLayout()
        value_data_battery_layout.setAlignment(Qt.AlignTop)
        self.label_prehenseur_courant = QLabel("Courant: 0 mA")
        self.label_prehenseur_tension = QLabel("Tension: 0 mV")
        self.label_prehenseur_puissance = QLabel("Puissance: 0 W")
        value_data_battery_layout.addWidget(self.label_prehenseur_courant)
        value_data_battery_layout.addWidget(self.label_prehenseur_tension)
        value_data_battery_layout.addWidget(self.label_prehenseur_puissance)
        # Ajouter les colonnes au layout horizontal
        columns_layout.addLayout(value_data_gyro_layout)
        columns_layout.addLayout(value_data_accel_layout)
        columns_layout.addLayout(value_data_battery_layout)
        # Ajouter le layout horizontal sous le titre
        prehenseur_layout.addLayout(columns_layout)
        # Créer un layout temporaire pour envoyer des commandes au STM32
        if self.data_manager.dev_mode:
            command_layout = QHBoxLayout()
            self.command_text_prehenseur = QLineEdit(self)
            self.btn_send_prehenseur = QPushButton("Send", self)
            self.btn_send_prehenseur.clicked.connect(self.send_command_prehenseur)
            command_layout.addWidget(self.command_text_prehenseur)
            command_layout.addWidget(self.btn_send_prehenseur)
            prehenseur_layout.addLayout(command_layout)

        left_layout.addLayout(prehenseur_layout)

        # Créer le layout principal des données du STM32
        stm_layout = QVBoxLayout()
        stm_layout.setAlignment(Qt.AlignTop)
        self.title_stm = QLabel("Valeurs STM32")
        self.title_stm.setStyleSheet("font-size: 24px; font-weight: bold;")
        stm_layout.addWidget(self.title_stm)
        # Créer un layout horizontal pour contenir les deux colonnes
        columns_layout = QHBoxLayout()
        # Créer un sous-layout pour la position de la grue
        value_pos_layout = QVBoxLayout()
        value_pos_layout.setAlignment(Qt.AlignTop)
        self.label_x = QLabel("Position X: 0")
        self.label_y = QLabel("Position Y: 0")
        self.label_z = QLabel("Position Z: 0")
        value_pos_layout.addWidget(self.label_x)
        value_pos_layout.addWidget(self.label_y)
        value_pos_layout.addWidget(self.label_z)
        # Créer un sous-layout pour la vitesse de la grue
        value_speed_layout = QVBoxLayout()
        value_speed_layout.setAlignment(Qt.AlignTop)
        self.label_speed_x = QLabel("Vitesse X: 0")
        self.label_speed_y = QLabel("Vitesse Y: 0")
        self.label_speed_z = QLabel("Vitesse Z: 0")
        value_speed_layout.addWidget(self.label_speed_x)
        value_speed_layout.addWidget(self.label_speed_y)
        value_speed_layout.addWidget(self.label_speed_z)
        # Ajouter les deux colonnes au layout horizontal
        columns_layout.addLayout(value_pos_layout)
        columns_layout.addLayout(value_speed_layout)
        
        stm_layout.addLayout(columns_layout)
        # Créer un layout temporaire pour envoyer des commandes au STM32
        if self.data_manager.dev_mode:
            command_layout = QHBoxLayout()
            self.command_text = QLineEdit(self)
            self.btn_send = QPushButton("Send", self)
            self.btn_send.clicked.connect(self.send_command)
            self.btn_open_command_dialog = QPushButton("?", self)
            self.btn_open_command_dialog.clicked.connect(self.open_command_dialog)
            command_layout.addWidget(self.command_text)
            command_layout.addWidget(self.btn_send)
            command_layout.addWidget(self.btn_open_command_dialog)
            stm_layout.addLayout(command_layout)
        left_layout.addLayout(stm_layout)

        # Create a QTabWidget
        self.tab_widget = QTabWidget(self)
        
        # Create the QListView for each tab
        self.list_view1 = QListView(self)
        self.list_view2 = QListView(self)
        self.list_view3 = QListView(self)
        
        # Create models for each list view
        self.model1 = QStringListModel(self)
        self.model2 = QStringListModel(self)
        self.model3 = QStringListModel(self)
        
        # Bind the models to the list views
        self.list_view1.setModel(self.model1)
        self.list_view2.setModel(self.model2)
        self.list_view3.setModel(self.model3)

        # Create the tabs
        self.tab_widget.addTab(self.list_view1, "Tous")
        self.tab_widget.addTab(self.list_view2, "STM32")
        self.tab_widget.addTab(self.list_view3, "Prehenseur")

        # Add the tab widget to the left layout
        left_layout.addWidget(self.tab_widget)

        layout.addWidget(left_widget, 1)

        # Créer le layout pour afficher le nombre de rondelle sur la balance
        self.charge_balance_layout = QHBoxLayout()
        self.charge_balance_layout.setAlignment(Qt.AlignHCenter)
        self.charge_balance_layout.setSpacing(0)
        self.charge_balance_layout.setContentsMargins(0, 30, 0, 0)  
        self.charge_balances = []
        self.max_charge_balances = 5
        for i in range(self.max_charge_balances):
            label = QLabel(self)
            label.setPixmap(self.charge_balance_empty_pixmap)
            label.setFixedSize(self.charge_balance_empty_pixmap.size())
            label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            label.setScaledContents(True)
            self.charge_balance_layout.addWidget(label)
            self.charge_balances.append(label)
        right_layout.addLayout(self.charge_balance_layout)

        # Créer le graphique pour afficher la carte et le deplacement de la grue
        self.figure, self.ax = plt.subplots(figsize=(8, 10))
        self.figure.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        self.ax.set_xlim(0, self.max_x)
        self.ax.set_ylim(0, self.max_y)
        self.ax.set_aspect('equal')
        self.ax.invert_xaxis()
        self.ax.set_xticks(range(0, self.max_x + 1, 100))
        self.ax.set_xticklabels([str(tick) for tick in range(0, self.max_x + 1, 100)])
        self.ax.set_yticks(range(0, self.max_y + 1, 100))
        self.ax.set_yticklabels([str(tick) for tick in range(0, self.max_y + 1, 100)])
        self.ax.grid(True)
        self.canvas = FigureCanvas(self.figure)
        self.figure.patch.set_facecolor("none")
        self.canvas.setAttribute(Qt.WA_TranslucentBackground)
        self.canvas.setFixedSize(1000, 800)  # Increased canvas size
        self.mobile_point, = self.ax.plot([], [], 'ro', markersize=10)
        right_layout.addWidget(self.canvas)

        # Créer le layout pour afficher les chemins a suivre
        self.grid_layout = QGridLayout()
        self.grid_layout.setAlignment(Qt.AlignTop)
        self.grid_layout.addWidget(QLabel("Origine -> Pick-up:"), 0, 0)
        self.grid_layout.addWidget(QLabel("Pick-up <-> Drop-off:"), 1, 0)
        right_layout.addLayout(self.grid_layout)

        layout.addWidget(right_widget, 1)

        # Ajouter le layout principal a l'application
        self.setLayout(layout)

        # Créer un timer pour rafraichir les informations au seconde
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(1000)


    # Permet de commencer la lecture des informations
    # Pourrais etre supprimer et lire au debut
    def start_sequence(self):
        self.data_manager.start_sequence()


    # Permet d'envoyer la commande pour indique a la grue de se positionner a Homing
    # TODO: Modifier la commande selon la facon que le STM32 va fonctionner
    def set_starting_position(self):
        self.data_manager.position_origin()
        self.data_manager.stm32.send_command("pos: 0,0")


    # region Ouvrir la carte et creer les chemins
    # Permet d'ouvrir un fichier CSV d'une carte
    def load_csv(self):
        temp = self.file_name
        options = QFileDialog.Options()
        self.file_name, _ = QFileDialog.getOpenFileName(self, "Choisir la carte", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if self.file_name:
            self.plot_from_csv(self.file_name)
        else:
            self.file_name = temp


    # Permet de créer les points et les ligne dans le graphique
    def plot_from_csv(self, file_name):
        # Supprimer les informations dans le graphique
        for line in self.ax.lines:
            line.remove()
        for text in self.ax.texts:
            text.remove()

        # Lire le fichier 
        data = pd.read_csv(file_name)
        points = [(row['x'], row[' y']) for index, row in data.iterrows()]

        # Dictionnaire qui va permettre de savoir les chemin possible
        # Key: point x,y      value: Points possible selon les angles
        reachable_points = {}

        text_color = 'white'
        if self.theme == 0:
            text_color = 'black'
        for index, row in data.iterrows():
            x = row['x']
            y = row[' y']
            angles = [row[f' angle{i + 1}'] for i in range(4)]
            reachable_points[(int(x), int(y))] = []
            # Dessiner le point, differente couleur selon son type
            if index == 0: # Origine
                self.ax.plot(x, y, 'bo') 
                text = self.ax.text(x, y, f'({row["x"]}, {row[" y"]}) - Origin', fontsize=8, ha='right', va='top')
                text.set_color(text_color)
            elif index == 1: # Pick-up
                self.ax.plot(x, y, 'go') 
                text = self.ax.text(x, y, f'({row["x"]}, {row[" y"]})', fontsize=8, ha='right', va='top')
                text.set_color(text_color)
            elif index == 2: # Drop-off
                self.ax.plot(x, y, 'ko') 
                text = self.ax.text(x, y, f'({row["x"]}, {row[" y"]})', fontsize=8, ha='right', va='top')
                text.set_color(text_color)
            else: # Turn
                self.ax.plot(x, y, 'mo') 
                text = self.ax.text(x, y, f'({row["x"]}, {row[" y"]})', fontsize=8, ha='right')
                text.set_color(text_color)
            for angle in angles:
                if angle != -1:
                    # On normalize l'angle pour reste dans les limites 0-360
                    angle_deg = self.normalize_angle(angle)
                    best_point = None
                    min_distance = float('inf')  # Distance minimale initiale
                    for point in points:
                        if (x, y) == point:
                            continue
                        # On calcule si le point est dans l'angle
                        dy = y - point[1]
                        dx = x - point[0]
                        angle_rad = math.atan2(dy, dx)
                        angle_calculated_deg = math.degrees(angle_rad) + 90
                        angle_calculated_deg = self.normalize_angle(angle_calculated_deg)
                        if angle_calculated_deg == angle_deg:
                            distance = math.sqrt(dx ** 2 + dy ** 2)
                            # On garde seulement le point le plus proche
                            # Il est possible que plusieurs points soit aligner sur le meme angle
                            if distance < min_distance:
                                min_distance = distance
                                best_point = point
                    # On dessine la ligne entre les 2 points
                    if best_point:
                        reachable_points[(x, y)].append((best_point, min_distance))
                        if self.theme == 0:
                            self.ax.plot([x, best_point[0]], [y, best_point[1]], 'b-')
                            self.ax.text((x + best_point[0]) / 2, (y + best_point[1]) / 2, f'{min_distance:.2f}', fontsize=8, color='blue')
                        else:
                            self.ax.plot([x, best_point[0]], [y, best_point[1]], 'c-')
                            self.ax.text((x + best_point[0]) / 2, (y + best_point[1]) / 2, f'{min_distance:.2f}', fontsize=8, color='cyan')
        # Definir les point start, end pour Dijkstra
        start = (int(points[0][0]), int(points[0][1]))
        pickup = (int(points[1][0]), int(points[1][1]))
        dropoff = (int(points[2][0]), int(points[2][1]))
        # Obtenir les chemins les plus efficace en distance
        self.path1, _ = self.dijkstra(reachable_points, start, pickup)
        self.path2, _ = self.dijkstra(reachable_points, pickup, dropoff)
        self.data_manager.update_path1(self.path1)
        self.data_manager.update_path2(self.path2)
        for text in self.ax.texts:
            text.set_color = text_color
        # Affiche les chemins
        self.update_paths_display(self.path1, self.path2)
        self.mobile_point, = self.ax.plot([], [], 'ro', markersize=8)
        # Rafraichie les données afficher
        self.update_plot() 
        self.btn_start.setDisabled(False)
        self.canvas.draw()
    

    # Normalise l'angle pour reste entre 0-360
    def normalize_angle(self, angle):
        return angle % 360
    

    # Algorithm pour le plus cours chemin
    # TODO: Modifier pour A* serait probablement plus rapide, est-ce utile?
    def dijkstra(self, graph, start, end):
        queue = [(0, start)]  # (cost, node)
        distances = {node: float('inf') for node in graph}
        distances[start] = 0
        previous_nodes = {}
        while queue:
            current_distance, current_node = heapq.heappop(queue)
            if current_node == end:
                path = []
                while current_node in previous_nodes:
                    path.insert(0, current_node)
                    current_node = previous_nodes[current_node]
                path.insert(0, start)
                return path, distances[end]
            for neighbor, weight in graph[current_node]:
                new_distance = current_distance + weight
                if new_distance < distances[(int(neighbor[0]), int(neighbor[1]))]:
                    distances[neighbor] = new_distance
                    previous_nodes[neighbor] = current_node
                    heapq.heappush(queue, (new_distance, neighbor))
    # endregion


    # region Actualiser l'affichage
    # Permet de mettre a jours les données
    def update_plot(self):
        # Data du stm
        dest = self.data_manager.current_data["destination"]
        x = self.data_manager.current_data["x"]
        y = self.data_manager.current_data["y"]
        z = self.data_manager.current_data["z"]
        v_x = self.data_manager.current_data["v_x"]
        v_y = self.data_manager.current_data["v_y"]
        v_z = self.data_manager.current_data["v_z"]
        charge_balance = self.data_manager.current_data["charge_balance"]
        self.label_x.setText(f"Position X: {x}")
        self.label_y.setText(f"Position Y: {y}")
        self.label_z.setText(f"Position Z: {z}")
        self.label_speed_x.setText(f"Vitesse X: {v_x}")
        self.label_speed_y.setText(f"Vitesse Y: {v_y}")
        self.label_speed_z.setText(f"Vitesse Z: {v_z}")

        # Data du prehenseur
        gyro_x = self.data_manager.current_data["gyro_x"]
        gyro_y = self.data_manager.current_data["gyro_y"]
        gyro_z = self.data_manager.current_data["gyro_z"]
        accel_x = self.data_manager.current_data["accel_x"]
        accel_y = self.data_manager.current_data["accel_y"]
        accel_z = self.data_manager.current_data["accel_z"]
        courant = self.data_manager.current_data["courant"]
        tension = self.data_manager.current_data["tension"]
        puissance = self.data_manager.current_data["puissance"]
        self.label_prehenseur_gyro_x.setText(f"Gyro X: {gyro_x}")
        self.label_prehenseur_gyro_y.setText(f"Gyro Y: {gyro_y}")
        self.label_prehenseur_gyro_z.setText(f"Gyro Z: {gyro_z}")
        self.label_prehenseur_accel_x.setText(f"Accel X: {accel_x}")
        self.label_prehenseur_accel_y.setText(f"Accel Y: {accel_y}")
        self.label_prehenseur_accel_z.setText(f"Accel Z: {accel_z}")
        self.label_prehenseur_courant.setText(f"Courant: {courant} mA")
        self.label_prehenseur_tension.setText(f"Tension: {tension} mV")
        self.label_prehenseur_puissance.setText(f"Puissance: {puissance} W")

        self.mobile_point.set_data([x], [y])
        self.highlight_selected_point(dest)
        for i in range(self.max_charge_balances):
            if i < charge_balance:
                self.charge_balances[i].setPixmap(self.charge_balance_succes_pixmap)
            else:
                self.charge_balances[i].setPixmap(self.charge_balance_empty_pixmap)

        # Afficher les logs
        self.model1.setStringList(self.data_manager.current_logs)
        self.model2.setStringList(self.data_manager.current_stm32_log)
        self.model3.setStringList(self.data_manager.current_prehenseur_log)
        
        self.list_view1.scrollToBottom()
        self.list_view2.scrollToBottom()
        self.list_view3.scrollToBottom()

        self.canvas.draw()


    # Permet selon les coordonnées x,y de mettre le background en vert
    # Ceci permet d'identifier le point vers lequel la grue se dirige
    def highlight_selected_point(self, dest):
        path1_done = self.data_manager.path1_completed
        if self.theme == 0:
            for label in self.path1_labels:
                label.setStyleSheet("color: black; background: none;")
                if label.text() == dest and not path1_done:
                    label.setStyleSheet("color: white; background: green;")
            for label in self.path2_labels:
                label.setStyleSheet("color: black; background: none;")
                if label.text() == dest and path1_done:
                    label.setStyleSheet("color: white; background: green;")   
        else:
            for label in self.path1_labels:
                label.setStyleSheet("color: white; background: none;")
                if label.text() == dest and not path1_done:
                    label.setStyleSheet("color: white; background: green;")
            for label in self.path2_labels:
                label.setStyleSheet("color: white; background: none;")
                if label.text() == dest and path1_done:
                    label.setStyleSheet("color: white; background: green;")

    
    # Mettre a jours les chemins afficher
    def update_paths_display(self, path1, path2):
        # Suppression des anciens labels
        for label in self.path1_labels:
            self.grid_layout.removeWidget(label)
            label.deleteLater()
        for label in self.path2_labels:
            self.grid_layout.removeWidget(label)
            label.deleteLater()  
        self.path1_labels = []
        self.path2_labels = []    
        max_len = max(len(path1), len(path2))       
        for i in range(max_len):
            if i < len(path1):
                label = QLabel(f'({path1[i][0]}, {path1[i][1]})')
                label.setAlignment(Qt.AlignCenter)
                self.path1_labels.append(label)
                self.grid_layout.addWidget(label, 0, i + 1)
            else:
                empty_label = QLabel("")
                self.grid_layout.addWidget(empty_label, 0, i + 1)
            if i < len(path2):
                label = QLabel(f'({path2[i][0]}, {path2[i][1]})')
                label.setAlignment(Qt.AlignCenter)
                self.path2_labels.append(label)
                self.grid_layout.addWidget(label, 1, i + 1)
            else:
                empty_label = QLabel("")
                self.grid_layout.addWidget(empty_label, 1, i + 1)
    # endregion
        
    
    # region Theme
    # Utiliser pour lire les fichier de theme
    def load_stylesheet(self, filename):
        try:
            with open(filename, "r") as file:
                return file.read()
        except Exception as e:
            print(f"Erreur lors du charge_balancement de {filename} : {e}")
            return ""


    # Permet de changer entre les 2 themes
    def toggle_stylesheet(self):
        self.theme = 1 - self.theme
        app = QApplication.instance()
        if app is None:
            print("Erreur : QApplication n'est pas instanciée.")
            return
        qss_file = "theme/dark.qss" if self.theme == 1 else "theme/light.qss"
        style_sheet = self.load_stylesheet(qss_file)
        self.toggle_plot_theme()
        if style_sheet:
            app.setStyleSheet(style_sheet)

        
    # Le theme ne possede pas de modification pour le graphique
    # Cette methode modifie le graphique selon le theme
    def toggle_plot_theme(self):
        if self.theme == 0:
            plt.style.use("dark_background")
            self.figure.patch.set_facecolor("none")
        else:
            plt.style.use("default")
            self.figure.patch.set_facecolor("none")
        self.canvas.setStyleSheet("background: transparent;")       
        self.ax.set_facecolor("none")
        if self.theme == 0:
            self.ax.grid(True, color='black')
            self.ax.tick_params(axis='x', colors='black')
            self.ax.tick_params(axis='y', colors='black')
        else:
            self.ax.grid(True, color='white')
            self.ax.tick_params(axis='x', colors='white')
            self.ax.tick_params(axis='y', colors='white')
        self.ax.set_xlim(-10, self.max_x)
        self.ax.set_ylim(-10, self.max_y)
        self.ax.set_aspect('equal')
        self.ax.invert_xaxis()
        self.ax.set_xticks(range(0, self.max_x + 1, 100))
        self.ax.set_yticks(range(0, self.max_y + 1, 100))
        if not self.file_name == "":
            self.plot_from_csv(self.file_name)
        self.canvas.draw()
    # endregion


    # region Section developpeur
    # Permet d'envoyer une commande manuellement au STM32
    def send_command(self):
         self.data_manager.send_command_stm(self.command_text.text())

    
    def send_command_prehenseur(self):
        self.data_manager.send_command_prehenseur(self.command_text_prehenseur.text())


    # Permet d'ouvrir la fenetre pour envoyer plusieurs commande au STM32
    def open_command_dialog(self):
        dialog = MultipleCommandDialog()
        if dialog.exec_() == QDialog.Accepted:
            commands = dialog.commands
            if not commands == None or not commands == "":
                list_command = commands.split('\n')
                for line in list_command:
                    if line.startswith("d="):
                        delay = float(line.replace("d=",""))
                        time.sleep(delay)
                    else:
                        self.data_manager.send_command_stm(line)
    # endregion