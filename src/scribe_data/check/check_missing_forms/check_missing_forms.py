# SPDX-License-Identifier: GPL-3.0-or-later
"""
Check for missing forms in Wikidata and download Wikidata lexeme dump.
"""

import json
from collections import defaultdict

from generate_query import generate_query

from scribe_data.utils import (
    LANGUAGE_DATA_EXTRACTION_DIR,
    language_metadata,
    lexeme_form_metadata,
    sub_languages,
)

from scribe_data.check.check_missing_forms.normalize_forms import (
    sort_qids_in_list,
    sort_qids_by_position,
)


def get_all_languages():
    """
    Extract all languages and sub languages from language metadata.

    Returns
    -------
    list of str
        List of language codes for all languages and sub languages that have
        both ISO codes and QIDs defined.

    Notes
    -----
    Only includes languages and sub languages that have both 'iso' and 'qid'
    fields in their metadata.
    """
    languages = []

    for lang, lang_data in language_metadata.items():
        # Add main language if it has ISO and QID.
        if "iso" in lang_data and "qid" in lang_data:
            languages.append(lang)

        # Add sub languages.
        if "sub_languages" in lang_data:
            languages.extend(
                sublang
                for sublang, sublang_data in lang_data["sub_languages"].items()
                if "iso" in sublang_data and "qid" in sublang_data
            )

    return languages


def get_missing_features(result_sparql, result_dump):
    """
    Compare features between SPARQL results and dump data to find missing ones.

    Parameters
    ----------
    result_sparql : dict
        Features extracted from SPARQL queries.
        Format: {language: {data_type: [features]}}

    result_dump : dict
        Features extracted from Wikidata dump.
        Format: {language: {data_type: [features]}}

    Returns
    -------
    dict or None
        Dictionary of missing features by language and data type if any found,
        otherwise None.
        Format: {language: {data_type: [missing_features]}}

    Notes
    -----
    Only includes features that have valid QIDs present in lexeme_form_metadata.
    """
    missing_by_lang_type = defaultdict(lambda: defaultdict(list))

    # Extract all QIDs from the metadata.
    all_qids = set()
    for category, items in lexeme_form_metadata.items():
        for key, value in items.items():
            all_qids.add(value["qid"])

    # Compare features for each language and data type.
    for lang in result_sparql:
        if lang in result_dump:
            # Get all unique data types from both sources.
            all_data_types = set(result_sparql[lang].keys()) | set(
                result_dump[lang].keys()
            )

            for dt in all_data_types:
                sparql_values = set()
                dump_values = set()

                # Get values from SPARQL if available.
                if dt in result_sparql[lang]:
                    sparql_values = {tuple(item) for item in result_sparql[lang][dt]}

                # Get values from dump if available.
                if dt in result_dump[lang]:
                    dump_values = {tuple(item) for item in result_dump[lang][dt]}

                print(dump_values)

                # Get unique values from both sources.
                unique_dump_values = (
                    set(map(tuple, sort_qids_in_list(dump_values))) - sparql_values
                )

                # Store valid missing features from dump.
                for item in unique_dump_values:
                    if all(qid in all_qids for qid in item):
                        missing_by_lang_type[lang][dt].append(list(item))

    return missing_by_lang_type or None


