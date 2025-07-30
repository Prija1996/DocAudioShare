# tts_engines/base_engine.py
from abc import ABC, abstractmethod

class TTSEngine(ABC):
    """Classe de base abstraite pour les moteurs TTS."""

    @abstractmethod
    def synthesize(self, text: str, output_path: str, options: dict = None) -> bool:
        """
        Synthétise le texte en audio et le sauvegarde.

        Args:
            text (str): Le texte à convertir.
            output_path (str): Le chemin du fichier de sortie (.mp3).
            options (dict, optional): Options spécifiques au moteur (voix, vitesse, etc.).

        Returns:
            bool: True si la synthèse a réussi, False sinon.
        """
        pass
