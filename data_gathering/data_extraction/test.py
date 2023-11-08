import json

import spacy
from bs4 import BeautifulSoup
from markdownify import ATX, BACKSLASH
from transformers import pipeline

from data_gathering.data_extraction.html2markdown import (
    HtmlAttrsAndTranslationMarkdownConverter,
)
from data_gathering.data_extraction.tree_modification import simplify_body
from data_gathering.data_extraction.utils import get_binary_dicts_templates

translator = pipeline("translation", model="Helsinki-NLP/opus-mt-pl-en")

nlp = spacy.load(
    "pl_core_news_sm",
    disable=[
        "tagger",
        "ner",
        "morphologizer",
        "lemmatizer",
        "attribute_ruler",
        "parser",
        "tok2vec",
    ],
)
nlp.enable_pipe("senter")

with open("dataset_creation_config.json", "r") as file:
    config = json.load(file)

tags_to_include = set(config["tags"])
text_formatting_tags = set(config["text_formatting_tags"])
abbreviations = config["abbreviations"]
meta_values = config["meta_values"]
(
    available_tags_binary_dict,
    available_attributes_values_binary_dict,
) = get_binary_dicts_templates(config)

class_id_to_exclude = [
    "nav",
    "tooltip",
    "banner",
    "footer",
    "shipping",
    "popup",
    "checkout",
    "payments",
    "returns",
    "delivery",
    "support",
    "warranty",
    "privacy",
    "benefit",
    "sign-in",
    "sign-up",
    "login",
    "password",
    "add-to-cart",
    "announcement",
    "notification",
    "wishlist",
    "social",
    "json",
    "alert",
    "disclaimer",
    "contact",
    "cookies",
    "newsletter",
    "basket",
    "askforproduct",
    "ask-about-product",
    "mobile-header",
    "header-menu",
    "customer",
]

markdown_converter = HtmlAttrsAndTranslationMarkdownConverter(
    abbreviations=abbreviations,
    meta_acceptable_values=meta_values,
    translation_pipeline=translator,
    nlp=nlp,
    heading_style=ATX,
    newline_style=BACKSLASH,
)

file_name = "polish_answear_160.html"

with open(f"web_pages/all_domains/pages/{file_name}", "r") as file:
    html = file.read()

soup = BeautifulSoup(html, "html.parser")

simplified_soup_body = simplify_body(
    soup=soup.body,
    text_formatting_tags=text_formatting_tags,
    tags_to_include=tags_to_include,
    class_id_to_exclude=class_id_to_exclude,
)

should_translate_to_english = file_name.startswith("polish")

simplified_body_text = markdown_converter.textify_body(
    simplified_soup_body, should_translate_to_english
)
# meta_tags_string = markdown_converter.textify_meta_tags(
#     soup=soup, should_translate_to_english=should_translate_to_english
# )

print(simplified_body_text)
with open("res.txt", "w") as file:
    file.write(simplified_body_text)
