#!/bin/bash
coverage erase
#coverage run -a --branch app/manage.py runserver test
coverage report
coverage xml

rm -r tmp
rm -r dumps
rm -r logs