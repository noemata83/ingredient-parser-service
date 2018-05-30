from flask import Flask, request, jsonify
from nltk.tokenize import PunktSentenceTokenizer
import pycrfsuite

from utils import *


app = Flask(__name__)

@app.route('/parse', methods=['POST'])
def parse_ingredients():
    data = request.get_json()
    
    tagger = pycrfsuite.Tagger()
    tagger.open('data/trained_pycrfsuite')

    ingredient_sentences = data['ingredients']
    ingredients = []
    for ingredient_string in ingredient_sentences:
        ingredients.extend(parse_ingredient(ingredient_string, tagger))
    
    return jsonify({
        "ingredients": ingredients,
    })