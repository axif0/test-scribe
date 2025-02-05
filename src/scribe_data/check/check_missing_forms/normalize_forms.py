from scribe_data.utils import lexeme_form_metadata
# from scribe_data.check.check_query_forms import lexeme_form_labels_order

def sort_qids_in_list(qids_lists):
    # Create a mapping of QID to its position
    qid_positions = {}
    for category in lexeme_form_metadata.values():
        for item in category.values():
            if "qid" in item:
                qid_positions[item["qid"]] = len(qid_positions)
    
    # Sort each sublist based on position
    return [sorted(qids, key=lambda x: qid_positions.get(x, float('inf'))) for qids in qids_lists]

#--------------------------------------------------

def sort_qids_by_position(nested_qids):
    # Create QID position mapping with category priority
    qid_positions = {}
    for category_index, (category_name, category) in enumerate(lexeme_form_metadata.items()):
        for item in category.values():
            if "qid" in item:
                # Category index * 1000 ensures different categories don't overlap
                qid_positions[item["qid"]] = category_index * 1000 + len(qid_positions)
    
    def get_sort_key(sublist):
        # First priority: length of sublist
        length_priority = len(sublist) * 1000000
        
        # Sort QIDs within the sublist by their positions
        sorted_positions = sorted(qid_positions.get(qid, float('inf')) for qid in sublist)
        
        # Pad with infinity for consistent comparison
        while len(sorted_positions) < 5:  # Assuming max length of 3
            sorted_positions.append(float('inf'))
            
        return [length_priority] + sorted_positions
    
    return sorted(nested_qids, key=get_sort_key)



# def remove_duplicate_form(input_qids):
#     # Sort each sublist before converting to tuple
#     unique_tuples = {tuple(sorted(form)) for form in input_qids}
#     return [list(t) for t in unique_tuples]

 
# input_qids=[['Q146233', 'Q1775415', 'Q110786'], ['Q1775415', 'Q110786', 'Q4239848'], ['Q145599', 'Q499327', 'Q110786'], ['Q145599', 'Q1775461', 'Q110786'], ['Q192997', 'Q1775461', 'Q110786'], ['Q146078', 'Q51927507', 'Q1775461', 'Q110786'], ['Q499327', 'Q110786', 'Q4239848'], ['Q131105', 'Q499327', 'Q110786'], ['Q146233', 'Q1775461', 'Q110786'], ['Q2114906', 'Q499327', 'Q110786'], ['Q146078', 'Q51927539', 'Q146786'], ['Q131105', 'Q499327'], ['Q2114906', 'Q1775461', 'Q110786'], ['Q131105', 'Q1775415', 'Q110786'], ['Q146078', 'Q51927507', 'Q146786'], ['Q1817208'], ['Q192997', 'Q1775415', 'Q110786'], ['Q146078', 'Q1775415', 'Q110786'], ['Q2114906', 'Q146786'], ['Q499327', 'Q110786'], ['Q14169499'], ['Q131105', 'Q1775461', 'Q110786'], ['Q1775461', 'Q110786', 'Q4239848'], ['Q2114906', 'Q1775415', 'Q110786'], ['Q146078', 'Q51927539', 'Q1775461', 'Q110786'], ['Q146078', 'Q51927539', 'Q110786'], ['Q146078', 'Q1775461', 'Q110786'], ['Q146233', 'Q499327', 'Q110786'], ['Q146786'], ['Q192997', 'Q146786'], ['Q146078', 'Q1775415', 'Q51927539', 'Q110786'], ['Q131105', 'Q499327', 'Q146786'], ['Q146078', 'Q499327', 'Q110786'], ['Q146078', 'Q499327', 'Q51927507', 'Q110786'], ['Q192997', 'Q499327', 'Q110786'], ['Q131105', 'Q110786'], ['Q146078', 'Q1775415', 'Q51927507', 'Q110786'], ['Q145599', 'Q1775415', 'Q110786'], ['Q146078', 'Q54020116', 'Q110786'], ['Q146078', 'Q499327', 'Q51927539', 'Q110786'], ['Q1775415', 'Q110786'], ['Q1775461', 'Q110786']]

# print(remove_duplicate_form(input_qids))

# # Test cases
# input_qids = [['Q499327'], ['Q1817208'], ['Q110786'], ['Q499327', 'Q110786'], 
#               ['Q110786', 'Q1817208'], ['Q1775415', 'Q110786'], ['Q146786'], ['Q499327', 'Q146786'],
#                 ['Q146786', 'Q1817208'], ['Q499327', 'Q110786', 'Q1817208'], ['Q1775415', 'Q146786'], 
#                 ['Q1775415', 'Q110786', 'Q1817208'],
#                   ['Q499327', 'Q146786', 'Q1817208'], ['Q1775415', 'Q146786', 'Q1817208'],['Q499327'], ['Q1817208']]


# print(remove_duplicate_form(input_qids))

# sorted_qids = sort_qids_by_position(input_qids)
# print("Sorted QIDs:",sorted_qids)
 
# sort_qids_in_list = [['Q499327'], ['Q1817208'], ['Q110786'], ['Q110786', 'Q499327'], 
#               ['Q110786', 'Q1817208'], ['Q110786', 'Q1775415'], 
#               ['Q146786'], ['Q146786', 'Q499327'], ['Q146786', 'Q1817208'], 
#               ['Q110786', 'Q1817208', 'Q499327'], ['Q146786', 'Q1775415'], 
#               ['Q110786', 'Q1775415', 'Q1817208'],
#               ['Q146786', 'Q1817208', 'Q499327'], 
#               ['Q146786', 'Q1775415', 'Q1817208']]

# sorted_qids = sort_qids_in_list(sort_qids_in_list)
# print(sorted_qids)