def process_missing_features(missing_features, query_dir):
    """
    Generate SPARQL queries for missing features by language and data type.

    Parameters
    ----------
    missing_features : dict
        Dictionary of missing features by language and data type.
        Format: {language: {data_type: [features]}}

    query_dir : str or Path
        Directory where generated query files should be saved.

    Notes
    -----
    Generates separate queries for each data type within each language.
    """
    if not missing_features:
        return
    sub_languages_iso_codes = {}
    for language, sub_langs in sub_languages.items():
        # Get all unique QIDs and their ISO codes for this language.
        qid_to_isos = {}
        for iso_code, sub_lang_data in sub_langs.items():
            qid = sub_lang_data["qid"]
            if qid not in qid_to_isos:
                qid_to_isos[qid] = set()
            qid_to_isos[qid].add(iso_code)

        # Add to main dictionary.
        sub_languages_iso_codes |= qid_to_isos

    for language_qid, data_types_qid in missing_features.items():
        print(f"Processing language: {language_qid}")
        print(f"Data types: {list(data_types_qid.keys())}")

        # Create a separate entry for each data type.
        for data_type_qid, features in data_types_qid.items():
            language_entry = {language_qid: {data_type_qid: features}}
            #
            if language_qid in sub_languages_iso_codes:
                for sub_lang_iso_code in sub_languages_iso_codes[language_qid]:
                    print(
                        f"Generating query for {language_qid} - {data_type_qid} - {sub_lang_iso_code}"
                    )
                    split_group_by_identifier(
                        language_entry, LANGUAGE_DATA_EXTRACTION_DIR, sub_lang_iso_code
                    )
                    # generate_query(
                    #     language_entry, LANGUAGE_DATA_EXTRACTION_DIR, sub_lang_iso_code
                    # )

            else:
                print(f"Generating query for {language_qid} - {data_type_qid}")
                # generate_query(language_entry, LANGUAGE_DATA_EXTRACTION_DIR)
                split_group_by_identifier(
                    language_entry, LANGUAGE_DATA_EXTRACTION_DIR, sub_lang_iso_code=None
                )


def split_group_by_identifier(language_entry, output_dir, sub_lang_iso_code=None):
    """
    Split forms into groups of up to six forms per query based on identifiers.

    Parameters
    ----------
    language_entry : dict
        Dictionary containing language data with missing features.
        Format: {language_qid: {data_type_qid: [features]}}
    output_dir : str or Path
        Directory where generated query files should be saved.
    sub_lang_iso_code : str, optional
        ISO code for sub-language if applicable.

    Notes
    -----
    Groups forms based on their identifiers to avoid generating too many queries.
    Combines small groups when possible to reduce the number of query files.
    """
    for lang, data in language_entry.items():
        for data_type, missing_features_list in data.items():
            # Group features by their first identifier
            identifier_groups = defaultdict(list)

            # First try to group by the first identifier in each feature list
            for feature_list in missing_features_list:
                if feature_list:  # Skip empty lists
                    # Use the first identifier as the grouping key
                    key = feature_list[0]
                    identifier_groups[key].append(
                        feature_list
                    )  # =>{Q1234:[Q2345,Q4567],[Q567]}

            # Now check if any groups have more than 6 features
            final_groups = []

            for identifier, features in identifier_groups.items():
                if len(features) <= 6:
                    # This group is small enough, keep it as is
                    final_groups.append(features)
                else:
                    # This group is too large, need to split further by second identifier
                    second_level_groups = defaultdict(list)

                    for feature_list in features:
                        if len(feature_list) > 1:
                            # Use the second identifier for further grouping
                            second_key = feature_list[1]
                            second_level_groups[second_key].append(feature_list)
                        else:
                            # If there's only one identifier, make it its own group
                            second_level_groups["single_identifier"].append(
                                feature_list
                            )

                    # Further split if necessary and add to final groups
                    for (
                        second_identifier,
                        second_features,
                    ) in second_level_groups.items():
                        # Split into chunks of 6
                        for i in range(0, len(second_features), 6):
                            chunk = second_features[i : i + 6]
                            final_groups.append(chunk)

            # Now combine small groups if possible to reduce query files
            optimized_groups = []
            current_group = []

            # Sort groups by size to try combining smaller ones first
            final_groups.sort(key=len)

            for group in final_groups:
                if len(current_group) + len(group) <= 6:
                    # Can add this group to the current one
                    current_group.extend(group)
                else:
                    # Current group is full, start a new one
                    if current_group:
                        optimized_groups.append(current_group)
                    current_group = group

            # Add the last group if not empty
            if current_group:
                optimized_groups.append(current_group)

            # Generate queries for each optimized group
            for i, group in enumerate(optimized_groups):
                # Create a new language entry for this group
                group = sort_qids_by_position(group)
                group_entry = {lang: {data_type: group}}

                print(
                    f"Generating query {i+1}/{len(optimized_groups)} for {lang} - {data_type} with {len(group)} features"
                )

                # Call generate_query with the grouped features
                generate_query(
                    group_entry,
                    output_dir,
                    sub_lang_iso_code=sub_lang_iso_code,
                )


