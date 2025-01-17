import json
import sys
from pathlib import Path
from get_forms import parse_sparql_files, extract_dump_forms 
from generate_query import generate_query
from collections import defaultdict
from scribe_data.utils import (
    lexeme_form_metadata,
    language_metadata,
    data_type_metadata,
) 

def get_all_languages():
    """Extract all languages including sublanguages."""
    languages = []
    
    for lang, lang_data in language_metadata.items():
        # Add main language if it has ISO and QID
        if "iso" in lang_data and "qid" in lang_data:
            languages.append(lang)
        
        # Add sublanguages
        if "sub_languages" in lang_data:
            for sublang, sublang_data in lang_data["sub_languages"].items():
                if "iso" in sublang_data and "qid" in sublang_data:
                    languages.append(sublang)
    
    return languages

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
 
    return missing_by_lang_type if missing_by_lang_type else None

def main():
    if len(sys.argv) != 3:
        print("Usage: python check_missing_forms.py <dump_path> <query_dir>")
        sys.exit(1)

    dump_path = Path(sys.argv[1])
    query_dir = Path(sys.argv[2])

    if not dump_path.exists():
        print(f"Error: Dump path does not exist: {dump_path}")
        sys.exit(1)

    if not query_dir.exists():
        print(f"Error: Query directory does not exist: {query_dir}")
        sys.exit(1)

    # Get all languages including sublanguages
    languages = get_all_languages()

    print("Parsing SPARQL files...")
    result_sparql = parse_sparql_files()

    print("Extracting Wiki lexeme dump...")
    result_dump = extract_dump_forms(
        languages=languages,
        languages=languages,
        data_types=list(data_type_metadata.keys()),
        file_path=dump_path
    )

    missing_features = get_missing_features(result_sparql, result_dump)

    try:
        print("Generated missing features:", missing_features)

        # Save the missing features to a JSON file
        with open('missing_features.json', 'w') as f:
            json.dump(missing_features, f, indent=4)
        print("Missing features data has been saved to missing_features.json")

        if missing_features:
            for language, data_types in missing_features.items():
                # Create and process one language at a time
                language_entry = defaultdict(lambda: defaultdict(list))
                language_entry[language] = data_types
                generate_query(language_entry, query_dir)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
            