# database.py
import sqlite3
import os

# Nom du fichier de la base de données
DATABASE = 'documents.db'

def get_db_connection():
    """Crée une connexion à la base de données SQLite."""
    conn = sqlite3.connect(DATABASE)
    # Permet d'accéder aux colonnes par leur nom
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialise la base de données et crée la table si elle n'existe pas."""
    with get_db_connection() as conn:
        # --- Mise à jour de la requête CREATE TABLE ---
        # Ajout de play_count avec une valeur par défaut de 0
        conn.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL DEFAULT 'Document sans titre',
                content TEXT NOT NULL,
                audio_file_path TEXT,
                view_count INTEGER DEFAULT 0,
                play_count INTEGER DEFAULT 0 -- Nouvelle colonne
            )
        ''')
        conn.commit()
        print("Base de données initialisée (mise à jour si nécessaire).")

def insert_document(slug, title, content, audio_file_path):
    """Insère un nouveau document dans la base de données."""
    with get_db_connection() as conn:
        # La requête INSERT reste la même car play_count a une valeur par défaut
        conn.execute(
            'INSERT INTO documents (slug, title, content, audio_file_path) VALUES (?, ?, ?, ?)',
            (slug, title, content, audio_file_path)
        )
        conn.commit()

def get_document_by_slug(slug):
    """Récupère un document par son slug."""
    with get_db_connection() as conn:
        doc = conn.execute(
            'SELECT * FROM documents WHERE slug = ?', (slug,)
        ).fetchone()
        return doc

def increment_view_count(slug):
    """Incrémente le compteur de vues pour un document."""
    with get_db_connection() as conn:
        conn.execute(
            'UPDATE documents SET view_count = view_count + 1 WHERE slug = ?',
            (slug,)
        )
        conn.commit()

# --- Nouvelle fonction ---
def increment_play_count(slug):
    """Incrémente le compteur de lectures (plays) pour un document."""
    with get_db_connection() as conn:
        conn.execute(
            'UPDATE documents SET play_count = play_count + 1 WHERE slug = ?',
            (slug,)
        )
        conn.commit()

def get_recent_documents(limit=10):
    """Récupère les 'limit' documents les plus récents."""
    with get_db_connection() as conn:
        # Trie par ID décroissant pour avoir les plus récents en premier
        docs = conn.execute(
            'SELECT slug, title, view_count, play_count FROM documents ORDER BY id DESC LIMIT ?',
            (limit,)
        ).fetchall()
        # Convertir les Row objects en dictionnaires pour une manipulation plus facile dans le template
        return [dict(doc) for doc in docs]

# Si ce fichier est exécuté directement, initialise la DB
if __name__ == '__main__':
    init_db()
