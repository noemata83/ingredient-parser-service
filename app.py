from flask import Flask, request, jsonify
from flask_cors import CORS
import pycrfsuite

from utils import parse_ingredient

application = Flask(__name__)
app = application

CORS(app)

@app.route('/')
def hello():
    return "Hello. Welcome to the Ingredient Phrase Tagger Service. To tag ingredient phrase, send a json object with an array of ingredient strings under a key of \"ingredients\" to /parse. Enjoy!"

@app.route('/parse', methods=['POST'])
def parse_ingredients():
    data = request.get_json()
    
    tagger = pycrfsuite.Tagger()
    tagger.open('static/trained_pycrfsuite')

    ingredient_sentences = data['ingredients']
    ingredients = []
    for ingredient_string in ingredient_sentences:
        ingredients.extend(parse_ingredient(ingredient_string, tagger))
    
    return jsonify({
        "ingredients": ingredients,
    })

if __name__ == "__main__":
    app.debug = True
    app.run()