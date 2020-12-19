# iQuISE Website

This is a Django driven backend with html inspired from templates by @ajlkn.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.
There will be a few environment variables that aren't tracked by git, that contain sensitive information. This file is loaded directly into the root namespace of iquise/settings.py.

### Prerequisites
Currently only supports python 2 (specifically running with 2.7).

Django (tested in version 1.11.15) and dependencies.

django-easy-audit - a nice light-weight, third-party auditing tool: https://github.com/soynatan/django-easy-audit

Pillow - image resizing (tested with 5.2.0, but this is a pretty stable package)
```
pip install django==1.11.15
pip install django-easy-audit==1.0
pip install Pillow
```
Navigate to the root of the repository, and create a default iquise/.env (json) file that contains the following lines:
```
{
    "DATABASES":{
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "{{os.path.join(BASE_DIR,'iquisedb_dev.sqlite3')}}"
        }
    },
    "ALLOWED_HOSTS":["localhost","18.62.21.215"],
    "DEBUG": true
}
```
Note, you can also use a mysql server as well - reference django docs for configuration.

### Installing

Navigate to the root of the repository
Make sure we are in DEBUG mode by making sure the iquise/.env file has the line
```
"DEBUG": true
```
Migrate the model schema to a sqlite3 database
```
python manage.py makemigrations website meetings
python manage.py migrate
```
Add a superuser (interactively make a username, email and password)
```
python manage.py createsuperuser
```
Add a group called "exec", used in the Auth User model upon signal
```
python create_exec_group.py
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
ALLOWED_HOSTS = ['localhost', 'YOUR PUBLIC IP']
...
```
Don't forget to deactivate debug mode in iquise/.env:
```
"DEBUG": false
```
Then start the dev server with an insecure flag (binding to all interfaces):
### THIS IS NOT GUARANTEED TO BE SECURE
```
python manage.py runserver 0.0.0.0:9000 --insecure
```
The .gitignore file is set to ignore "iquise/static/admin" such that it is safe to call collect those admin files:
```
python manage.py collectstatic
```
This should be done on the production server directly.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
