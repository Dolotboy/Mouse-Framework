import os
import shutil

def main():
    current_dir = os.path.abspath(os.path.curdir)
    
    # Define source and destination for the files
    package_root = os.path.dirname(__file__)
    files_to_copy = ['.env.example', '.gitignore', 'server.py']

    # Create necessary directories
    os.makedirs(os.path.join(current_dir, 'web/controllers'), exist_ok=True)
    os.makedirs(os.path.join(current_dir, 'web/routes'), exist_ok=True)
    os.makedirs(os.path.join(current_dir, 'web/templates'), exist_ok=True)
    os.makedirs(os.path.join(current_dir, 'pckg_commands'), exist_ok=True)

    # Copy files to the root of the project directory
    for file in files_to_copy:
        shutil.copy(os.path.join(package_root, file), current_dir)

    print("Project structure created successfully.")

if __name__ == '__main__':
    main()
