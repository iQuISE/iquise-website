# iQuISE Website

This is a Django driven backend with html inspired from templates by @ajlkn.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

Django (tested in version 1.11.15) and dependencies.
```
pip install django
```

### Installing

Navigate to the root of the repository
Make sure we are in DEBUG mode
```
vim iquise/settings.py
```
and make sure the line with "DEBUG=" is set to True
```
...
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost',...]
...
```
Migrate the model schema to a sqlite3 database
```
python manage.py makemigrations
python manage.py migrate
```
Add a superuser (interactively make a username, email and password)
```
python manage.py createsuperuser
```
Add a group called "leadership", used in the Auth User model upon signal
```
python create_leadership_group.py
```
Run the built-in dev server
```
python manage.py runserver localhost:8080
```
Now, you can use the web interface to add/edit Users, Presentations, etc.

For more options (e.g. using existing database, resetting migrations), see:
https://simpleisbetterthancomplex.com/tutorial/2016/07/26/how-to-reset-migrations.html

## Running the tests

Open your browser, and navigate to localhost:8080
localhost:8080/admin to go directly to the admin site
You will need to login with the superuser first, but once you make another user you will be able to login that way

## Deployment

See Django documentation on deployment.
https://docs.djangoproject.com/en/2.1/howto/deployment/

For a quick and dirty test, you can run it with the Django dev server:
```
...
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['localhost', 'YOUR PUBLIC IP']
...
```
Then start the dev server with an insecure flag (binding to all interfaces):
### THIS IS NOT GUARANTEED TO BE SECURE
```
python manage.py runserver 0.0.0.0:9000 --insecure
```
## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
