set -o allexport
source ../local.env
set +o allexport

python manage.py migrate
python manage.py collectstatic --no-input
python manage.py loaddata 'fixtures/fixture.json'
python manage.py runserver 9004