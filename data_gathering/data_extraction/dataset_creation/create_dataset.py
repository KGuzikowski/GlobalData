import json
import os

import openai
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv
from markdownify import ATX, BACKSLASH
from transformers import T5TokenizerFast

from data_gathering.data_extraction.html2markdown import create_md
from data_gathering.data_extraction.tree_modification import (
    simplify_body,
    textify_meta_tags,
)
from data_gathering.data_extraction.utils import get_binary_dicts_templates

load_dotenv()

API_KEY = os.getenv("OPEN_AI_API_KEY")

openai.api_key = API_KEY

tokenizer = T5TokenizerFast.from_pretrained("google/flan-t5-base")

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

md = create_md(abbreviations=abbreviations, heading_style=ATX, newline_style=BACKSLASH)

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


def join_tags(elems, tag_name):
    html = ""

    for partial_html, _ in elems:
        html += partial_html

    html = f"<{tag_name}>{html}</{tag_name}>"

    return html


def join_as_many_tags_as_possible(parts, max_size: int, tag_name="body"):
    final = []
    temp = []
    curr_len = 0

    for part, size in parts:
        if temp:
            if curr_len + size <= max_size:
                temp.append((part, size))
                curr_len += size
            else:
                final.append((join_tags(temp, tag_name), curr_len))
                temp = [(part, size)]
                curr_len = size
        else:
            temp = [(part, size)]
            curr_len = size

    if temp:
        final.append((join_tags(temp, tag_name), curr_len))

    return final


def divide_html_version(soup, transform_html_func, max_size):
    text = tokenizer(transform_html_func(soup)).input_ids
    size = len(text)

    if size <= max_size:
        return str(soup), size

    parts = []

    for elem in soup.contents:
        res = (
            divide_html_version(
                soup=elem, transform_html_func=transform_html_func, max_size=max_size
            )
            if isinstance(elem, Tag)
            else (str(elem), len(tokenizer(str(elem)).input_ids))
        )

        if res is None:
            return None
        elif isinstance(res, list):
            parts += res
        else:
            parts.append(res)

    return join_as_many_tags_as_possible(
        parts=parts, max_size=max_size, tag_name=soup.name
    )


def get_max_input_size(
    model_max_input_size: int,
    prompt_desc_size: int,
    header_md: str,
    tokenizer: T5TokenizerFast,
) -> int:
    return model_max_input_size - prompt_desc_size - len(tokenizer(header_md).input_ids)


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

input = tokenizer(prompt)
prompt_desc_size = len(input.input_ids)
print(f"Prompt description size: {prompt_desc_size}")
model_max_input_size = 16384

DIR_PATH = "../web_pages/all_domains/pages"

files = os.listdir(DIR_PATH)
files.sort()

for i, file_name in enumerate(files):
    print()
    print(f"File: {file_name}")

    dir_name = file_name.replace(".", "_")
    if not os.path.exists(f"results/{dir_name}"):
        os.makedirs(f"results/{dir_name}")

    with open(f"{DIR_PATH}/{file_name}", "r") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    simplified_soup_body = simplify_body(
        soup=soup.body,
        text_formatting_tags=text_formatting_tags,
        tags_to_include=tags_to_include,
        class_id_to_exclude=class_id_to_exclude,
    )
    simplified_body_text = md(simplified_soup_body)

    meta_tags_str = textify_meta_tags(
        soup=soup.head, meta_acceptable_values=meta_values
    )

    max_input_size = get_max_input_size(
        model_max_input_size, prompt_desc_size, meta_tags_str, tokenizer
    )

    res = divide_html_version(
        simplified_soup_body, transform_html_func=md, max_size=max_input_size
    )

    print(f"Divided into {len(res) if isinstance(res, list) else 1} parts")

    if isinstance(res, list):
        pass
    else:
        res = [res]

    for i, elem in enumerate(res):
        print(f"Webpage part {i+1} of {len(res)}")
        elem_soup = BeautifulSoup(elem[0], "html.parser")

        simplified_elem_text = md(elem_soup)
        full_page_text_curr = f"{meta_tags_str}\n{simplified_elem_text}"

        chat_gpt_prompt = f"{prompt}\n{full_page_text_curr}"

        temps = [0.7]
        for temp in temps:
            subdir_name = str(temp).replace(".", "_")
            if not os.path.exists(f"results/{dir_name}/{subdir_name}"):
                os.makedirs(f"results/{dir_name}/{subdir_name}")

            if f"part_{i}.json" in os.listdir(f"results/{dir_name}/{subdir_name}"):
                print(f"Temperature: {temp} already done!")
                continue

            print(f"Temperature: {temp}")
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k",
                temperature=temp,
                messages=[{"role": "user", "content": chat_gpt_prompt}],
            )

            # save the response to txt file
            with open(f"results/{dir_name}/{subdir_name}/part_{i}.json", "w") as f:
                f.write(response["choices"][0]["message"]["content"])
