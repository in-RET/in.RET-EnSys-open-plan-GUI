!!! info
    If you find some bugs don't hesitate to mail at <a href="mailto:ensys@hs-nordhausen.de">Hochschule Nordhausen</a>

# Short description
The 'ensys'-project contains of two main parts. A graphical user interface, which is built with the python package 'Django' 
and an api which is built with 'FastAPI'.

On our github page, see right corner above, is the code for both parts as one repository downloadable.

# Folder structure
Open these an you find a number of folders.

## .run
Configurations for JetBrains PyCharm.

## api
Subfolder which contains the FastAPI code.

## app
Subfolder which contains the Django-Webframework Code and templates for the entire Frontend.

## docs
Contains these documentation.

## proxy
Configuration files for the proxy used in production.

## requirements
Contains the file with all requirements and the prebuild backend-package.

## After first start

### .venv
Contains the virtual environment for python. 
Version 3.11.

### data
Storage folder which is automatically created for storage of simulations data.

This folder is also used in Debugging for the database and pgadmin files.