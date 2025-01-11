import json
from scribe_data.utils import lexeme_form_metadata

result_sparql = {
    "Q9610": {"Q1084": [["Q131105"], ["Q146233"], ["Q146078"], ["Q202142"]]}
}

result_dump = {
    "Q9610": {
        "Q1084": [
            ["Q202142", "Q202142"],
            ["Q202142", "Q55094451"],
            ["Q131105", "Q146078"],
            ["Q131105", "Q146078", "Q202142"],
            ["Q131105"],
            ["Q146078", "Q146233"],
            ["Q146233"],
            ["Q145599", "Q146078"],
            ["Q131105", "Q202142"],
            ["Q146078"],
            ["Q131105", "Q145599", "Q146078", "Q146233"],
            ["Q146233", "Q202142"],
            ["Q145599"],
            ["Q202142"],
            ["Q146078", "Q202142"],
            ["Q131105", "Q146233"],
        ]
    }
}

final_result = {}
for key1 in result_sparql:
    if key1 in result_dump:
        for key2 in result_sparql[key1]:
            if key2 in result_dump[key1]:
                # Get the unique values from result_dump excluding those in result_sparql
                sparql_values = set(tuple(item) for item in result_sparql[key1][key2])
                dump_values = set(tuple(item) for item in result_dump[key1][key2])
                unique_dump_values = dump_values - sparql_values

                # Prepare the final result
                if key1 not in final_result:
                    final_result[key1] = {}
                final_result[key1][key2] = [list(item) for item in unique_dump_values]


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
