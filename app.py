# app.py
import os
import webbrowser
import threading
import time
import uuid
import database
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from tts_engines.gtts_engine import gtts_engine
import requests
import json
from flask import Response
# A supprimer quand c'est à lancer
import urllib3
# Désactive les avertissements InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Nouvelle fonction pour ouvrir le navigateur ---
def open_browser():
    """Ouvre le navigateur par défaut après un court délai."""
    time.sleep(1.5) # Attendre que le serveur soit opérationnel
    webbrowser.open_new_tab('http://127.0.0.1:5000/')


# --- Utilisation de gTTS ---
# from gtts import gTTS # L'import reste le même

# --- Initialisation de Flask ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "une_cle_secrete_par_defaut_a_changer_v2")

# Dossier pour stocker les fichiers audio
AUDIO_FOLDER = os.path.join('static', 'audio')
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# --- Initialisation de la base de données ---
with app.app_context():
    database.init_db()

# --- Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    """Page d'accueil pour soumettre un document ou lister les récents."""
    if request.method == 'POST':
        # --- 1. Récupération des champs du formulaire ---
        title = request.form.get('title', '').strip()
        content_from_textarea = request.form.get('content', '').strip()
        selected_voice = request.form.get('voice', 'Femme (fr)')
        # --- NOUVEAU : Récupération du moteur TTS sélectionné ---
        selected_engine_name = request.form.get('tts_engine', 'gTTS') # Valeur par défaut

        # Options pour le moteur TTS
        tts_options = {'voice': selected_voice}
        
        # --- 2. Gestion du fichier uploadé ---
        content_from_file = ""
        txt_file = request.files.get('txt_file')
        if txt_file and txt_file.filename != '':
            if not txt_file.filename.lower().endswith('.txt'):
                 flash("Erreur : Veuillez sélectionner un fichier avec l'extension .txt.")
                 return redirect(url_for('index'))
            try:
                content_from_file = txt_file.read().decode('utf-8')
            except UnicodeDecodeError:
                flash("Erreur : Le fichier n'est pas un fichier texte valide (UTF-8).")
                return redirect(url_for('index'))
            except Exception as e:
                flash(f"Erreur lors de la lecture du fichier : {e}")
                return redirect(url_for('index'))

        # --- 3. Déterminer le contenu final ---
        final_content = content_from_file if content_from_file else content_from_textarea

        # --- 4. Validation du contenu ---
        if not final_content:
            flash("Veuillez entrer du texte ou sélectionner un fichier .txt.")
            return redirect(url_for('index'))

        # --- 5. Validation du titre ---
        if not title:
            title = "Document sans titre"

        # --- 6. Suite du processus avec le moteur TTS modulaire ---
        slug = uuid.uuid4().hex[:8]
        audio_filename = f"{slug}.mp3"
        audio_file_path = os.path.join(AUDIO_FOLDER, audio_filename)
        
        # --- NOUVEAU : Logique de sélection du moteur TTS ---
        # Dictionnaire de mapping moteur
        tts_engines = {
            'gTTS': gtts_engine,
            # 'IBM Watson TTS': ibm_watson_tts_engine, # Décommente cette ligne plus tard
            # Ajouter d'autres moteurs ici
        }

        # Sélectionner le moteur
        selected_engine = tts_engines.get(selected_engine_name)
        if not selected_engine:
             flash(f"Moteur TTS '{selected_engine_name}' non reconnu.")
             return redirect(url_for('index'))

        # Utiliser le moteur sélectionné
        # success = selected_engine.synthesize(final_content, audio_file_path, tts_options)
        # --- FIN DE LA MODIFICATION POUR LA SÉLECTION ---

        # --- Pour l'instant, on garde l'ancien appel pour éviter les erreurs ---
        # Une fois ibm_watson_tts_engine.py prêt, remplacez cette ligne par celle du dessus.
        if selected_engine_name == 'gTTS':
            success = gtts_engine.synthesize(final_content, audio_file_path, tts_options)
        # elif selected_engine_name == 'IBM Watson TTS':
        #     success = ibm_watson_tts_engine.synthesize(final_content, audio_file_path, tts_options)
        else:
             # Gestion d'erreur si un moteur est sélectionné mais pas encore implémenté dans cette branche "if/elif"
             flash(f"Le traitement avec le moteur '{selected_engine_name}' n'est pas encore implémenté dans cette branche.")
             return redirect(url_for('index'))
        # --- FIN DE L'ADAPTATION ---

        if not success:
            flash("Erreur lors de la génération de l'audio. Veuillez réessayer.")
            return redirect(url_for('index'))

        relative_audio_path = f"audio/{audio_filename}"
        try:
            database.insert_document(slug, title, final_content, relative_audio_path)
        except sqlite3.IntegrityError:
            flash("Erreur lors de la sauvegarde. Veuillez réessayer.")
            return redirect(url_for('index'))

        return redirect(url_for('listen', slug=slug))

    # Si la méthode est GET, afficher la page d'accueil avec la liste des documents
    recent_docs = database.get_recent_documents(limit=10)
    return render_template('index.html', recent_docs=recent_docs)

