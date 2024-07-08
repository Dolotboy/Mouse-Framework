import argparse
import os
import shutil
import server

def create_controller(name):
    controllers_dir = os.path.join(server.root_directory, 'controllers')
    
    file_name = f"{name}.py"
    file_path = os.path.join(controllers_dir, file_name)

    if os.path.exists(file_path):
        print(f"Controller {file_name} already exists.")
    else:
        with open(file_path, 'w') as f:
            f.write(f"# {name.capitalize()} Controller\n\n")
            f.write("class {}Controller:\n".format(name.capitalize()))
            f.write("    def __init__(self):\n")
            f.write("        pass\n")
        print(f"Controller {file_name} created.")

def main():
    parser = argparse.ArgumentParser(description='Create a new controller.')
    parser.add_argument('name', type=str, help='The name of the controller.')
    args = parser.parse_args()
    create_controller(args.name)

if __name__ == '__main__':
    main()