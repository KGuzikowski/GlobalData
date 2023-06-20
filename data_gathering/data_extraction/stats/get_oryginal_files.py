import json
import os
import shutil

from bs4 import BeautifulSoup

from data_gathering.data_extraction.tree_modification import simplify_body
from data_gathering.data_extraction.utils import get_binary_dicts_templates

PRODUCTS_DIR_PATH = (
    "../../../../../studia/master-thesis/data/02_intermediate/web_pages/products"
)
dirs = ["2000_tokens", "4000_tokens", "8000_tokens", "10000_tokens", "20000_tokens"]

with open("../dataset_creation_config.json", "r") as file:
    config = json.load(file)

tags_to_include = set(config["tags"])
text_formatting_tags = set(config["text_formatting_tags"])
meta_values = config["meta_values"]
abbreviations = config["abbreviations"]
(
    available_tags_binary_dict,
    available_attributes_values_binary_dict,
) = get_binary_dicts_templates(config)

for dir_name in dirs:
    files = os.listdir(f"text_version/{dir_name}")

    # if not os.path.exists(f"original_pages_html/{dir_name}"):
    #     os.makedirs(f"original_pages_html/{dir_name}")

    if not os.path.exists(f"simplified_pages_html/{dir_name}"):
        os.makedirs(f"simplified_pages_html/{dir_name}")

    for file in files:
        # copy originals
        shutil.copy(
            f"{PRODUCTS_DIR_PATH}/{file}", f"original_pages_html/{dir_name}/{file}"
        )

        # create simplified versions
        with open(f"original_pages_html/{dir_name}/{file}", "r") as f:
            html = f.read()

        soup = BeautifulSoup(html, "html.parser")

        simplified_soup_body = simplify_body(
            soup=soup.body,
            text_formatting_tags=text_formatting_tags,
            tags_to_include=tags_to_include,
        )

        with open(f"simplified_pages_html/{dir_name}/{file}", "w") as f:
            f.write(simplified_soup_body.prettify())
