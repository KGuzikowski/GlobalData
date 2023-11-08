import re
from typing import Dict, List

import spacy
from bs4 import Tag
from nltk.stem import WordNetLemmatizer

nlp = spacy.load("en_core_web_md")


def flatten_list(main_list: List):
    return [item for sublist in main_list for item in sublist]


def unique_elems_in_order(elems: List):
    return list(dict.fromkeys(elems))


class HTMLAttributesExtractor:
    def __init__(self, abbreviations: Dict[str, str]):
        self.abbreviations = abbreviations

        self.lemmatizer = WordNetLemmatizer()
        self.english_words = set(nlp.vocab.strings)

        self.camel_case_pattern1 = re.compile(r"(.)([A-Z][a-z]+)")
        self.camel_case_pattern2 = re.compile(r"([a-z0-9])([A-Z])")
        self.numbers_pattern = re.compile(r"\d+")
        self.delimiters_pattern = re.compile(r'[-_%”?=".\]@/“:ٍ\\\';&\[]+')

    def from_camel_case_to_sneak_case(self, name: str) -> str:
        name = self.camel_case_pattern1.sub(r"\1_\2", name)
        name = self.camel_case_pattern2.sub(r"\1_\2", name)

        return name.lower()

    def remove_numbers(self, name: str) -> str:
        name = self.numbers_pattern.sub("_", name)

        return name

    def remove_delimiters(self, name: str) -> str:
        name = self.delimiters_pattern.sub(" ", name)

        return name

    def transform_name_base_pipeline(self, name: str) -> List[str]:
        return self.remove_delimiters(
            self.remove_numbers(self.from_camel_case_to_sneak_case(name))
        ).split()

    def get_flat_transformed_word_list(self, values: List[str]) -> List[str]:
        return flatten_list(
            [self.transform_name_base_pipeline(elem) for elem in values]
        )

    def get_allowed_attribute_values(
        self, values: List[str], is_itemtype: bool = False
    ) -> List[str]:
        if is_itemtype and len(values):
            name = values[0].split("/")[-1]
            values = [name]

        words = self.get_flat_transformed_word_list(values)
        final_words = []

        for word in words:
            # expand abbreviations
            word = self.abbreviations.get(word, word)

            if word not in self.english_words or len(word) < 4:
                continue

            word = self.lemmatizer.lemmatize(word)

            final_words.append(word)

        return final_words

    def get_attributes_values(self, v: Tag) -> List[str]:
        values = v.attrs.get("itemprop", [])
        words = self.get_allowed_attribute_values(
            values=values if isinstance(values, list) else [values]
        )

        values = v.attrs.get("itemtype", [])
        words.extend(
            self.get_allowed_attribute_values(
                values=values if isinstance(values, list) else [values],
                is_itemtype=True,
            )
        )

        values = v.attrs.get("class", [])
        words.extend(
            self.get_allowed_attribute_values(
                values=values if isinstance(values, list) else [values],
            )
        )

        values = v.attrs.get("id", [])
        words.extend(
            self.get_allowed_attribute_values(
                values=values if isinstance(values, list) else [values],
            )
        )

        return unique_elems_in_order(words)

    def get_attributes_values_per_kind(self, v: Tag) -> List[str]:
        attrs_text_arr = []

        values = v.attrs.get("itemprop", [])
        words = self.get_allowed_attribute_values(
            values=values if isinstance(values, list) else [values]
        )

        if words:
            attrs_text_arr.append(
                f"item prop: {' '.join(unique_elems_in_order(words))}"
            )

        values = v.attrs.get("itemtype", [])
        words = self.get_allowed_attribute_values(
            values=values if isinstance(values, list) else [values],
            is_itemtype=True,
        )

        if words:
            attrs_text_arr.append(
                f"item type: {' '.join(unique_elems_in_order(words))}"
            )

        values = v.attrs.get("class", [])
        words = self.get_allowed_attribute_values(
            values=values if isinstance(values, list) else [values],
        )

        if words:
            attrs_text_arr.append(f"class: {' '.join(unique_elems_in_order(words))}")

        values = v.attrs.get("id", [])
        words = self.get_allowed_attribute_values(
            values=values if isinstance(values, list) else [values],
        )

        if words:
            attrs_text_arr.append(f"id: {' '.join(unique_elems_in_order(words))}")

        return attrs_text_arr
