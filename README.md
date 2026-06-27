Flask SocketIO Games
Games with Flask SocketIO Web Interfaces
- Quizz
- Blind Test

# Installation
## export environement variables for Pip to get packages in a depot list
> export PIP_INDEX_URL="https://pypi.python.org/simple"

From work (not mandatory)  
> export ARTIFACTORY_RO_TOKEN=*************************

> export ARTIFACTORY_RO_USER=xduval

> export PIP_EXTRA_INDEX_URL="https://{ARTIFACTORY_RO_USER}:{ARTIFACTORY_RO_TOKEN}@artifactory.global.ingenico.com/artifactory/api/pypi/core-pypi/simple"

> export PIP_TRUSTED_HOST=artifactory.global.ingenico.com

## Installer l'environement virtuel python3.12 avec venv:
>python -m venv .venv312

>echo "*" > .venv312/.gitignore

>source .venv312/bin/activate

>python -m pip install --upgrade pip

### packages by packages
> python -m pip install Flask-SocketIO
> python -m pip install "qrcode[pil]"
> python -m pip install tinydb

### with requirements file
>pip install -r requirements312.txt

# Quizz
Lancer script:  
>python web_quizz_yt.py

# Blind Test
Lancer script:  
>python web_blind_test_ui_yt.py

## Arrêter l'environement virtuel venv:
>deactivate
