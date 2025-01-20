"""
Get forms from Wikidata.
.. raw:: html
    <!--
    * Copyright (C) 2024 Scribe
    *
    * This program is free software: you can redistribute it and/or modify
    * it under the terms of the GNU General Public License as published by
    * the Free Software Foundation, either version 3 of the License, or
    * (at your option) any later version.
    *
    * This program is distributed in the hope that it will be useful,
    * but WITHOUT ANY WARRANTY; without even the implied warranty of
    * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    * GNU General Public License for more details.
    *
    * You should have received a copy of the GNU General Public License
    * along with this program.  If not, see <https://www.gnu.org/licenses/>.
    -->
"""

from scribe_data.wiktionary.parse_dump import LexemeProcessor
import re
from collections import defaultdict
from scribe_data.utils import (
    language_metadata,
    data_type_metadata,
    LANGUAGE_DATA_EXTRACTION_DIR as language_data_extraction,
)

iso_to_qid = {
    lang_data["iso"]: lang_data["qid"]
    for lang, lang_data in language_metadata.items()
    if "iso" in lang_data and "qid" in lang_data
}

all_forms = defaultdict(lambda: defaultdict(list))


def parse_sparql_files():
    """
    Read and parse all SPARQL query files to extract form information.

    Returns
    -------
    dict
        Accumulated forms for each language and lexical category.
        Format: {language: {lexical_category: [forms]}}

    Notes
    -----
    Recursively searches through language_data_extraction directory
    for .sparql files and accumulates all form information.
    """
    for sub_sub_file in language_data_extraction.rglob("*.sparql"):
        with open(sub_sub_file, "r", encoding="utf-8") as query_text:
            result = parse_sparql_query(query_text.read())

            # Accumulate forms for each language and lexical category.
            for lang, categories in result.items():
                for category, forms in categories.items():
                    if forms:
                        all_forms[lang][category].extend(forms)

    return all_forms


def parse_sparql_query(query_text):
    """
    Parse a SPARQL query to extract lexical categories and features.

    Parameters
    ----------
    query_text : str
        Content of the SPARQL query file.

    Returns
    -------
    dict
        Dictionary containing parsed information.
        Format: {language: {lexical_category: [forms]}}

    Notes
    -----
    Extracts:
    - Language QID
    - Lexical category QID
    - Grammatical features from OPTIONAL blocks
    """
    # Get language and category first.
    language = None
    lexical_category = None

    # Parse lexical category.
    lexical_matches = re.finditer(r"wikibase:lexicalCategory\s+wd:(Q\d+)", query_text)
    for match in lexical_matches:
        lexical_category = match.group(1)

    # Parse language.
    language_matches = re.finditer(r"dct:language\s+wd:(Q\d+)", query_text)
    for match in language_matches:
        language = match.group(1)

    result = {language: {lexical_category: []}}

    # Parse optional blocks for forms and features.
    optional_blocks = re.finditer(r"OPTIONAL\s*{([^}]+)}", query_text)

    for block in optional_blocks:
        block_text = block.group(1)

        # Extract grammatical features.
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
    Extract unique grammatical features from Wikidata lexeme dump.

    Parameters
    ----------
    languages : list of str, optional
        List of language ISO codes (e.g., ['en', 'fr'])
    data_types : list of str, optional
        List of lexical categories (e.g., ['nouns', 'verbs'])
    file_path : str, optional
        Path to the lexeme dump file, by default "latest-lexemes.json.bz2"

    Returns
    -------
    dict
        Dictionary of unique grammatical features per language and lexical category.
        Format: {language_qid: {data_type_qid: features}}

    Notes
    -----
    - Converts ISO codes to QIDs in the output
    - Converts data type names to their corresponding QIDs
    - Only includes languages and data types that have valid QID mappings
    """
    processor = LexemeProcessor(
        target_iso=languages, parse_type=["form"], data_types=data_types
    )

    processor.process_file(file_path)

    unique_features = dict(processor.unique_forms)

    # Convert ISO codes to QIDs and data types to QIDs.
    converted_features = {}
    for iso_code, data_types_dict in unique_features.items():
        if iso_code in iso_to_qid:
            lang_qid = iso_to_qid[iso_code]
            converted_features[lang_qid] = {}

            for data_type, features in data_types_dict.items():
                # Get QID from data_type_metadata.
                data_type_qid = data_type_metadata.get(data_type)
                if data_type_qid:
                    converted_features[lang_qid][data_type_qid] = features

    return converted_features
