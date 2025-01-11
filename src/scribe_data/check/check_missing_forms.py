import json
from scribe_data.wiktionary.parse_dump import LexemeProcessor
import re
from pathlib import Path
from scribe_data.utils import (
    lexeme_form_metadata,
    language_metadata,
    data_type_metadata,
)

iso_to_qid = {
    lang_data["iso"]: lang_data["qid"]
    for lang, lang_data in language_metadata.items()
    if "iso" in lang_data and "qid" in lang_data
}
# print(iso_to_qid)


def read_query_file(file_path):
    """
    Read SPARQL query from a file
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Query file not found at: {file_path}")
    except Exception as e:
        raise Exception(f"Error reading file: {str(e)}")


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


def extract_unique_grammatical_features(
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

    # Restructure results to match desired output format
    result = {}
    for word, lang_data in processor.forms_index.items():
        for lang, category_data in lang_data.items():
            # Convert ISO to QID
            lang_qid = iso_to_qid.get(lang)
            if not lang_qid or lang_qid not in result:
                result[lang_qid] = {data_type_metadata[dt]: [] for dt in data_types}

            for category, forms in category_data.items():
                # Get QID for the category
                category_qid = data_type_metadata.get(category)
                if not category_qid:
                    continue

                # Collect unique grammatical feature lists
                unique_features = []
                for form_features in forms.values():
                    sorted_features = sorted(form_features)
                    if sorted_features and sorted_features not in unique_features:
                        unique_features.append(sorted_features)

                # Add to result if not empty
                if unique_features:
                    result[lang_qid][category_qid].extend(unique_features)

    # Remove duplicates from each data type's lists
    for lang_qid in result:
        for category_qid in data_types:
            category_qid_mapped = data_type_metadata[category_qid]
            # Convert lists to tuples for set operation
            unique_features = {
                tuple(features) for features in result[lang_qid][category_qid_mapped]
            }
            # Convert back to lists
            result[lang_qid][category_qid_mapped] = [
                list(features) for features in unique_features
            ]

    # Remove languages with no features
    result = {
        lang_qid: data
        for lang_qid, data in result.items()
        if any(features for features in data.values())
    }

    return result


def get_missing_features(result_sparql, result_dump, languages, data_types):
    final_result = {}
    for key1 in result_sparql:
        if key1 in result_dump:
            for key2 in result_sparql[key1]:
                if key2 in result_dump[key1]:
                    # Get the unique values from result_dump excluding those in result_sparql
                    sparql_values = set(
                        tuple(item) for item in result_sparql[key1][key2]
                    )
                    dump_values = set(tuple(item) for item in result_dump[key1][key2])
                    unique_dump_values = dump_values - sparql_values

                    # Prepare the final result
                    if key1 not in final_result:
                        final_result[key1] = {}
                    final_result[key1][key2] = [
                        list(item) for item in unique_dump_values
                    ]

    # Extract all QIDs from the metadata
    all_qids = set()
    for category, items in lexeme_form_metadata.items():
        for key, value in items.items():
            all_qids.add(value["qid"])
    # Initialize results
    unmentioned_sublists = []
    remaining_sublists = []

    # Check each sublist in final_result
    for key1, key2_dict in final_result.items():
        for key2, sublists in key2_dict.items():
            for sublist in sublists:
                if any(qid not in all_qids for qid in sublist):
                    unmentioned_sublists.append(sublist)
                else:
                    remaining_sublists.append(sublist)

    # Print results
    print("Unmentioned Sublists:")
    print(json.dumps(unmentioned_sublists, indent=2))

    print("Remaining Mentioned Sublists:")
    print(json.dumps(remaining_sublists, indent=2))

    if remaining_sublists:
        remaining_sublists = {languages: {data_types: remaining_sublists}}
        return remaining_sublists
    return None


if __name__ == "__main__":
    import sys
    
    # Get the dump file path from command line argument
    dump_file = sys.argv[1] if len(sys.argv) > 1 else None
    if not dump_file:
        print("Error: Please provide the path to the dump file")
        sys.exit(1)

    try:
        # Read the query file
        input_file = Path(__file__).parent / "wikidata" / "language_data_extraction" / "bengali" / "nouns" / "query_nouns.sparql"
        query_text = read_query_file(input_file)
        result_sparql = parse_sparql_query(query_text)
        print(json.dumps(result_sparql, indent=2))

    except Exception as e:
        print(f"Error processing query: {str(e)}")

    print("Extracting unique grammatical features")
    result_dump = extract_unique_grammatical_features(
        languages=["bengali"],
        data_types=["nouns"],
        file_path=dump_file  # Use the provided file path
    )

    missing_features = get_missing_features(
        result_sparql, result_dump, languages="Q9610", data_types="Q1084"
    )

    if missing_features:
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

        forms_query = []
        for form_qids in missing_features[language_qid][data_type_qid]:
            # Convert QIDs to labels and join them together
            labels = [qid_to_label.get(qid, qid) for qid in form_qids]
            concatenated_label = "".join(labels)
            # Make first letter lowercase
            concatenated_label = concatenated_label[0].lower() + concatenated_label[1:]
            # Create a dictionary with both label and QIDs
            forms_query.append({"label": concatenated_label, "qids": form_qids})

        main_body = f"""
        # tool: scribe-data
        # All {language} ({language_qid}) {data_type} ({data_type_qid}) and the given forms.
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

        optional_clause = ""
        for i, form in enumerate(forms_query):
            qids = ", ".join(f"wd:{qid}" for qid in form["qids"])
            optional_clause += f"""
            OPTIONAL {{
                ?lexeme ontolex:lexicalForm ?{form['label']}Form .
                ?{form['label']}Form ontolex:representation ?{form['label']} ;
                    wikibase:grammaticalFeature {qids} .
            }}"""

        print(main_body + where_clause + optional_clause + "\n}")
