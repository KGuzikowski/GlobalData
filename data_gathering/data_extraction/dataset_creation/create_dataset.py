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
The text given below was extracted from a product website page.Extract the following product information from the text:
- title - string
- brand - string
- current price - dictionary with the price as number and the currency as string
- old price - number
- product features - list of dictionaries, each dictionary should contain the feature and its  value, do not include things provided in other points
- short description - string
- colors variants - list of strings
- size variants - list of strings excluding dimensions
- product categories - as list of strings, if not provided then always suggest your own, try to be as general as possible - must always be provided
- customer ratings - dictionary with average_rating and number of ratings of each rating only if such information is strictly provided
- customer reviews - list of strings
- similar or related products - list of strings
- products recommended for me - list of strings
Don't return any size table information.
Never guess, if there's no information return: null.
Return only a proper JSON format using snake case for properties. The text:
"""

input = tokenizer(prompt)
prompt_desc_size = len(input.input_ids)
model_max_input_size = 16000

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

        temps = [0.6, 0.7]
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
