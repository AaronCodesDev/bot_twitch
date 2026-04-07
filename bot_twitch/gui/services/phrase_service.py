import os
import re

class PhraseService:
    """Servicio para gestión de frases optimizado"""
    
    def get_categories(self, file_path: str):
        """Busca las variables del archivo filtrando las dinámicas"""
        try:
            # Estas son las que NO queremos que aparezcan nunca en la App
            EXCLUIR = [
                "FRASES_POSICION", 
                "FRASES_LASTLAP", 
                "IRATING_TROLL", 
                "IRATING_FRASES",
                "i", "random", "frase"
            ]
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Buscamos cualquier VARIABLE = [ (independientemente de los espacios)
                # El regex ahora es más permisivo: ^(\w+) busca el nombre al inicio de línea
                found = re.findall(r'^(\w+)\s*=\s*\[', content, re.MULTILINE)
                
                # Filtramos las que están en la lista negra
                categories = [cat for cat in found if cat not in EXCLUIR]
                
                print(f"Categorías detectadas en {os.path.basename(file_path)}: {categories}")
                return categories
                
        except Exception as e:
            print(f"Error en get_categories: {e}")
            return []
    
    def load_phrases(self, file_path: str, category: str):
        """Carga las frases de la lista seleccionada"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Buscamos el contenido dentro de los corchetes de esa categoría
            pattern = rf'{re.escape(category)}\s*=\s*\[([\s\S]*?)\]'
            match = re.search(pattern, content)
            
            if match:
                phrases_text = match.group(1)
                # Buscamos todo lo que esté entre " " o ' '
                raw_phrases = re.findall(r'["\']([\s\S]*?)["\']', phrases_text)
                
                # Limpiamos saltos de línea para que no se vea mal en la App
                return [p.replace('\n', ' ').strip() for p in raw_phrases if p.strip()]
            return []
        except Exception as e:
            print(f"Error en load_phrases: {e}")
            return []

    def save_phrases(self, file_path: str, category: str, phrases: list):
        """Guarda las frases respetando el formato del archivo"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Guardamos con comillas dobles para que los 'hola' no rompan nada
            formatted = ',\n    '.join([f'"{p}"' for p in phrases])
            
            # Reemplazamos solo el bloque de la lista específica
            pattern = rf'({re.escape(category)}\s*=\s*\[)[\s\S]*?(\])'
            replacement = rf'\1\n    {formatted}\n\2'
            
            new_content = re.sub(pattern, replacement, content)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True
        except Exception as e:
            print(f"Error en save_phrases: {e}")
            return False