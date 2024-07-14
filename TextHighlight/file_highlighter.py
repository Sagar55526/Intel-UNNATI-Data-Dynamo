import re
import spacy

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

def highlight_information_and_extract_entities(text, sections):
    # Define patterns for matching various key terms
    date_pattern = r'\b(?:\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\b(?:\d{1,2}(?:st|nd|rd|th)?\s(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s\d{4}))\b'
    confidential_pattern = r'\b(?:confidential|non-disclosure|non disclosure|proprietary|sensitive)\b'
    party_names_pattern = r'\b(?:CLIENT|SERVICE PROVIDER|PARTY|PARTIES|AFFILIATE|COMPANY|EMPLOYEE|EMPLOYER|SELLER|BUYER|LESSOR|LESSEE)\b'
    financial_info_pattern = r'\b(?:Amount|Payment Schedule|Start Date|End Date|Description of Services|Fee|Compensation|Rate|Revenue|Cost|Price|Payment Terms|Invoice)\b'
    agreement_terms_pattern = r'\b(?:Agreement|Contract|Term|Duration|Effective Date|Termination|Renewal|Amendment|Jurisdiction|Governing Law)\b'
    contact_info_pattern = r'\b(?:Email|Phone|Contact|Address|Fax)\b'
    signatures_pattern = r'\b(?:Signature|Signed by|Date Signed|Witness)\b'
    amount_pattern = r'\b(?:[₹$€£¥]\s?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\b|\b(?:\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\s?[₹$€£¥]?)\b'
    participant_pattern = r'\bParticipant:\s*(Mr\.|Ms\.|Mrs\.)\s*[A-Za-z]+\s+[A-Za-z]+\s+[A-Za-z]+\b'

    # Apply the patterns to the text to highlight matches
    highlighted_text = re.sub(date_pattern, r'<mark>\g<0></mark>', text, flags=re.IGNORECASE)
    highlighted_text = re.sub(confidential_pattern, r'<mark>\g<0></mark>', highlighted_text, flags=re.IGNORECASE)
    highlighted_text = re.sub(party_names_pattern, r'<mark>\g<0></mark>', highlighted_text, flags=re.IGNORECASE)
    highlighted_text = re.sub(financial_info_pattern, r'<mark>\g<0></mark>', highlighted_text, flags=re.IGNORECASE)
    highlighted_text = re.sub(agreement_terms_pattern, r'<mark>\g<0></mark>', highlighted_text, flags=re.IGNORECASE)
    highlighted_text = re.sub(contact_info_pattern, r'<mark>\g<0></mark>', highlighted_text, flags=re.IGNORECASE)
    highlighted_text = re.sub(signatures_pattern, r'<mark>\g<0></mark>', highlighted_text, flags=re.IGNORECASE)
    highlighted_text = re.sub(amount_pattern, r'<mark>\g<0></mark>', highlighted_text, flags=re.IGNORECASE)
    highlighted_text = re.sub(participant_pattern, r'<mark>\g<0></mark>', highlighted_text, flags=re.IGNORECASE)

    # Use SpaCy to find and return entities
    doc = nlp(text)
    entities = []
    entity_mappings = {}

    for ent in doc.ents:
        if ent.label_ in ['PERSON', 'ORG', 'GPE', 'DATE', 'MONEY']:
            entities.append({'text': ent.text, 'label': ent.label_})

    # Extract highlighted words and their section numbers
    highlighted_words = []

    for section in sections:
        section_content = []
        for entity in section['content']:
            if isinstance(entity, dict):
                section_content.append(entity['title'])
                section_content.extend(entity['content'])
            else:
                section_content.append(entity)
        
        section_content_str = ' '.join(map(str, section_content))  # Join only strings
        section_doc = nlp(section_content_str)
        for ent in section_doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'GPE', 'DATE', 'MONEY']:
                highlighted_words.append({'text': ent.text, 'section': section['title'], 'label': ent.label_})
                # Extract values associated with entities from the original text
                entity_value = extract_entity_value(ent.text, text)
                if entity_value:
                    entity_mappings[ent.text] = entity_value

    return highlighted_text, entities, highlighted_words, entity_mappings

def extract_entity_value(entity_text, text):
    value_pattern = re.compile(r'\b{}\b'.format(re.escape(entity_text)), flags=re.IGNORECASE)
    match = re.search(value_pattern, text)
    if match:
        return match.group(0)
    return None

# def find_missing_content(template_entities, contract_entities):
#     missing_content = []

#     template_texts = {entity['text'] for entity in template_entities}
#     contract_texts = {entity['text'] for entity in contract_entities}

#     for text in template_texts:
#         if text not in contract_texts:
#             missing_content.append(text)

#     return missing_content

# def find_additional_content(template_entities, contract_entities):
#     additional_content = []

#     template_texts = {entity['text'] for entity in template_entities}
#     contract_texts = {entity['text'] for entity in contract_entities}

#     for text in contract_texts:
#         if text not in template_texts:
#             additional_content.append(text)

#     return additional_content

# def find_modified_content(template_entities, contract_entities):
#     modified_content = []

#     for template_entity in template_entities:
#         for contract_entity in contract_entities:
#             if template_entity['text'] == contract_entity['text'] and template_entity['text'] != contract_entity['text']:
#                 modified_content.append({
#                     'template_entity': template_entity['text'],
#                     'contract_entity': contract_entity['text']
#                 })

#     return modified_content
