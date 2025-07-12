import os
import random
import string
import routeros_api

class BaseRouter:
    """Classe de base pour tous les gestionnaires de routeurs."""
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password

    def connect(self):
        """Établit la connexion avec le routeur."""
        raise NotImplementedError

    def disconnect(self):
        """Ferme la connexion avec le routeur."""
        raise NotImplementedError

    def generate_voucher(self, package):
        """Génère un voucher/ticket."""
        raise NotImplementedError

class MikroTikRouter(BaseRouter):
    """Gestionnaire pour les routeurs MikroTik."""
    def connect(self):
        try:
            self.connection = routeros_api.RouterOsApiPool(
                self.host,
                username=self.user,
                password=self.password,
                plaintext_login=True
            )
            self.api = self.connection.get_api()
            print("Connexion au routeur MikroTik réussie.")
            return True
        except Exception as e:
            print(f"Erreur de connexion au routeur MikroTik : {e}")
            return False

    def disconnect(self):
        if hasattr(self, 'connection'):
            self.connection.disconnect()
            print("Déconnexion du routeur MikroTik.")

    def generate_voucher(self, package):
        username = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        password = username
        
        # Préparation des paramètres pour le routeur
        user_params = {
            'name': username,
            'password': password,
            'profile': package['name'],
        }

        # Gérer les forfaits "illimités" vs "limités"
        if package.get('limit_type') != 'unlimited':
            user_params['limit-uptime'] = package['duration']

        try:
            # Crée un nouvel utilisateur Hotspot
            self.api.get_resource('/ip/hotspot/user').add(user_params)
            print(f"Voucher MikroTik créé : {username}")
            return username
        except Exception as e:
            print(f"Erreur lors de la création du voucher MikroTik : {e}")
            return None

class DummyRouter(BaseRouter):
    """Gestionnaire de simulation pour le développement."""
    def connect(self):
        print("Mode simulation : Connexion au routeur factice.")
        return True

    def disconnect(self):
        print("Mode simulation : Déconnexion du routeur factice.")

    def generate_voucher(self, package):
        username = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        print("-------------------------------------------")
        print(f"Mode simulation : Génération d'un voucher")
        print(f"  - Forfait : {package['name']}")
        print(f"  - Code généré : {username}")
        print("-------------------------------------------")
        return username

def get_router_manager():
    """Retourne une instance du gestionnaire de routeur approprié."""
    router_type = os.getenv('ROUTER_TYPE', 'dummy').lower()
    
    host = os.getenv('MIKROTIK_HOST')
    user = os.getenv('MIKROTIK_USER')
    password = os.getenv('MIKROTIK_PASS')

    if router_type == 'mikrotik':
        return MikroTikRouter(host, user, password)
    else:
        # Par défaut, on utilise le routeur de simulation
        return DummyRouter(host, user, password)
