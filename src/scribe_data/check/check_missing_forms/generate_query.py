from scribe_data.utils import (
    lexeme_form_metadata,
    language_metadata,
    data_type_metadata,
    language_data_extraction
)
 
import os
 
def generate_query(missing_features):
    language_qid = next(iter(missing_features.keys()))
    data_type_qid = next(iter(missing_features[language_qid].keys()))

    # Find the language entry by QID
    language_entry = next(
        (name, data)
        for name, data in language_metadata.items()
        if data.get("qid") == language_qid
    )
    language = language_entry[0]  # The language name

    data_type = next(
        name for name, qid in data_type_metadata.items() if qid == data_type_qid
    )

    iso_code = language_metadata[language]["iso"]

    # Create a QID to label mapping from the metadata
    qid_to_label = {}
    for category in lexeme_form_metadata.values():
        for item in category.values():
            qid_to_label[item["qid"]] = item["label"]

    # Process all forms at once
    forms_query = []
    all_form_combinations = missing_features[language_qid][data_type_qid]
    for form_qids in all_form_combinations:
        # Convert QIDs to labels and join them together
        labels = [qid_to_label.get(qid, qid) for qid in form_qids]
        concatenated_label = "".join(labels)
        # Make first letter lowercase
        concatenated_label = concatenated_label[0].lower() + concatenated_label[1:]
        forms_query.append({"label": concatenated_label, "qids": form_qids})

    # Generate a single query for all forms
    main_body = f"""
# tool: scribe-data
# All {language} ({language_qid}) {data_type} ({data_type_qid}) and their forms.
# Enter this query at https://query.wikidata.org/.

SELECT
   (REPLACE(STR(?lexeme), "http://www.wikidata.org/entity/", "") AS ?lexemeID)
    ?{data_type}
    """ + "\n  ".join(f'?{form["label"]}' for form in forms_query)

    where_clause = f"""
  WHERE {{
    ?lexeme dct:language wd:{language_qid} ;
        wikibase:lexicalCategory wd:{data_type_qid} ;
        wikibase:lemma ?{data_type} .
        FILTER(lang(?{data_type}) = "{iso_code}")
    """

    # Generate OPTIONAL clauses for all forms in one query
    optional_clauses = ""
    for form in forms_query:
        qids = ", ".join(f"wd:{qid}" for qid in form["qids"])
        optional_clauses += f"""
        OPTIONAL {{
            ?lexeme ontolex:lexicalForm ?{form['label']}Form .
            ?{form['label']}Form ontolex:representation ?{form['label']} ;
                wikibase:grammaticalFeature {qids} .
        }}"""

    # Print the complete query
    final_query = main_body + where_clause + optional_clauses + "\n}"
    
    def get_available_filename(base_path):
        """Helper function to find the next available filename"""
        if not os.path.exists(base_path):
            return base_path
            
        base, ext = os.path.splitext(base_path)
        counter = 1
        
        # If the base already ends with _N, start from that number
        import re
        if match := re.search(r'_(\d+)$', base):
            counter = int(match.group(1)) + 1
            base = base[:match.start()]
            
        while True:
            new_path = f"{base}_{counter}{ext}"
            if not os.path.exists(new_path):
                return new_path
            counter += 1
    
    # Create base filename
    base_file_name = f"{language_data_extraction}/{language}/{data_type}/query_{data_type}.sparql"
    
    # Get the next available filename
    file_name = get_available_filename(base_file_name)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    
    # Write the file
    with open(file_name, "w") as file:
        file.write(final_query)
    
    print(f"Query file created: {file_name}")

