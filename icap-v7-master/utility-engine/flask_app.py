from flask import Flask
from flask_cors import CORS

from app.address_parser import init as address_parser_init
from app.fuzzy_c import init as fuzzy_c_init

app = Flask(__name__)
CORS(app)

#####
# configure module wise routes
####

address_parser_init(app)
fuzzy_c_init(app)
