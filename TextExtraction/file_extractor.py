import os
import re
import fitz  
import pytesseract  
from PIL import Image  

UPLOAD_FOLDER = 'uploads/'

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'png', 'jpeg', 'jpg', 'gif'}

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(pdf_file)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

# Function to extract text from images using OCR
def extract_text_from_image(image_file):
    image = Image.open(image_file)
    text = pytesseract.image_to_string(image)
    return text

def classify_sections(text):
    sections = []
    current_section = None
    current_subsection = None
    current_entity = None
    parent_stack = []

    lines = text.splitlines()

    section_pattern = re.compile(r'^Section \d+(\.\d+)*')
    subsection_pattern = re.compile(r'^\(\w+\)')
    number_pattern = re.compile(r'^\d+\.')
    alphabet_pattern = re.compile(r'^[a-zA-Z]\.')
    stage_pattern = re.compile(r'^\*\*\*.*\*\*\*')
    rule_pattern = re.compile(r'^\_\_\_.*\_\_\_')

    for line in lines:
        line = line.strip()

        # Check for new entities
        if section_pattern.match(line):
            # Save previous entity if exists
            save_previous_entity(current_entity, current_section, current_subsection)

            # Start new section
            current_section = {'title': line, 'content': [], 'type': 'section'}
            current_entity = current_section
            sections.append(current_section)

        elif number_pattern.match(line):
            # Save previous entity if exists
            save_previous_entity(current_entity, current_section, current_subsection)

            # Start new number
            current_entity = {'title': line, 'content': [], 'type': 'number'}

            # Determine parent-child relationship
            determine_parent_child_relationship(parent_stack, current_entity, sections)

        elif alphabet_pattern.match(line) or \
             stage_pattern.match(line) or \
             rule_pattern.match(line) or \
             subsection_pattern.match(line):
            # Save previous entity if exists
            save_previous_entity(current_entity, current_section, current_subsection)

            # Start new entity
            entity_type = determine_entity_type(line, alphabet_pattern, stage_pattern, rule_pattern, subsection_pattern)
            current_entity = {'title': line, 'content': [], 'type': entity_type}

            # Determine parent-child relationship
            determine_parent_child_relationship(parent_stack, current_entity, sections)

        elif current_entity:
            # Add content to current entity
            current_entity['content'].append(line)

    # Save the last entity
    save_previous_entity(current_entity, current_section, current_subsection)

    return sections

def save_previous_entity(current_entity, current_section, current_subsection):
    if current_entity:
        if current_section:
            current_section['content'].append(current_entity)
        elif current_subsection:
            current_subsection['content'].append(current_entity)

def determine_parent_child_relationship(parent_stack, current_entity, sections):
    if parent_stack:
        parent_stack[-1]['content'].append(current_entity)
    else:
        sections.append(current_entity)

def determine_entity_type(line, alphabet_pattern, stage_pattern, rule_pattern, subsection_pattern):
    if alphabet_pattern.match(line):
        return 'alphabet'
    elif stage_pattern.match(line):
        return 'stage'
    elif rule_pattern.match(line):
        return 'rule'
    elif subsection_pattern.match(line):
        return 'subsection'
    
    return 'unknown'