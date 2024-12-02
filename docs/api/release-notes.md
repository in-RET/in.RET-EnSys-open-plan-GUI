# Release Notes

## 0.02 Pre-Release (beta)
### Features
- Support configurationsfiles in two fileformats, JSON or Binary
- Support to directly submit data via JSON-Requests
- Automically solve energysystem via docker
- Added support for upload to the "Universitätsrechenzentrum Ilmenau" (login data is required!)
- Support uploading multiple Files at once also with both filetypes mixed

### Fixes
- Fixed loginmask for the UniRZ
- Splitted solving via docker / ssh in two files for better readability
- added constants.py for Filetypes, SSH-Addresses, Docker-Imagenames etc.

## 0.01 Pre-Release (alpha)
First implementation.