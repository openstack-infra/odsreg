odsreg - The OpenStack Design Summit session management system
==============================================================

odsreg is the Django app used for the OpenStack Design Summit
session proposal and scheduling.

It has the following features:

 * Session proposal
 * Session review
 * Ability to merge sessions and add a cover description
 * Drag-and-drop scheduling
 * Synchronization to sched.org event schedule
 * Launchpad SSO integration


Prerequisites
-------------

You'll need the following Python modules installed:
 - django (1.8+)
 - python-django-auth-openid

OR

If you are using pip with or without a venv,
you can use the following commands instead:
 - pip install django
 - pip install python-openid
 - pip install django-openid-auth


Configuration and Usage
-----------------------

Copy odsreg/local_settings.py.sample to odsreg/local_settings.py and change
settings there. In particular you should set DEBUG=True or ALLOWED_HOSTS.

Build migrations files:
./manage.py makemigrations cfp

Create empty database:
./manage.py migrate

Create a superuser:
./manage.py createsuperuser

Copy event.json.sample to event.json and edit the file to match
the event and topics you want to have. Then run:

./manage.py loadevent event.json

Then run a dev server using:
./manage.py runserver

When you have room layout, copy slots.json.sample to slots.json and edit
the file to match the rooms and time slots for each topic. Then run:

./manage.py loadslots slots.json
