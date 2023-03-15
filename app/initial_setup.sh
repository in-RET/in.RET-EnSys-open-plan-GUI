#!/usr/local/bin/python
python manage.py compilemessages
python manage.py makemigrations users projects dashboard && \
python manage.py migrate && \
#python manage.py update_assettype && \
python manage.py loaddata 'fixtures/multivector_fixture_inret.json' && \
python manage.py collectstatic --no-input
