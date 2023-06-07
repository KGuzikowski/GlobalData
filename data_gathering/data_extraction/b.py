import json
import re

from bs4 import BeautifulSoup, Tag
from markdownify import ATX, BACKSLASH, MarkdownConverter
from tree_modification import simplify_body, textify_simplified_head
from utils import get_binary_dicts_templates

with open("dataset_creation_config.json", "r") as file:
    config = json.load(file)

tags_to_include = set(config["tags"])
text_formatting_tags = set(config["text_formatting_tags"])
meta_values = config["meta_values"]
abbreviations = config["abbreviations"]
(
    available_tags_binary_dict,
    available_attributes_values_binary_dict,
) = get_binary_dicts_templates(config)


# Create shorthand method for conversion
def create_md(**options):
    converter = MarkdownConverter(**options)

    def md(soup: Tag):
        return converter.convert_soup(soup)

    return md


md = create_md(heading_style=ATX, newline_style=BACKSLASH)

# flake8: noqa: E501
url_regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

with open(
    "web_pages/all_domains/broken_pages/english_charmingcharlie_2444.html", "r"
) as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")

simplified_soup_body = simplify_body(
    soup=soup.body,
    text_formatting_tags=text_formatting_tags,
    tags_to_include=tags_to_include,
)
simplified_body_text = md(simplified_soup_body)
simplified_soup_head_text = textify_simplified_head(
    soup=soup.head, meta_acceptable_values=meta_values
)

full_page_text = f"{simplified_soup_head_text}\n{simplified_body_text}"
full_page_text = re.sub(url_regex, "", full_page_text)

with open("english_charmingcharlie_2444_1.txt", "w") as f:
    f.write(full_page_text)
