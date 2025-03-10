# LITReview

The project is a webapp which enables a community of users to publish reviews on books and literature on demand. Moreover, the user can follow, be followed or block other members.

## Fonctionnalités de l'application
The application presents three main use cases:

 - The publication of book or article reviews;
 - The request for criticism on a particular book or article;
 - Viewing reviews of members followed.

## Setup
### Prérequis
Python must be installed beforehand.

If you work in a Linux or MacOS environment: Python is normally already installed. To check, open your terminal and type:
```bash
python --version or python3 --version
```
If Python is not installed, you can download it at the following address: [Download Python3](https://www.python.org/downloads)

You will also need the pip Python package installer which is included by default if you have a Python version >= 3.4. You can check that it is available through your command line, by entering: 
```bash
pip --version
```
You will also need Git to clone the application on your computer. Check your installation by typing
```bash
git --version Otherwise
```
choose and download the version of Git that corresponds to your installation: MacOS, Windows or Linux/Unix by clicking on the following link: [Download git](https://git-scm.com/downloads) Then run the file you just downloaded. Press Next at each window and then Install. During installation, leave all the default options as they work well. Git Bash is the interface for using Git on the command line.

### 1. Clone the Repository

First, open the command prompt in the folder where you want to drop the clone.

clone this repository to your local machine. 

```bash
git clone https://github.com/Mikael2983/OC_P9_Develop_web_application_using_Django.git
```
Then navigate inside the folder OC_P9_Develop_web_application_using_Django

```bash
cd OC_P9_Develop_web_application_using_Django
```

### 2. Create Virtual Environment

To create virtual environment, install virtualenv package of python and activate it by following command on terminal:

```bash
python -m venv env
```
for windows:
```bash
env\Scripts\activate
```
for Unix/MacOS :
```bash
source env/bin/acivate
```


### 3. Requirements

To install required python packages, copy requirements.txt file and then run following command on terminal:

```bash
pip install -r requirements.txt
```
then access the project directory

```bash
cd LITRevu
```

### 4. Start Server

On the terminal enter following command to start the server:

```bash
python manage.py runserver
```

### 5. Start the Webapp

To start the webapp on localhost, enter following URL in the web browser:

http://127.0.0.1:8000/
