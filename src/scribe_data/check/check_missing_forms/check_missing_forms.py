import json
 
from get_forms import parse_sparql_files, extract_dump_forms 
from generate_query import generate_query
from collections import defaultdict
from scribe_data.utils import (
    lexeme_form_metadata,
    language_metadata,
    data_type_metadata
)
from pathlib import Path
iso_to_qid = {
    lang_data["iso"]: lang_data["qid"]
    for lang, lang_data in language_metadata.items()
    if "iso" in lang_data and "qid" in lang_data
}
# print(iso_to_qid)
# language_data_extraction = Path(__file__).parent/ 'wikidata'/ 'language_data_extraction'
language_data_extraction = Path('/media/asif/Mahbub1/test-scribe/src/scribe_data/wikidata/language_data_extraction')
 
 
def get_missing_features(result_sparql, result_dump):
    missing_by_lang_type = defaultdict(lambda: defaultdict(list))

    # Extract all QIDs from the metadata
    all_qids = set()
    for category, items in lexeme_form_metadata.items():
        for key, value in items.items():
            all_qids.add(value["qid"])

    # Compare features for each language and data type
    for lang in result_sparql:
        if lang in result_dump:
            for dt in result_sparql[lang]:
                if dt in result_dump[lang]:
                    # Get the unique values from result_dump excluding those in result_sparql
                    sparql_values = set(tuple(item) for item in result_sparql[lang][dt])
                    dump_values = set(tuple(item) for item in result_dump[lang][dt])
                    unique_dump_values = dump_values - sparql_values

                    # Filter and store valid missing features
                    for item in unique_dump_values:
                        if all(qid in all_qids for qid in item):
                            missing_by_lang_type[lang][dt].append(list(item))
 
    # Print results for debugging
    print("Missing features by language and type:")
    print(json.dumps(missing_by_lang_type, indent=2))

    return missing_by_lang_type if missing_by_lang_type else None
 
# Read the query file using the provided path
result_sparql = parse_sparql_files()
print(result_sparql)
 
print("Extracting Wiki lexeme dump")
result_dump = extract_dump_forms(
    languages=list(language_metadata.keys()),
    data_types=list(data_type_metadata.keys()),
    file_path="/media/asif/Mahbub1/test-scribe/scribe_data_wikidata_dumps_export/latest-lexemes.json.bz2"
)

# Convert result_dump to a JSON string and print it beautifully
print(json.dumps(result_dump, indent=4, ensure_ascii=False))

missing_features = get_missing_features(
    result_sparql, result_dump
)
 
if missing_features:
    for language, data_types in missing_features.items():
        # Create and process one language at a time
        language_entry = defaultdict(lambda: defaultdict(list))
        language_entry[language] = data_types  # Keep the entire data structure for this language
        generate_query(language_entry)
            