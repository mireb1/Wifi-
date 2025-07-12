import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from router_manager import get_router_manager

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'une-cle-secrete-par-defaut')

# Nos forfaits Wi-Fi
# La clé 'duration' est utilisée pour la configuration du routeur (ex: limit-uptime sur MikroTik)
# Pour les forfaits "illimités", on ne met pas de limite de temps.
PACKAGES = {
    '1': {'name': '24h Illimité', 'price': 2000, 'duration': '1d', 'limit_type': 'unlimited'},
    '2': {'name': '1 Semaine Illimité', 'price': 1200, 'duration': '7d', 'limit_type': 'unlimited'},
    '3': {'name': '1 Mois Illimité', 'price': 4200, 'duration': '30d', 'limit_type': 'unlimited'},
}

@app.route('/')
def index():
    """Affiche la page d'accueil avec les forfaits."""
    return render_template('index.html', packages=PACKAGES, platform_name="Mireb Wifi")

@app.route('/buy/<package_id>')
def buy(package_id):
    """Redirige vers la page de paiement."""
    if package_id not in PACKAGES:
        flash("Forfait non valide.", "error")
        return redirect(url_for('index'))

    package = PACKAGES[package_id]
    
    # Construction de l'URL de paiement Flexpaie
    flexpaie_base_url = "https://vpos.flexpaie.com/pay/"
    api_key = os.getenv('FLEXPAIE_API_KEY')
    
    transaction_ref = f"MIREB-WIFI-{package_id}-{os.urandom(4).hex()}"
    
    # Paramètres pour Flexpaie (à vérifier avec leur documentation)
    # Le callback_url est crucial pour que Flexpaie sache où rediriger l'utilisateur
    callback_url = url_for('payment_callback', _external=True)
    
    payment_params = {
        'amount': package['price'],
        'currency': 'CDF', # ou 'USD' selon votre configuration
        'reference': transaction_ref,
        'description': f"Achat forfait {package['name']}",
        'callback_url': callback_url,
        'customer_name': 'Client Mireb Wifi', # Peut être demandé à l'utilisateur
        'customer_email': 'test@example.com'
    }
    
    # Pour la simulation, nous allons directement au callback
    # En production, vous redirigeriez vers l'URL de Flexpaie
    print("--- SIMULATION DE PAIEMENT ---")
    print(f"Référence: {transaction_ref}")
    print(f"Montant: {package['price']} CDF")
    print(f"Redirection de retour (callback): {callback_url}")
    print("-----------------------------")
    
    # Simuler un succès de paiement et passer les infos au callback
    return redirect(url_for('payment_callback', 
                            status='success', 
                            ref=transaction_ref, 
                            package_id=package_id))

@app.route('/payment/callback')
def payment_callback():
    """Gère le retour de la passerelle de paiement."""
    status = request.args.get('status')
    ref = request.args.get('ref')
    package_id = request.args.get('package_id')

    # En production, vous devriez vérifier la validité de la transaction
    # en appelant une API de Flexpaie avec la référence `ref`.

    if status == 'success' and package_id in PACKAGES:
        package = PACKAGES[package_id]
        
        router = get_router_manager()
        if router.connect():
            voucher_code = router.generate_voucher(package)
            router.disconnect()

            if voucher_code:
                return render_template('voucher.html', code=voucher_code, platform_name="Mireb Wifi")
            else:
                flash("Erreur critique lors de la génération de votre code. Veuillez contacter le support.", "error")
                return redirect(url_for('index'))
        else:
            flash("Erreur : Impossible de communiquer avec le système de gestion des accès.", "error")
            return redirect(url_for('index'))
    else:
        flash("Le paiement a échoué, a été annulé ou les données sont invalides.", "error")
        return redirect(url_for('index'))

if __name__ == '__main__':
    # Le mode debug ne doit JAMAIS être activé en production
    app.run(debug=False, host='0.0.0.0')
else:
    # Gunicorn va chercher l'objet 'app'
    gunicorn_app = app
