import json
import sys
import argparse
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
 
    # Print results for debugging
    # print("Missing features by language and type:")
    # print(json.dumps(missing_by_lang_type, indent=2))

    return missing_by_lang_type if missing_by_lang_type else None

def process_missing_features(missing_features, query_dir):
    """Process all data types for each language when generating queries."""
    if not missing_features:
        return

    for language, data_types in missing_features.items():
        print(f"Processing language: {language}")
        print(f"Data types: {list(data_types.keys())}")
        
        # Create a separate entry for each data type
        for data_type, features in data_types.items():
            language_entry = {
                language: {
                    data_type: features
                }
            }
            print(f"Generating query for {language} - {data_type}")
            generate_query(language_entry, query_dir)

def main():
    parser = argparse.ArgumentParser(description='Check missing forms in Wikidata')
    parser.add_argument('dump_path', type=str, help='Path to the dump file')
    parser.add_argument('query_dir', type=str, help='Path to the query directory')
    parser.add_argument('--process-all-keys', action='store_true', 
                       help='Process all nested keys in the missing features')
    
    args = parser.parse_args()

    dump_path = Path(args.dump_path)
    query_dir = Path(args.query_dir)

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
        data_types=list(data_type_metadata.keys()),
        file_path=dump_path
    )

    missing_features = get_missing_features(result_sparql, result_dump, args.process_all_keys)

    try:
        print("Generated missing features:", missing_features)

        # Save the missing features to a JSON file
        with open('missing_features.json', 'w') as f:
            json.dump(missing_features, f, indent=4)
        print("Missing features data has been saved to missing_features.json")

        if missing_features:
            # Process all data types for each language
            process_missing_features(missing_features, query_dir)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
            