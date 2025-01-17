import json
import sys
from scribe_data.utils import (
    language_metadata,
    data_type_metadata,
)

def pr_body(missing_features):
    # Initialize PR body with a header
    pr_body_content = "## Automated PR: Missing Features\n\n"
    pr_body_content += "This PR was automatically created by a GitHub Action.\n\n"
    pr_body_content += "### Missing Features Summary\n"
    pr_body_content += "| **Language** | **Feature Type** |\n"
    pr_body_content += "|--------------|------------------|\n"
    
    # Iterate over the missing features to populate the table
    for entity, features in missing_features.items():
        # Check for sub-languages
        language_name = None
        for name, data in language_metadata.items():
            if data.get('qid') == entity:
                language_name = name
                break
            if 'sub_languages' in data:
                for sub_name, sub_data in data['sub_languages'].items():
                    if sub_data.get('qid') == entity:
                        language_name = f"{name} ({sub_name})"
                        break
            if language_name:
                break

        # Default to entity if no name is found
        language_name = language_name or entity

        for feature, details in features.items():
            feature_name = next((name for name, qid in data_type_metadata.items() if qid == feature), feature)
            pr_body_content += f"| **{language_name}** | *{feature_name}* |\n"
    
    pr_body_content += "\nPlease review the changes and provide feedback.\n"
    
    return pr_body_content

if __name__ == "__main__":
    # Load missing f eatures from a JSON file
    with open(sys.argv[1], 'r') as f:
        missing_features = json.load(f)
    
    pr_body(missing_features)
 