import json
from strsimpy.levenshtein import Levenshtein
from strsimpy.jaro_winkler import JaroWinkler
from strsimpy.normalized_levenshtein import NormalizedLevenshtein

levenshtein = Levenshtein()
jaro = JaroWinkler()
n_l = NormalizedLevenshtein()



# https://github.com/luozhouyang/python-string-similarity?tab=readme-ov-file#weighted-levenshtein


## function to open file with groundtruth and reads json as dict
def read_json(path_to_json_file):
    with open(path_to_json_file) as json_data:
        df = json.load(json_data)
        json_data.close()
        return df
    
def simple_compare(ground_truth, parsing_result):
    keys = ['client', 'creation_date', 'drawing_name/ plan type', 'project_name', 'location', 'scale', 'architect']
    all_keys = len(keys)
    matched = 0
    for key in keys:
        groundt_truth_field = str(ground_truth[key]).lower().strip()
        result_field = str(parsing_result[key]).lower().strip()
        if groundt_truth_field == result_field:
            matched = matched + 1
    accuracy = matched/all_keys
    return accuracy

def calc_levensthein(ground_truth, parsing_result):
    keys = ['client', 'creation_date', 'drawing_name/ plan type', 'project_name', 'location', 'scale', 'architect']
    for key in keys:
        gt_v = str(ground_truth[key])
        r_v = str(parsing_result[key])
        result_leven = levenshtein.distance(gt_v,r_v)
        print("Levensthein Distance: " + gt_v +","+r_v + "  "+ str(result_leven))

def normalized_levensthein(ground_truth, parsing_result):
    keys = ['client', 'creation_date', 'drawing_name/ plan type', 'project_name', 'location', 'scale', 'architect']
    for key in keys:
        gt_v = str(ground_truth[key])
        r_v = str(parsing_result[key])
        result_leven = n_l.distance(gt_v,r_v)
        print("Normalized Levensthein Distance: " + gt_v +","+r_v + "  "+ str(result_leven))
        similarity = str(1-result_leven)
        print("Similarity: " + similarity)

def jaro_winkler(ground_truth, parsing_result):
    keys = ['client', 'creation_date', 'drawing_name/ plan type', 'project_name', 'location', 'scale', 'architect']
    for key in keys:
        gt_v = str(ground_truth[key])
        r_v = str(parsing_result[key])
        result_leven = jaro.distance(gt_v,r_v)
        print("Jaro Winkler " + gt_v +", "+r_v + "  "+ str(result_leven))


def validate(path_to_json, parsing_result):
    ground_truth = read_json(path_to_json)
    accuracy = simple_compare(ground_truth, parsing_result)
    print("The accuracy of the parser equals" + str(accuracy))

def test2(path_to_json, parsing_result):
    ground_truth = read_json(path_to_json)
    calc_levensthein(ground_truth, parsing_result)
    normalized_levensthein(ground_truth, parsing_result)
    jaro_winkler(ground_truth, parsing_result)


def test(string1, string2):
    print(string1,string2)
    len_str1= len(string1)
    len_str2= len(string2)
    print(levenshtein.distance(string1,string2))
    print("Total length str1+str2 "+ str(len_str1+len_str2))
    