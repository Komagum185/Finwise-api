import os
import django
from django.conf import settings

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finwise.settings')  # Replace with your project name
django.setup()

# Get the base directory of the Django project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Function to create __init__.py in migrations folder
def create_migrations_init(app_name):
    migrations_dir = os.path.join(BASE_DIR, app_name, 'migrations')
    
    # Create migrations directory if it does not exist
    if not os.path.exists(migrations_dir):
        os.makedirs(migrations_dir)
        print(f'Created migrations directory for app {app_name}: {migrations_dir}')

    init_file_path = os.path.join(migrations_dir, '__init__.py')
    if not os.path.exists(init_file_path):
        with open(init_file_path, 'w') as f:
            f.write('# This file is required to make Django treat the directory as a package.\n')
        print(f'Created {init_file_path}')
    else:
        print(f'{init_file_path} already exists.')

# Get all Django apps from the installed apps
def main():
    installed_apps = settings.INSTALLED_APPS
    for app in installed_apps:
        app_name = app.split('.')[-1]  # Get the app name
        create_migrations_init(app_name)

if __name__ == '__main__':
    main()

