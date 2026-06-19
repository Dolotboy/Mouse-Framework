import os

def display_view(view_name, root_directory):
    file_path = os.path.join(root_directory, 'views', view_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le fichier {file_path} n'existe pas.")
    
    with open(file_path, 'r') as f:
        return f.read()