# def main():
#     """
#     Main function to check for missing forms in Wikidata.

#     Processes command line arguments, downloads and compares Wikidata dump data
#     with SPARQL query results to identify missing features, and generates
#     appropriate SPARQL queries.

#     Notes
#     -----
#     Required command line arguments:
#     - dump_path: Path to the Wikidata dump file or None to download
#     - query_dir: Directory for storing generated queries

#     Optional arguments:
#     - --process-all-keys: Flag to process all nested keys in missing features
#     - --download-dump: Flag to download the dump if dump_path is not provided
#     """
#     parser = argparse.ArgumentParser(description="Check missing forms in Wikidata")
#     parser.add_argument(
#         "dump_path",
#         type=str,
#         nargs="?",
#         default=None,
#         help="Path to the dump file (optional if --download-dump is used)",
#     )
#     parser.add_argument("query_dir", type=str, help="Path to the query directory")
#     parser.add_argument(
#         "--process-all-keys",
#         action="store_true",
#         help="Process all nested keys in the missing features",
#     )
#     parser.add_argument(
#         "--download-dump",
#         action="store_true",
#         help="Download Wikidata lexeme dump if dump_path is not provided",
#     )

#     args = parser.parse_args()

#     # If no dump path is provided and download flag is set, download the dump.
#     if not args.dump_path and args.download_dump:
#         # MARK: Download Dump

#         dump_path = wd_lexeme_dump_download_wrapper(
#             wikidata_dump=None, output_dir=None, default=True
#         )
#         if not dump_path:
#             print("Failed to download Wikidata dump.")
#             sys.exit(1)

#     elif not args.dump_path:
#         print("Error: Either provide a dump path or use --download-dump flag")
#         sys.exit(1)

#     else:
#         dump_path = args.dump_path

#     dump_path = Path(dump_path)
#     query_dir = Path(args.query_dir)

#     if not dump_path.exists():
#         print(f"Error: Dump path does not exist: {dump_path}")
#         sys.exit(1)

#     if not query_dir.exists():
#         print(f"Error: Query directory does not exist: {query_dir}")
#         sys.exit(1)

#     # Get all languages including sub languages.
#     languages = get_all_languages()

#     # MARK: Parse SPARQL

#     print("Parsing SPARQL files...")
#     result_sparql = parse_sparql_files()

#     # MARK: Extract Forms

#     print("Extracting Wiki lexeme dump...")
#     result_dump = extract_dump_forms(
#         languages=languages,
#         data_types=list(data_type_metadata.keys()),
#         file_path=dump_path,
#     )

#     # MARK: Get Features

#     missing_features = get_missing_features(result_sparql, result_dump)

#     try:
#         # MARK: Save Features

#         print("Generated missing features:", missing_features)

#         with open("missing_features.json", "w") as f:
#             json.dump(missing_features, f, indent=4)

#         print("Missing features data has been saved to missing_features.json")

#         if missing_features:
#             # Process all data types for each language.
#             process_missing_features(missing_features, query_dir)

#     except Exception as e:
#         print(f"An error occurred: {e}")
#         sys.exit(1)


# if __name__ == "__main__":
#     main()


