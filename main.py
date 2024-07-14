import os
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
from TextHighlight import file_highlighter
from TextExtraction import file_extractor
from TextCompare import file_compare

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = file_extractor.UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def home():
    return render_template('homePage.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files or 'template' not in request.files:
            return render_template('index.html', error='Please upload both files')

        file = request.files['file']
        template = request.files['template']

        if file.filename == '' or template.filename == '':
            return render_template('index.html', error='Please select both files')

        if file and file_extractor.allowed_file(file.filename) and template and file_extractor.allowed_file(template.filename):
            filename = secure_filename(file.filename)
            template_filename = secure_filename(template.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            template_path = os.path.join(app.config['UPLOAD_FOLDER'], template_filename)
            file.save(file_path)
            template.save(template_path)

            if filename.lower().endswith('.pdf'):
                extracted_text = file_extractor.extract_text_from_pdf(file_path)
            elif filename.lower().endswith(('.png', '.jpeg', '.jpg', '.gif')):
                extracted_text = file_extractor.extract_text_from_image(file_path)
            else:
                return render_template('index.html', error='Unsupported file format')

            if template_filename.lower().endswith('.pdf'):
                template_text = file_extractor.extract_text_from_pdf(template_path)
            elif template_filename.lower().endswith(('.png', '.jpeg', '.jpg', '.gif')):
                template_text = file_extractor.extract_text_from_image(template_path)
            else:
                return render_template('index.html', error='Unsupported template file format')

            classified_sections = file_extractor.classify_sections(extracted_text)
            template_sections = file_extractor.classify_sections(template_text)

            similarity_score, deviation_score, missing_content, additional_content, modified_content = file_compare.compare_contract_with_template(extracted_text, template_text)

            highlighted_text, highlighted_entities, highlighted_words, entity_mappings = file_highlighter.highlight_information_and_extract_entities(extracted_text, classified_sections)
            highlighted_template_text, highlighted_template_entities, highlighted_template_words, template_entity_mappings = file_highlighter.highlight_information_and_extract_entities(template_text, template_sections)

            # Ensure entity_mappings and template_entity_mappings are dictionaries
            if not isinstance(entity_mappings, dict):
                entity_mappings = {}
            if not isinstance(template_entity_mappings, dict):
                template_entity_mappings = {}

            return render_template('index.html', classified_sections=classified_sections, highlighted_text=highlighted_text, highlighted_entities=highlighted_entities, highlighted_words=highlighted_words,
                                   template_sections=template_sections, highlighted_template_text=highlighted_template_text, highlighted_template_entities=highlighted_template_entities, highlighted_template_words=highlighted_template_words,
                                   entity_mappings=entity_mappings, template_entity_mappings=template_entity_mappings, deviation_score=(similarity_score, deviation_score), additional_content=additional_content, missing_content=missing_content, 
                                   modified_content=modified_content)

        return render_template('index.html', error='File upload failed')

    return render_template('index.html')



if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
