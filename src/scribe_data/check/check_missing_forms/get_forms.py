from scribe_data.wiktionary.parse_dump import LexemeProcessor
import re
from pathlib import Path
from scribe_data.utils import (
    language_metadata,
    data_type_metadata,
)
from collections import defaultdict
# from check_missing_forms.check_missing_forms import language_data_extraction 
iso_to_qid = {
    lang_data["iso"]: lang_data["qid"]
    for lang, lang_data in language_metadata.items()
    if "iso" in lang_data and "qid" in lang_data
}
# print(iso_to_qid)
language_data_extraction = Path('/media/asif/Mahbub1/test-scribe/src/scribe_data/wikidata/language_data_extraction')
 

all_forms = defaultdict(lambda: defaultdict(list))

def parse_sparql_files():
    """
    Read SPARQL query from a file and accumulate all forms
    """
    for sub_sub_file in language_data_extraction.rglob('*.sparql'):
        with open(sub_sub_file, "r", encoding="utf-8") as query_text:
            result = parse_sparql_query(query_text.read())
            
            # Accumulate forms for each language and lexical category
            for lang, categories in result.items():
                for category, forms in categories.items():
                    if forms:  
                        all_forms[lang][category].extend(forms)

    return all_forms

def parse_sparql_query(query_text):
    """
    Parse SPARQL query to extract lexical categories and grammatical features
    Returns format: {language: {lexical_category: [forms...]}}
    """
    # Get language and category first
    language = None
    lexical_category = None

    # Parse lexical category
    lexical_matches = re.finditer(r"wikibase:lexicalCategory\s+wd:(Q\d+)", query_text)
    for match in lexical_matches:
        lexical_category = match.group(1)

    # Parse language
    language_matches = re.finditer(r"dct:language\s+wd:(Q\d+)", query_text)
    for match in language_matches:
        language = match.group(1)

    # Initialize result structure
    result = {language: {lexical_category: []}}

    # Parse optional blocks for forms and features
    optional_blocks = re.finditer(r"OPTIONAL\s*{([^}]+)}", query_text)

    for block in optional_blocks:
        block_text = block.group(1)

        # Extract grammatical features
        features = re.finditer(r"wd:(Q\d+)", block_text)
        feature_list = [f.group(1) for f in features]

        if feature_list:
            result[language][lexical_category].append(feature_list)

    return result


parse_sparql_files()


def extract_dump_forms(
    languages=None, data_types=None, file_path="latest-lexemes.json.bz2"
):
    """
    Extract unique grammatical features from lexeme dump.

    Parameters:
    - languages: List of language ISO codes (e.g., ['en', 'fr'])
    - data_types: List of lexical categories (e.g., ['nouns', 'verbs'])
    - file_path: Path to the lexeme dump file

    Returns:
    Dictionary of unique grammatical features per language and lexical category
    """
    # Initialize processor with specific parsing requirements
    processor = LexemeProcessor(
        target_iso=languages, parse_type=["form"], data_types=data_types
    )

    # Process the entire dump file
    processor.process_file(file_path)

    unique_features = dict(processor.unique_forms)
    
    # Convert ISO codes to QIDs and data types to QIDs
    converted_features = {}
    for iso_code, data_types_dict in unique_features.items():
        if iso_code in iso_to_qid:
            lang_qid = iso_to_qid[iso_code]
            converted_features[lang_qid] = {}
            
            for data_type, features in data_types_dict.items():
                # Get QID from data_type_metadata
                data_type_qid = data_type_metadata.get(data_type)
                if data_type_qid:
                    converted_features[lang_qid][data_type_qid] = features

    return converted_features

