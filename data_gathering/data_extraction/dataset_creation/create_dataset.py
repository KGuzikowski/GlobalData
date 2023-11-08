import gc
import json
import os

import openai
import spacy
import torch
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from markdownify import ATX, BACKSLASH
from transformers import pipeline

from data_gathering.data_extraction.html2markdown import (
    HtmlAttrsAndTranslationMarkdownConverter,
)
from data_gathering.data_extraction.tree_modification import simplify_body
from data_gathering.data_extraction.utils import get_binary_dicts_templates

load_dotenv()

API_KEY = os.getenv("OPEN_AI_API_KEY")

openai.api_key = API_KEY

with open("../dataset_creation_config.json", "r") as file:
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
    "banner",
    "footer",
    "tooltip",
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

translator = pipeline(
    "translation", model="Helsinki-NLP/opus-mt-pl-en", device="cuda:0", batch_size=128
)

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

markdown_converter = HtmlAttrsAndTranslationMarkdownConverter(
    abbreviations=abbreviations,
    meta_acceptable_values=meta_values,
    translation_pipeline=translator,
    nlp=nlp,
    heading_style=ATX,
    newline_style=BACKSLASH,
)

# flake8: noqa: C901
prompt = """
The text given below was extracted from a product website page. Extract the following product information from the text:
- title - a string
- brand - a string
- current price - a number
- old price - a number
- currency - a string
- product features and specifications - returns all product features and specifications included in text and relevant to the product itself (describing it). Return a list of dictionaries containing present product features and specifications. Each dictionary should contain the feature name as "feature" and its value as "value". The important thing is that you must provide all the features and specifications you can find. Split features into separate points. Remember to never provide a description. Name this field "product_features".
- short description - a string as a meaningful short description of the product
- available colors - a  list of strings
- available size variants - a list of strings. Don't ever include any product dimensions, quantity, and size table information information. If products come in only one universal size return a word (string) default.
- product categories - a list of strings. Use categories from the text to come up with your own categories. If no information is provided in the text create your own categories. Try to be as general and precise as possible. Remember, this field must always be provided.
- customer ratings - a dictionary with the average rating and each separate rating with their number (if that information is strictly provided otherwise if each rating with a number is not provided return only the mean rating and overall number of ratings)
- customer reviews - return all customer reviews (opinions) as a list of strings
- similar or related products - a list of strings consisting of similar products
- products recommended for me - a list of strings consisting of products recommended for me
Don't return any size table information or delivery information. Return each number as a number, not a string.
Never guess unless you're asked to, if there's no information return: null.
Return only a proper JSON format using snake case for properties. The text:
"""

if not os.path.exists(f"results"):
    os.makedirs(f"results")

DIR_PATH = "../web_pages/all_domains/pages"

files = os.listdir(DIR_PATH)
files.sort()

for i, file_name in enumerate(files):
    torch.cuda.empty_cache()
    gc.collect()
    print()
    print(f"File: {file_name}")

    dir_name = file_name.replace(".", "_")

    if not os.path.exists(f"results/{dir_name}"):
        os.makedirs(f"results/{dir_name}")

    if len(os.listdir(f"results/{dir_name}")) == 2:
        print("Already done")
        continue

    with open(f"{DIR_PATH}/{file_name}", "r") as file:
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
        soup=simplified_soup_body,
        should_translate_to_english=should_translate_to_english,
    )

    meta_tags_str = markdown_converter.textify_meta_tags(
        soup=soup, should_translate_to_english=should_translate_to_english
    )

    full_page_text_curr = f"{meta_tags_str}\n{simplified_body_text}".strip()

    # with open("results/simplified_text.txt", "w") as file:
    #     file.write(full_page_text_curr)

    temps = [0.6, 0.7]  # 0.7 is the best
    for temp in temps:
        print(f"Temperature: {temp}")

        file_name = str(temp).replace(".", "_")
        if file_name in os.listdir(f"results/{dir_name}"):
            print("Already done")
            continue

        chat_gpt_prompt = f"{prompt}\n{full_page_text_curr}"
        # print(chat_gpt_prompt)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            temperature=temp,
            messages=[{"role": "user", "content": chat_gpt_prompt}],
        )

        # save the response to txt file
        with open(f"results/{dir_name}/{file_name}.json", "w") as f:
            f.write(response["choices"][0]["message"]["content"])
