from flask import Flask
from flask_cors import CORS

from app.ocrengine_api import init as ocrengine_api_init

app = Flask(__name__)
CORS(app)

#####
# configure module wise routes
####

ocrengine_api_init(app)
