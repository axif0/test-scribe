from scribe_data.utils import (
    lexeme_form_metadata,
    language_metadata,
    data_type_metadata,
)

missing_queries = {
    "Q13955": {
        "Q34698": [
            ["Q131105", "Q1775415", "Q53997857", "Q110786"],
            ["Q131105", "Q1775415", "Q53997857", "Q146786"],
            ["Q131105", "Q1775415", "Q53997857", "Q110022"],
            ["Q131105", "Q499327", "Q53997857", "Q110786"],
            ["Q131105", "Q499327", "Q53997857", "Q146786"],
            ["Q131105", "Q499327", "Q53997857", "Q110022"],
            ["Q146233", "Q1775415", "Q53997857", "Q110786"],
            ["Q146233", "Q1775415", "Q53997857", "Q146786"],
            ["Q146233", "Q1775415", "Q53997857", "Q110022"],
            ["Q146233", "Q499327", "Q53997857", "Q110786"],
            ["Q146233", "Q499327", "Q53997857", "Q146786"],
            ["Q146233", "Q499327", "Q53997857", "Q110022"],
            ["Q146078", "Q1775415", "Q53997857", "Q110786"],
            ["Q146078", "Q1775415", "Q53997857", "Q146786"],
            ["Q146078", "Q1775415", "Q53997857", "Q110022"],
            ["Q146078", "Q499327", "Q53997857", "Q110786"],
            ["Q146078", "Q499327", "Q53997857", "Q146786"],
            ["Q146078", "Q499327", "Q53997857", "Q110022"],
            ["Q117262361", "Q1775415", "Q53997857", "Q110786"],
            ["Q117262361", "Q1775415", "Q53997857", "Q146786"],
            ["Q117262361", "Q1775415", "Q53997857", "Q110022"],
            ["Q117262361", "Q499327", "Q53997857", "Q110786"],
            ["Q117262361", "Q499327", "Q53997857", "Q146786"],
            ["Q117262361", "Q499327", "Q53997857", "Q110022"],
        ]
    }
}
language_qid = next(iter(missing_queries.keys()))
data_type_qid = next(iter(missing_queries[language_qid].keys()))

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
for form_qids in missing_queries[language_qid][data_type_qid]:
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
