import argparse
import os
import server

controllerPath = server.root_directory + "/controllers"

# Function to create a controller
def create_controller(name):
    filename = f"{name}.py"
    newControllerFilePath = controllerPath + "/" + filename
    with open(newControllerFilePath, 'w') as f:
        f.write("from .Controller import Controller\n\n")
        f.write(f"class {name}(Controller):\n")
        f.write("    def __init__(self):\n")
        f.write("        super().__init__()\n")
        f.write("    pass\n")
    print(f"Controller '{filename}' successfully created.")

# Function to create a view
def create_view(name):
    filename = f"{name}.html"
    newViewFilePath = server.root_directory + "/" + filename
    with open(newViewFilePath, 'w') as f:
        f.write(f"<!-- Vue {name} -->\n")
    print(f"View '{filename}' successfully created.")

# Configuration de l'analyseur d'arguments
parser = argparse.ArgumentParser(description="Gestionnaire de création PWF")
parser.add_argument("command", choices=['create'], help="La commande à exécuter")
parser.add_argument("type", choices=['controller', 'view'], help="Le type de fichier à créer")
parser.add_argument("name", help="Le nom du fichier à créer")

# Analyse des arguments
args = parser.parse_args()

# Exécution des commandes
if args.command == 'create':
    if args.type == 'controller':
        create_controller(args.name)
    elif args.type == 'view':
        create_view(args.name)
