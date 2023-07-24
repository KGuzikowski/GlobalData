from typing import Dict

from bs4 import Tag
from markdownify import MarkdownConverter

from data_gathering.data_extraction.html_features import get_attributes_values

# Create shorthand method for conversion
# def create_md(**options):
#     converter = MarkdownConverter(**options)
#
#     def md(soup: Tag):
#         return converter.convert_soup(soup)
#
#     return md


class CustomMarkdownConverter(MarkdownConverter):
    def __init__(self, abbreviations: Dict[str, str], **options):
        super().__init__(**options)
        self.abbreviations = abbreviations

    def process_tag(self, node, convert_as_inline, children_only=False):
        attrs_words = get_attributes_values(node, self.abbreviations)
        start = " ".join(attrs_words)
        text = super().process_tag(node, convert_as_inline, children_only)
        if start:
            start = f"\n- {start}:"
        return f"{start}\n{text}" if start else text


# Create shorthand method for conversion
def create_md(abbreviations: Dict[str, str], **options):
    converter = CustomMarkdownConverter(abbreviations=abbreviations, **options)

    def md(soup: Tag):
        return converter.convert_soup(soup)

    return md
