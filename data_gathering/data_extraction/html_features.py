import re
from typing import Dict, List, Set

from bs4 import Tag
from nltk.corpus import words
from nltk.stem import WordNetLemmatizer

ENGLISH_WORDS = set(words.words())


def get_camel_case_converter():
    pattern1 = re.compile(r"(.)([A-Z][a-z]+)")
    pattern2 = re.compile(r"([a-z0-9])([A-Z])")

    def from_camel_case_to_sneak_case(name: str) -> str:
        name = pattern1.sub(r"\1_\2", name)
        name = pattern2.sub(r"\1_\2", name)
        return name.lower()

    return from_camel_case_to_sneak_case


def get_numbers_remover():
    pattern = re.compile(r"\d+")

    def remove_numbers(name: str) -> str:
        name = pattern.sub("_", name)
        return name

    return remove_numbers


def get_delimiters_remover():
    pattern = re.compile(r'[-_%”?=".\]@/“:ٍ\\\';&\[]+')

    def remove_delimiters(name: str) -> str:
        name = pattern.sub(" ", name)
        return name

    return remove_delimiters


lemmatizer = WordNetLemmatizer()
from_camel_case_to_sneak_case = get_camel_case_converter()
remove_numbers = get_numbers_remover()
remove_delimiters = get_delimiters_remover()


def name_base_transforms_pipeline(name: str) -> List[str]:
    return remove_delimiters(
        remove_numbers(from_camel_case_to_sneak_case(name))
    ).split()


def flatten_list(main_list: List):
    return [item for sublist in main_list for item in sublist]


def get_flat_transformed_word_list(values: List[str]) -> List[str]:
    return flatten_list([name_base_transforms_pipeline(elem) for elem in values])


def get_allowed_attribute_values(
    values: List[str], abbreviations: Dict[str, str], is_itemtype: bool = False
) -> Set[str]:
    if is_itemtype and len(values):
        name = values[0].split("/")[-1]
        name = from_camel_case_to_sneak_case(name)

        return {name}

    words = set(get_flat_transformed_word_list(values))
    final_words = set()

    for word in words:
        # expand abbreviations
        word = abbreviations.get(word, word)

        if word not in ENGLISH_WORDS or len(word) < 4:
            continue

        word = lemmatizer.lemmatize(word)

        final_words.add(word)

    return final_words


def get_attributes_values(v: Tag, abbreviations: Dict[str, str]) -> List[str]:
    values = v.attrs.get("itemprop", [])
    words = get_allowed_attribute_values(
        values=values if type(values) == list else [values], abbreviations=abbreviations
    )

    values = v.attrs.get("itemtype", [])
    words = words.union(
        get_allowed_attribute_values(
            values=values if type(values) == list else [values],
            abbreviations=abbreviations,
            is_itemtype=True,
        )
    )

    values = v.attrs.get("class", [])
    words = words.union(
        get_allowed_attribute_values(
            values=values if type(values) == list else [values],
            abbreviations=abbreviations,
        )
    )

    values = v.attrs.get("id", [])
    words = words.union(
        get_allowed_attribute_values(
            values=values if type(values) == list else [values],
            abbreviations=abbreviations,
        )
    )

    return list(words)
