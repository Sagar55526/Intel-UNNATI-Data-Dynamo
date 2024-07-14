import os
import re
import spacy
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import difflib

nlp = spacy.load("en_core_web_sm")
stopwords = spacy.lang.en.stop_words.STOP_WORDS

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def preprocess_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_entities(text):
    doc = nlp(text)
    entities = {}
    
    # Use spaCy's NER
    for ent in doc.ents:
        if ent.label_ in ['PERSON', 'ORG', 'GPE', 'DATE', 'MONEY']:
            entities[ent.text] = ent.label_
    
    # Use regex for address patterns
    address_pattern = re.compile(r'\b(\d+\s+)?(?:[A-Za-z0-9]+[ \t]+)?(?:[A-Za-z0-9]+[ \t]+)*(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Parkway|Pkwy|Place|Pl)\b')
    addresses = address_pattern.findall(text)
    
    for address in addresses:
        entities[address] = 'ADDRESS'
    
    return entities

def remove_stopwords_and_normalize(text):
    # Remove stopwords and normalize text
    doc = nlp(text)
    tokens = [token.text.lower() for token in doc if not token.is_stop]
    return ' '.join(tokens)

def calculate_cosine_similarity(template_entities, contract_entities):
    vectorizer = CountVectorizer().fit_transform([' '.join(template_entities), ' '.join(contract_entities)])
    vectors = vectorizer.toarray()
    
    similarity = cosine_similarity(vectors)
    return similarity[0][1]

def find_missing_content(template_entities, contract_entities):
    missing_content = {}

    for entity, label in template_entities.items():
        if entity not in contract_entities:
            missing_content[entity] = label

    return missing_content

def find_additional_content(template_entities, contract_entities):
    additional_content = {}

    for entity, label in contract_entities.items():
        if entity not in template_entities:
            additional_content[entity] = label

    return additional_content

def get_differences(template_text, contract_text):
    differ = difflib.Differ()
    diff = list(differ.compare(template_text.splitlines(), contract_text.splitlines()))
    
    modified_content = [line[2:] for line in diff if line.startswith('+ ')]
    return modified_content

def compare_contract_with_template(contract_text, template_text):
    contract_text = preprocess_text(contract_text)
    template_text = preprocess_text(template_text)
    
    contract_text_clean = remove_stopwords_and_normalize(contract_text)
    template_text_clean = remove_stopwords_and_normalize(template_text)
    
    contract_entities = extract_entities(contract_text_clean)
    template_entities = extract_entities(template_text_clean)

    missing_content = find_missing_content(template_entities, contract_entities)
    additional_content = find_additional_content(template_entities, contract_entities)

    # Adjust contract_entities by removing missing_content
    adjusted_contract_entities = {entity: label for entity, label in contract_entities.items() if entity not in missing_content}

    # Calculate cosine similarity with the adjusted contract entities
    similarity_score = calculate_cosine_similarity(template_entities.keys(), adjusted_contract_entities.keys())

    template_text_str = "\n".join(template_text_clean) if isinstance(template_text_clean, list) else template_text_clean
    contract_text_str = "\n".join(contract_text_clean) if isinstance(contract_text_clean, list) else contract_text_clean

    differences = get_differences(template_text_str, contract_text_str)

    deviation_score = len(missing_content) + len(additional_content)

    return similarity_score, deviation_score, missing_content, additional_content, differences

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        file = request.files['file']
        template = request.files['template']
        
        if file and allowed_file(file.filename) and template and allowed_file(template.filename):
            filename = secure_filename(file.filename)
            template_filename = secure_filename(template.filename)
            
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            template_path = os.path.join(app.config['UPLOAD_FOLDER'], template_filename)
            
            file.save(file_path)
            template.save(template_path)
            
            with open(file_path, 'r') as f:
                contract_text = f.read()
            
            with open(template_path, 'r') as f:
                template_text = f.read()
            
            similarity_score, deviation_score, missing_content, additional_content, differences = compare_contract_with_template(contract_text, template_text)
            
            return render_template('index.html', similarity_score=similarity_score, deviation_score=deviation_score,
                                   missing_content=missing_content, additional_content=additional_content, differences=differences)
    
    return render_template('index.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app.run(debug=True)