def main():
    #     """
    #     Main function to check for missing forms in Wikidata.

    #     Processes command line arguments, downloads and compares Wikidata dump data
    #     with SPARQL query results to identify missing features, and generates
    #     appropriate SPARQL queries.

    #     Notes
    #     -----
    #     Required command line arguments:
    #     - dump_path: Path to the Wikidata dump file or None to download
    #     - query_dir: Directory for storing generated queries

    #     Optional arguments:
    #     - --process-all-keys: Flag to process all nested keys in missing features
    #     - --download-dump: Flag to download the dump if dump_path is not provided
    #     """
    # parser = argparse.ArgumentParser(description="Check missing forms in Wikidata")
    # parser.add_argument(
    #     "dump_path",
    #     type=str,
    #     nargs="?",
    #     default=None,
    #     help="Path to the dump file (optional if --download-dump is used)",
    # )
    # parser.add_argument("query_dir", type=str, help="Path to the query directory")
    # parser.add_argument(
    #     "--process-all-keys",
    #     action="store_true",
    #     help="Process all nested keys in the missing features",
    # )
    # parser.add_argument(
    #     "--download-dump",
    #     action="store_true",
    #     help="Download Wikidata lexeme dump if dump_path is not provided",
    # )

    # args = parser.parse_args()

    # # If no dump path is provided and download flag is set, download the dump.
    # if not args.dump_path and args.download_dump:
    #     # MARK: Download Dump

    #     dump_path = wd_lexeme_dump_download_wrapper(
    #         wikidata_dump=None, output_dir=None, default=True
    #     )
    #     if not dump_path:
    #         print("Failed to download Wikidata dump.")
    #         sys.exit(1)

    # elif not args.dump_path:
    #     print("Error: Either provide a dump path or use --download-dump flag")
    #     sys.exit(1)

    # else:
    #     dump_path = args.dump_path

    # dump_path = Path(dump_path)
    # query_dir = Path(args.query_dir)

    # if not dump_path.exists():
    #     print(f"Error: Dump path does not exist: {dump_path}")
    #     sys.exit(1)

    # if not query_dir.exists():
    #     print(f"Error: Query directory does not exist: {query_dir}")
    #     sys.exit(1)

    # Get all languages including sub languages.
    # languages = get_all_languages()

    # # MARK: Parse SPARQL

    # # print("Parsing SPARQL files...")
    # result_sparql = parse_sparql_files()

    # # MARK: Extract Forms

    # print("Extracting Wiki lexeme dump...")
    # result_dump = extract_dump_forms(
    #     languages=languages,
    #     data_types=list(data_type_metadata.keys()),
    #     file_path="/media/asif/Mahbub1/test-scribe/src/scribe_data/check/scribe_data_wikidata_dumps_export/latest-lexemes.json.bz2",
    # )
    # with open("result_dump.json", "w") as f:
    #     json.dump(result_dump, f, indent=4)

    # with open("result_sparql.json", "w") as f:
    #     json.dump(result_sparql, f, indent=4)

    # with open("result_sparql.json", "r") as f:
    #     result_sparql = json.load(f)

    # with open("result_dump.json", "r") as f:
    #     result_dump = json.load(f)

    # missing_features = get_missing_features(result_sparql, result_dump)

    # with open("missing_features.json", "w") as f:
    #     json.dump(missing_features, f, indent=4)

    with open("missing_features.json", "r") as f:
        missing_features = json.load(f)

    process_missing_features(missing_features, query_dir=None)


# # # MARK: Get Features


# try:
#     # MARK: Save Features

#     print("Generated missing features:", missing_features)

#     with open("missing_features.json", "w") as f:
#         json.dump(missing_features, f, indent=4)

#     print("Missing features data has been saved to missing_features.json")

#     if missing_features:
#         # Process all data types for each language.
#         process_missing_features(missing_features, query_dir=None)

# except Exception as e:
#     print(f"An error occurred: {e}")
#     sys.exit(1)


if __name__ == "__main__":
    main()
