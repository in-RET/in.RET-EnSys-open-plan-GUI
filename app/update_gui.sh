#!/usr/local/bin/python
python manage.py compilemessages
python manage.py makemigrations users projects dashboard && \
python manage.py migrate && \
python manage.py collectstatic && \
echo 'Updated the open-plan GUI app successfully!!'
