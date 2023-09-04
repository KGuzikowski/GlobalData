from typing import Callable, Dict

from bs4 import Tag
from markdownify import MarkdownConverter
from transformers import Pipeline

from data_gathering.data_extraction.html_features import get_attributes_values


class CustomMarkdownConverter(MarkdownConverter):
    def __init__(
        self,
        abbreviations: Dict[str, str],
        translator: Pipeline,
        extract_translation: Callable,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.abbreviations = abbreviations
        self.should_translate_to_english = False
        self.translator = translator
        self.extract_translation = extract_translation

    def convert_soup(self, soup):
        return self.process_tag(
            soup,
            convert_as_inline=False,
            children_only=True,
        )

    def process_tag(self, node, convert_as_inline, children_only=False):
        attrs_words = get_attributes_values(node, self.abbreviations)
        start = " ".join(attrs_words)

        text = super().process_tag(node, convert_as_inline, children_only)

        if start:
            start = f"\n- {start}:"
        return f"{start.strip()}\n{text.strip()}" if start else text.strip()

    def process_text(self, el):
        text = super().process_text(el)

        if self.should_translate_to_english and text:
            text = self.extract_translation(self.translator(text))

        return text


def create_md(**options):
    converter = CustomMarkdownConverter(**options)

    def md(soup: Tag, should_translate_to_english: bool = False):
        converter.should_translate_to_english = should_translate_to_english
        return converter.convert_soup(soup)

    return md
