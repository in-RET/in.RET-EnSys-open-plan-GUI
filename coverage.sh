#!/bin/bash
coverage erase
coverage run -a --branch app/manage.py runserver test
coverage report
coverage xml