@app.route('/listen/<slug>')
def listen(slug):
    """Page pour écouter un document."""
    doc = database.get_document_by_slug(slug)
    if doc is None:
        flash("Document non trouvé.")
        return redirect(url_for('index'))
    
    # Incrémenter le compteur de vues
    database.increment_view_count(slug)
    
    # Recharger le document pour avoir le count à jour
    doc = database.get_document_by_slug(slug)
    
    return render_template('listen.html', document=doc)
    
    
@app.route('/play/<slug>')
def play(slug):
    """Route API pour incrémenter le compteur de lecture d'un document."""
    doc = database.get_document_by_slug(slug)
    if doc is None:
        # Retourne une erreur JSON si le document n'existe pas
        return jsonify({"error": "Document non trouvé"}), 404
    
    # Incrémenter le compteur de plays dans la base de données
    database.increment_play_count(slug)
    
    # Retourne une réponse JSON de succès
    return jsonify({"success": True, "message": "Play count incremented"})


# --- Nouvelle route pour afficher les interactions ---
@app.route('/interactions/<slug>')
def show_interactions(slug):
    """Affiche une page avec le diagramme d'interactions."""
    doc = database.get_document_by_slug(slug)
    if doc is None:
        flash("Document non trouvé.")
        return redirect(url_for('index'))
    
    # Passer le document au template
    return render_template('interactions.html', document=doc)

'''@app.route('/showcase')
def public_showcase():
    """Page publique vitrine des documents récents."""
    recent_docs = database.get_recent_documents(limit=20) # On peut en montrer plus
    return render_template('public_showcase.html', documents=recent_docs)'''
    
@app.route('/api/documents.json')
def api_documents():
    """API simple pour obtenir la liste des documents récents en JSON."""
    recent_docs = database.get_recent_documents(limit=20)
    # Convertir les objets Row en dictionnaires si ce n'est pas déjà fait
    docs_list = [dict(doc) for doc in recent_docs]
    return Response(json.dumps(docs_list), mimetype='application/json')

# --- Nouvelle route temporaire pour tester la page vitrine ---
@app.route('/showcase')
def temp_showcase():
    """Route temporaire pour servir la page vitrine statique en développement."""
    # Envoie le fichier index.html depuis le dossier 'docs'
    # Assurez-vous que le fichier s'appelle bien 'index.html' et se trouve dans 'docs'
    return send_from_directory('docs', 'index.html')


