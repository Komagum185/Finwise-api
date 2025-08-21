import os
import django
from django.conf import settings
import shutil

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finwise.settings')  # Replace with your project name
django.setup()

# Get the base directory of the Django project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Function to delete the migrations folder
def delete_migrations_folder(app_name):
    migrations_dir = os.path.join(BASE_DIR, app_name, 'migrations')
    
    # Check if migrations directory exists and delete it
    if os.path.exists(migrations_dir) and os.path.isdir(migrations_dir):
        shutil.rmtree(migrations_dir)
        print(f'Deleted migrations directory for app {app_name}: {migrations_dir}')
    else:
        print(f'Migrations directory for app {app_name} does not exist.')

# Get all Django apps from the installed apps
def main():
    installed_apps = settings.INSTALLED_APPS
    for app in installed_apps:
        app_name = app.split('.')[-1]  # Get the app name
        delete_migrations_folder(app_name)

if __name__ == '__main__':
    main()

