# LITReview

The project is a webapp which enables a community of users to publish reviews on books and literature on demand. Moreover, the users can follow or unfollow other users.

## Setup

### 1. Clone the Repository

First, clone this repository to your local machine. Then navigate inside the folder litreview and open command prompt from inside the cloned repository

### 2. Create Virtual Environment

To create virtual environment, install virtualenv package of python and activate it by following command on terminal:

```python
python -m venv env
Windows: env\Scripts\activate.bat

Powershell: env\Scripts\activate

Unix/MacOS: source env/bin/acivate
```

### 3. Requirements

To install required python packages, copy requirements.txt file and then run following command on terminal:

```python
pip install requirements.txt
```

### 4. Start Server

On the terminal enter following command to start the server:

```python
python manage.py runserver
```

### 5. Start the Webapp

To start the webapp on localhost, enter following URL in the web browser:

https://127.0.0.1:8000/
