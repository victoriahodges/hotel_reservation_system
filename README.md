# Hotel Reservation System

Part of TM470 Final IT Project

Python application using Flask framework, REST API and SQLAlchemy.

## Setup environment

#### Check dependencies:

```
$ python --version
Python 3.11.6
```

#### Install pip 
https://packaging.python.org/en/latest/guides/installing-using-linux-tools/

```
$ sudo dnf install python3-pip python3-wheel

$ pip --version
pip 22.2.2
```

#### Install pipenv 
https://pipenv.pypa.io/en/latest/index.html

```
$ pip install pipenv --user

$ pipenv --version
pipenv, version 2023.12.1
```

Create and activate the virtual environment and spawn a shell within it
```
pipenv shell
```
Install packages
```
pipenv install [OPTIONS] [PACKAGES]...
```

## Creating Flask application

### Install Flask

```
$ pipenv install Flask
```

### Developing a hotel reservation application

The application builds upon steps from tutorial https://flask.palletsprojects.com/en/3.0.x/tutorial/

#### Initialise database
```
$ flask --app reservation_system init-db
```

#### Run app with debugger
```
$ flask --app reservation_system run --debug
```
