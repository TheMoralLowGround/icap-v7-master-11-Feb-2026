from flask import Flask
from flask_cors import CORS
import sys

# Required to load robot modules from external scripts folder
sys.path.append('/scripts')

from app.definitions_extractor import init as definitions_extractor

app = Flask(__name__)
CORS(app)

#####
# configure module wise routes
####

definitions_extractor(app)