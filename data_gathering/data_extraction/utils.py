from typing import Dict, List, Tuple, Union


def get_binary_dicts_templates(
    config: Dict[str, Union[List[str], Dict[str, str]]]
) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    Creates dictionary templates filled with zeros to mark the presence of a given
        word in an attr or tag name. This will be easily turned into a binary vector.

    :param config: a dict that holds data needed for dataset creation,
        eg. text attributes words, tags names, etc.
    :type config: Dict[str, Union[List[str], Dict[str, str]]]

    :return: a tuple of template binary dictionaries filled with zeros
        one for one hot vector for the tag name
        and one consisting of three others for each attribute.
    :rtype: Tuple[Dict[str, int], Dict[str, Dict[str, int]]]
    """
    available_tags_binary_dict = {}
    for tag in config["tags"]:
        available_tags_binary_dict[tag] = 0

    available_attributes_values_binary_dict = {}
    for name in config["attributes_values"]:
        available_attributes_values_binary_dict[name] = 0

    return available_tags_binary_dict, available_attributes_values_binary_dict
