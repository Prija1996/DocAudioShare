# tts_engines/gtts_engine.py
from .base_engine import TTSEngine
from gtts import gTTS
import os

class GTTSEngine(TTSEngine):
    """Moteur TTS utilisant gTTS."""

    def synthesize(self, text: str, output_path: str, options: dict = None) -> bool:
        """
        Synthétise le texte en audio (mp3) en utilisant gTTS.

        Args:
            text (str): Le texte à convertir.
            output_path (str): Le chemin du fichier de sortie (.mp3).
            options (dict, optional): Options. Clés supportées :
                - 'voice' (str): 'Homme (fr)' ou 'Femme (fr)' (simulation).

        Returns:
            bool: True si la synthèse a réussi, False sinon.
        """
        try:
            if not text or not text.strip():
                print("Erreur : Le texte fourni est vide ou invalide.")
                return False
            cleaned_text = text.strip()
            print(f"Texte à traiter (premiers 100 caractères): {cleaned_text[:100]}...")

            # --- Choix simplifié de la langue basé sur le "nom" de la voix ---
            chosen_lang = 'fr' # Langue par défaut
            if options and 'voice' in options and 'Homme' in options['voice']:
                print(f"Voix sélectionnée : {options['voice']}. Utilisation de la langue '{chosen_lang}'. (Note : gTTS utilise souvent la même voix pour 'fr').")
            else:
                print(f"Voix sélectionnée : {options.get('voice', 'Femme (fr)')} (considérée comme Femme). Utilisation de la langue '{chosen_lang}'.")

            # --- Création de l'objet gTTS ---
            tts = gTTS(text=cleaned_text, lang=chosen_lang, slow=False, lang_check=False, pre_processor_funcs=[])
            
            # --- Sauvegarde du fichier audio ---
            tts.save(output_path)
            print(f"Audio généré et sauvegardé avec succès : {output_path}")
            return True
        except Exception as e: # Capture de toutes les erreurs
            print(f"Erreur inattendue lors de la synthèse vocale avec gTTS : {type(e).__name__} - {e}")
            return False

# Instance singleton pour utilisation dans l'application
gtts_engine = GTTSEngine()
