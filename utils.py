import re

# Utility functions adapted for Python 3.6.5 from the New York Times 
# Ingredient Phrase Tagger Project: https://github.com/NYTimes/ingredient-phrase-tagger

def singularize(word):
    """
    A poor replacement for the pattern.en singularize function, but ok for now.
    """

    units = {
        "cups": u"cup",
        "tablespoons": u"tablespoon",
        "teaspoons": u"teaspoon",
        "pounds": u"pound",
        "ounces": u"ounce",
        "cloves": u"clove",
        "sprigs": u"sprig",
        "pinches": u"pinch",
        "bunches": u"bunch",
        "slices": u"slice",
        "grams": u"gram",
        "heads": u"head",
        "quarts": u"quart",
        "stalks": u"stalk",
        "pints": u"pint",
        "pieces": u"piece",
        "sticks": u"stick",
        "dashes": u"dash",
        "fillets": u"fillet",
        "cans": u"can",
        "ears": u"ear",
        "packages": u"package",
        "strips": u"strip",
        "bulbs": u"bulb",
        "bottles": u"bottle"
    }

    if word in units.keys():
        return units[word]
    else:
        return word

def isCapitalized(token):
    """
    Returns true if a given token starts with a capital letter.
    """
    return re.match(r'^[A-Z]', token) is not None

def lengthGroup(actualLength):
    """
    Buckets the length of the ingredient into 6 buckets.
    """
    for n in [4, 8, 12, 16, 20]:
        if actualLength < n:
            return str(n)

    return "X"

def insideParenthesis(token, tokens):
    """
    Returns true if the word is inside parenthesis in the phrase.
    """
    if token in ['(', ')']:
        return True
    else:
        line = " ".join(tokens)
        return re.match(r'.*\(.*'+re.escape(token)+'.*\).*',  line) is not None


def smartJoin(words):
    """
    Joins list of words with spaces, but is smart about not adding spaces
    before commas.
    """

    input = " ".join(words)

    # replace " , " with ", "
    input = input.replace(" , ", ", ")

    # replace " ( " with " ("
    input = input.replace("( ", "(")

    # replace " ) " with ") "
    input = input.replace(" )", ")")

    return input


def clumpFractions(s):
    """
    Replaces the whitespace between the integer and fractional part of a quantity
    with a dollar sign, so it's interpreted as a single token. The rest of the
    string is left alone.

        clumpFractions("aaa 1 2/3 bbb")
        # => "aaa 1$2/3 bbb"
    """
    return re.sub(r'(\d+)\s+(\d)/(\d)', r'\1$\2/\3', s)

def unclump(s):
    """
    Replacess $'s with spaces. The reverse of clumpFractions.
    """
    return re.sub(r'\$', " ", s)

def cleanUnicodeFractions(s):
    """
    Replace unicode fractions with ascii representation, preceded by a
    space.

    "1\x215e" => "1 7/8"
    """

    fractions = {
        u'\x215b': '1/8',
        u'\x215c': '3/8',
        u'\x215d': '5/8',
        u'\x215e': '7/8',
        u'\x2159': '1/6',
        u'\x215a': '5/6',
        u'\x2155': '1/5',
        u'\x2156': '2/5',
        u'\x2157': '3/5',
        u'\x2158': '4/5',
        u'\xbc': ' 1/4',
        u'\xbe': '3/4',
        u'\x2153': '1/3',
        u'\x2154': '2/3',
        u'\xbd': '1/2',
    }

    for f_unicode, f_ascii in fractions.items():
        s = s.replace(f_unicode, ' ' + f_ascii)

    return s

def getFeatures(token, index, tokens):
    """
    Returns a list of features for a given token.
    """
    length = len(tokens)

    return [
        ("I%s" % index),
        ("L%s" % lengthGroup(length)),
        ("Yes" if isCapitalized(token) else "No") + "CAP",
        ("Yes" if insideParenthesis(token, tokens) else "No") + "PAREN"
    ]

def tokenize(s):
    """
    """
    american_units = ['cup', 'tablespoon', 'teaspoon', 'pound', 'ounce', 'quart', 'pint']
    
    for unit in american_units:
        s = s.replace(unit + '/', unit + ' ')
        s = s.replace(unit + 's/', unit + 's ')
        
    return [token for token in re.split(r'([,\(\)])?\s*', clumpFractions(s)) if token is not None]

def get_sentence_features(sent):
    """ Gets the features of a sentence """
    sent_tokens = tokenize(cleanUnicodeFractions(sent))
    
    sent_features = []
    for i, token in enumerate(sent_tokens):
        token_features = [token]
        token_features.extend(getFeatures(token, i+1, sent_tokens))
        sent_features.append(token_features)
    return sent_features

def sent2tokens(sent):
    return [word[0] for word in sent]

def format_ingredient_output(tagger_output, display=False):
    """Formats the tagger output into a more convenient dictionary"""
    data = [{}]
    display = [[]]
    prevTag = None
    for (token, tag) in tagger_output:
        # turn B-NAME/123 back into "name"
        tag = re.sub(r'^[BI]\-', "", tag).lower()
        
        # ---- DISPLAY ----
        # build a structure which groups each token by its tag, so we can
        # rebuild the original display name later.
        
        if prevTag != tag:
            display[-1].append((tag, [token]))
            prevTag = tag
        else:
            display[-1][-1][1].append(token)
            #               ^- token
            #            ^---- tag
            #        ^-------- ingredient

            # ---- DATA ----
            # build a dict grouping tokens by their tag

            # initialize this attribute if this is the first token of its kind
        if tag not in data[-1]:
            data[-1][tag] = []
            
        # HACK: If this token is a unit, singularize it so Scoop accepts it.
        if tag == "unit":
            token = singularize(token)

        token = unclump(token)    
        data[-1][tag].append(token)
    
    # reassemble the output into a list of dicts.
    output = [
        dict([(k, smartJoin(tokens)) for k, tokens in ingredient.items()])
        for ingredient in data
        if len(ingredient)
    ]

    # Add the raw ingredient phrase
    for i,_ in enumerate(output):
        output[i]["input"] = unclump(smartJoin(
            [" ".join(tokens) for k, tokens in display[i]]))

    return output


def parse_ingredient(sent, tagger):
    """ingredient parsing logic"""
    sentence_features = get_sentence_features(sent)
    tags = tagger.tag(sentence_features)
    tagger_output = list(zip(sent2tokens(sentence_features), tags))
    parsed_ingredient =  format_ingredient_output(tagger_output)
    if parsed_ingredient:
        parsed_ingredient[0]['name'] = parsed_ingredient[0].get('name','').strip('.')
    return parsed_ingredient