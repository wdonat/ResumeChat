import os

from app import create_app

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
app.secret_key = 'twas brillig and the slithy toves'