# --- Nouvelle route pour générer l'image SVG du diagramme ---
@app.route('/interactions/<slug>/diagram.svg')
def get_interaction_diagram(slug):
    """Génère et renvoie le diagramme SVG des interactions via Kroki."""
    doc = database.get_document_by_slug(slug)
    if doc is None:
        # Retourner une image d'erreur ou un 404
        return "Document non trouvé", 404

    # --- 1. Préparer les données pour le diagramme ---
    title = doc['title']
    views = doc['view_count']
    plays = doc['play_count']

    # --- 2. Créer la description textuelle du diagramme (format Mermaid) ---
    diagram_source = f"""pie
    title Interactions pour "{title}"
    "Vues ({views})" : {views}
    "Lectures ({plays})" : {plays}
"""

    # --- 3. Envoyer la requête à l'API Kroki ---
    # Correction ici : utiliser /mermaid/svg au lieu de /graphviz/svg
    kroki_url = "https://kroki.io/mermaid/svg" # Endpoint pour Mermaid en SVG
    
    headers = {
        'Content-Type': 'text/plain'
    }
    
    try:
        response = requests.post(kroki_url, headers=headers, data=diagram_source, verify=False)
        
        if response.status_code == 200:
            # --- 4. Renvoyer l'image SVG ---
            from flask import Response
            return Response(response.content, mimetype='image/svg+xml')
        else:
            print(f"Erreur API Kroki : {response.status_code} - {response.text}")
            # Optionnel : Renvoyer un SVG d'erreur simple
            error_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="100">
                               <text x="10" y="50" font-family="Arial" font-size="16" fill="red">
                                   Erreur Kroki: {response.status_code}
                               </text>
                           </svg>"""
            return Response(error_svg, mimetype='image/svg+xml'), 500
            
    except requests.exceptions.RequestException as e:
        print(f"Erreur réseau vers Kroki : {e}")
        # Optionnel : Renvoyer un SVG d'erreur simple
        error_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="100">
                           <text x="10" y="50" font-family="Arial" font-size="16" fill="red">
                               Erreur réseau Kroki
                           </text>
                       </svg>"""
        return Response(error_svg, mimetype='image/svg+xml'), 500
# --- Fonction utilitaire pour gTTS ---
import sqlite3
from gtts import gTTS # Import local

def synthesize_speech(text, output_path, voice='Femme (fr)'):
    """Convertit le texte en audio (mp3) en utilisant gTTS avec une voix spécifiée."""
    try:
        # --- Validation et nettoyage du texte ---
        if not text or not text.strip():
            print("Erreur : Le texte fourni est vide ou invalide.")
            return False
        cleaned_text = text.strip()
        print(f"Texte à traiter (premiers 100 caractères): {cleaned_text[:100]}...")

        # --- Choix simplifié de la langue basé sur le "nom" de la voix ---
        # Note: gTTS de base ne permet pas un choix fin "Homme/Femme". 
        # On mappe nos options de sélection vers une langue de base.
        chosen_lang = 'fr' # Langue par défaut
        if 'Homme' in voice:
            # Simulation : on pourrait tenter une autre langue proche ou modifier slow, 
            # mais gTTS est limité. On reste sur 'fr'.
            print(f"Voix sélectionnée : {voice}. Utilisation de la langue '{chosen_lang}'. (Note : gTTS utilise souvent la même voix pour 'fr').")
        else: # Par défaut, Femme ou autre
            print(f"Voix sélectionnée : {voice} (considérée comme Femme). Utilisation de la langue '{chosen_lang}'.")

        # --- Création de l'objet gTTS ---
        # slow=False pour une vitesse normale
        # lang_check=False est souvent nécessaire pour éviter des erreurs strictes
        tts = gTTS(text=cleaned_text, lang=chosen_lang, slow=False, lang_check=False, pre_processor_funcs=[]) 
        
        # --- Sauvegarde du fichier audio ---
        tts.save(output_path)
        print(f"Audio généré et sauvegardé avec succès : {output_path}")
        return True
    except IndexError as ie: # Capture spécifique de l'erreur mentionnée
        print(f"Erreur d'index (IndexError) lors de la synthèse vocale avec gTTS : {ie}")
        # Afficher le texte peut aider à identifier le problème
        print(f"Texte qui a causé l'erreur (repr): {repr(text[:200])}") # Affiche les caractères spéciaux
        return False
    except Exception as e: # Capture de toutes les autres erreurs
        print(f"Erreur inattendue lors de la synthèse vocale avec gTTS : {type(e).__name__} - {e}")
        return False


# --- Point d'entrée de l'application ---
if __name__ == '__main__':
    # Démarre un thread pour ouvrir le navigateur
    threading.Thread(target=open_browser).start()
    
    # Démarre le serveur Flask en mode debug (utile pour le développement)
    app.run(debug=True, use_reloader=False) # use_reloader=False est important ici
    # Explication de use_reloader=False :
    # En mode debug, Flask redémarre automatiquement le script.
    # Cela exécuterait la fonction open_browser à chaque redémarrage,
    # ce qu'on ne veut pas. Ce paramètre désactive ce rechargement
    # automatique pour le lancement initial, mais le debug reste actif.
    # Si tu veux le reloader ET ouvrir le navigateur au tout premier lancement,
    # une logique un peu plus complexe est nécessaire, mais cela suffit pour commencer.