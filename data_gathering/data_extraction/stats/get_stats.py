import json
import multiprocessing
import os
import random
import re
from time import time
from typing import List

import html2text
from bs4 import BeautifulSoup
from markdownify import ATX, BACKSLASH
from transformers import T5TokenizerFast

from data_gathering.data_extraction.html2markdown import create_md
from data_gathering.data_extraction.tree_modification import (
    simplify_body,
    textify_simplified_head,
)
from data_gathering.data_extraction.utils import get_binary_dicts_templates

PRODUCTS_DIR_PATH = (
    "../../../../../studia/master-thesis/data/02_intermediate/web_pages/products"
)
products_list = os.listdir(PRODUCTS_DIR_PATH)
products_list = random.sample(products_list, 10000)
url_regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

md = create_md(heading_style=ATX, newline_style=BACKSLASH)
tokenizer = T5TokenizerFast.from_pretrained("google/flan-t5-base")

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

class_id_to_exclude = [
    "nav",
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
    "image",
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


def batch_get_stats(dir_path: str, file_names: List[str]):
    print("STARTED one batch!!", len(file_names))

    simplify_lxml_times = []
    simplify_html_parser_times = []
    md_lxml_times = []
    md_html_parser_times = []

    sizes_lxml = []
    sizes_html_parser = []

    for name in file_names:
        with open(f"{dir_path}/{name}", "r") as f:
            html = f.read()

        soup = BeautifulSoup(html, "lxml")

        simplified_soup_head_text = textify_simplified_head(
            soup=soup.head, meta_acceptable_values=meta_values
        )

        try:
            start = time()
            simplified_soup_body = simplify_body(
                soup=soup.body,
                text_formatting_tags=text_formatting_tags,
                tags_to_include=tags_to_include,
            )
            end = time()
            simplify_lxml_times.append(end - start)

            start = time()
            simplified_body_text = md(simplified_soup_body)
            end = time()
            md_lxml_times.append(end - start)

            full_page_text = f"{simplified_soup_head_text}\n{simplified_body_text}"
            full_page_text = re.sub(url_regex, "", full_page_text)

            inputs = tokenizer(full_page_text.strip(), return_tensors="pt")
            sizes_lxml.append(inputs.input_ids.squeeze().shape[0])
        except Exception:
            continue

        soup = BeautifulSoup(html, "html.parser")

        try:
            start = time()
            simplified_soup_body = simplify_body(
                soup=soup.body,
                text_formatting_tags=text_formatting_tags,
                tags_to_include=tags_to_include,
            )
            end = time()
            simplify_html_parser_times.append(end - start)

            start = time()
            simplified_body_text = html2text.html2text(simplified_soup_body.prettify())
            end = time()
            md_html_parser_times.append(end - start)

            full_page_text = f"{simplified_soup_head_text}\n{simplified_body_text}"
            full_page_text = re.sub(url_regex, "", full_page_text)

            inputs = tokenizer(full_page_text.strip(), return_tensors="pt")
            sizes_html_parser.append(inputs.input_ids.squeeze().shape[0])
        except Exception:
            continue

    print("DONE one batch!!")

    return (
        simplify_lxml_times,
        simplify_html_parser_times,
        md_lxml_times,
        md_html_parser_times,
        sizes_lxml,
        sizes_html_parser,
    )


def get_stats(chunked_products_list: List[List[str]]):
    simplify_lxml_times = []
    simplify_html_parser_times = []
    md_lxml_times = []
    md_html_parser_times = []

    sizes_lxml = []
    sizes_html_parser = []

    with multiprocessing.Pool(processes=5) as pool:
        results = [
            pool.apply_async(batch_get_stats, [PRODUCTS_DIR_PATH, file_names])
            for file_names in chunked_products_list
        ]

        for res in results:
            (
                simplify_lxml_times_chunk,
                simplify_html_parser_times_chunk,
                md_lxml_times_chunk,
                md_html_parser_times_chunk,
                sizes_lxml_chunk,
                sizes_html_parser_chunk,
            ) = res.get()

            simplify_lxml_times += simplify_lxml_times_chunk
            simplify_html_parser_times += simplify_html_parser_times_chunk
            md_lxml_times += md_lxml_times_chunk
            md_html_parser_times += md_html_parser_times_chunk
            sizes_lxml += sizes_lxml_chunk
            sizes_html_parser += sizes_html_parser_chunk

    with open("./stats_with_nav.json", "w") as file:
        json.dump(
            {
                "simplify_lxml_times": simplify_lxml_times,
                "simplify_html_parser_times": simplify_html_parser_times,
                "md_lxml_times": md_lxml_times,
                "md_html_parser_times": md_html_parser_times,
                "sizes_lxml": sizes_lxml,
                "sizes_html_parser": sizes_html_parser,
            },
            file,
            indent=4,
        )


def batch_get_tokens_stats(dir_path: str, file_names: List[str]):
    print("STARTED one batch!!", len(file_names))

    sizes = []

    for name in file_names:
        print(name)
        with open(f"{dir_path}/{name}", "r") as f:
            html = f.read()

        soup = BeautifulSoup(html, "html.parser")

        try:
            simplified_soup_head_text = textify_simplified_head(
                soup=soup.head, meta_acceptable_values=meta_values
            )

            simplified_soup_body = simplify_body(
                soup=soup.body,
                text_formatting_tags=text_formatting_tags,
                tags_to_include=tags_to_include,
                class_id_to_exclude=class_id_to_exclude,
            )
            simplified_body_text = md(simplified_soup_body)

            full_page_text = f"{simplified_soup_head_text}\n{simplified_body_text}"
            # full_page_text = re.sub(url_regex, "", full_page_text)

            inputs = tokenizer(full_page_text.strip(), return_tensors="pt")
            sizes.append(inputs.input_ids.squeeze().shape[0])
        except Exception:
            continue

    print("DONE one batch!!")

    return sizes


def get_tokens_stats(chunked_products_list: List[List[str]]):
    sizes = []

    with multiprocessing.Pool(processes=5) as pool:
        results = [
            pool.apply_async(batch_get_tokens_stats, [PRODUCTS_DIR_PATH, file_names])
            for file_names in chunked_products_list
        ]

        for res in results:
            sizes_chunk = res.get()
            sizes += sizes_chunk

    with open("./stats_without_given_class_id_names_no_urls.json", "w") as file:
        json.dump(sizes, file, indent=4)


def batch_get_different_size_pages(dir_path: str, file_names: List[str]):
    print("STARTED one batch!!", len(file_names))
    num_of_2000 = 0
    num_of_4000 = 0
    num_of_8000 = 0
    num_of_10000 = 0
    num_of_20000 = 0
    max_num_of_each = 5

    for name in file_names:
        with open(f"{dir_path}/{name}", "r") as f:
            html = f.read()

        soup = BeautifulSoup(html, "html.parser")

        simplified_soup_head_text = textify_simplified_head(
            soup=soup.head, meta_acceptable_values=meta_values
        )

        try:
            simplified_soup_body = simplify_body(
                soup=soup.body,
                text_formatting_tags=text_formatting_tags,
                tags_to_include=tags_to_include,
            )
            simplified_body_text = md(simplified_soup_body)

            full_page_text = f"{simplified_soup_head_text}\n{simplified_body_text}"
            full_page_text = re.sub(url_regex, "", full_page_text)

            inputs = tokenizer(full_page_text.strip(), return_tensors="pt")
            size = inputs.input_ids.squeeze().shape[0]
            # print(name, size)

            if size >= 20000 and num_of_20000 <= max_num_of_each:
                print("Found one with 20000 tokens!", size, name)
                with open(f"text_version/20000_tokens/{name}", "w") as f:
                    f.write(full_page_text)

                num_of_20000 += 1
            elif size >= 10000 and num_of_10000 <= max_num_of_each:
                print("Found one with 10000 tokens!", size, name)
                with open(f"text_version/10000_tokens/{name}", "w") as f:
                    f.write(full_page_text)

                num_of_10000 += 1
            elif size >= 8000 and num_of_8000 <= max_num_of_each:
                print("Found one with 8000 tokens!", size, name)
                with open(f"text_version/8000_tokens/{name}", "w") as f:
                    f.write(full_page_text)

                num_of_8000 += 1
            elif size >= 4000 and num_of_4000 <= max_num_of_each:
                print("Found one with 4000 tokens!", size, name)
                with open(f"text_version/4000_tokens/{name}", "w") as f:
                    f.write(full_page_text)

                num_of_4000 += 1
            elif size >= 2000 and num_of_2000 <= max_num_of_each:
                print("Found one with 2000 tokens!", size, name)
                with open(f"text_version/2000_tokens/{name}", "w") as f:
                    f.write(full_page_text)

                num_of_2000 += 1

            if (
                num_of_2000 == max_num_of_each
                and num_of_4000 == max_num_of_each
                and num_of_8000 == max_num_of_each
                and num_of_10000 == max_num_of_each
                and num_of_20000 == max_num_of_each
            ):
                break
        except Exception:
            continue

    print("DONE one batch!!")


def get_different_size_pages(chunked_products_list: List[List[str]]):
    dirs = ["2000_tokens", "4000_tokens", "8000_tokens", "10000_tokens", "20000_tokens"]

    for dir_name in dirs:
        if not os.path.exists(f"text_version/{dir_name}"):
            os.makedirs(f"text_version/{dir_name}")

    with multiprocessing.Pool(processes=5) as pool:
        results = [
            pool.apply_async(
                batch_get_different_size_pages, [PRODUCTS_DIR_PATH, file_names]
            )
            for file_names in chunked_products_list
        ]

        for res in results:
            res.get()


# flake8: noqa: C901
if __name__ == "__main__":
    chunks_number = 5

    chunked_products_list = []
    for i in range(0, len(products_list), len(products_list) // chunks_number):
        chunked_products_list.append(
            products_list[i : i + len(products_list) // chunks_number]
        )

    # get_stats(chunked_products_list)
    # get_different_size_pages(chunked_products_list)
    get_tokens_stats(chunked_products_list)
