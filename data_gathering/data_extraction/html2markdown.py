from typing import Dict, List, Optional

import regex
from bs4 import Tag
from markdownify import MarkdownConverter
from spacy import Language
from transformers import Pipeline

from data_gathering.data_extraction.const import url_regex_exp
from data_gathering.data_extraction.html_features import HTMLAttributesExtractor


def includes_values(text: str, values: List[str]) -> bool:
    for value in values:
        if text.startswith(value):
            return True

    return False


def exists_and_includes_values(text: Optional[str], values: List[str]) -> bool:
    return bool(text) and includes_values(text, values)


class NoTextToTranslateException(Exception):
    pass


class HtmlAttrsAndTranslationMarkdownConverter(MarkdownConverter):
    def __init__(
        self,
        abbreviations: Dict[str, str],
        meta_acceptable_values: List[str],
        translation_pipeline: Pipeline,
        nlp: Language,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.abbreviations = abbreviations
        self.meta_acceptable_values = meta_acceptable_values
        self.translation_pipeline = translation_pipeline
        self.nlp = nlp

        self.should_translate_to_english = False
        self.attrs_extractor = HTMLAttributesExtractor(abbreviations=abbreviations)
        self.text_lines_to_translate = []

    def textify_body(self, soup: Tag, should_translate_to_english: bool = False):
        self._reset(should_translate_to_english)

        result = self.convert_soup(soup)

        if not self.should_translate_to_english:
            return result

        if not self.text_lines_to_translate:
            raise NoTextToTranslateException("No text to translate")

        translated_text = self.translation_pipeline(
            self.text_lines_to_translate, max_length=512, num_beams=1
        )
        translated_text = [elem["translation_text"] for elem in translated_text]

        result = result.format(*translated_text)
        return result

    def _reset(self, should_translate_to_english: bool = False):
        self.should_translate_to_english = should_translate_to_english
        self.text_lines_to_translate = []

    def _batch_translation_text(self) -> List[str]:
        """
        From the list of text lines to translate, create batches
        of text lines to translate. Add as much text as you can
        to the batch, but don't exceed the max input size.
        Each text line is split by ` [TS] ` (translation separator) token
        and spaces around it.
        """
        batch = []

        for line in self.text_lines_to_translate:
            if len(batch) == 0:
                text_ids = self.tokenizer(line, return_tensors="pt")["input_ids"]
                batch.append([line, text_ids.shape[1]])
            else:
                text = " <T> " + line
                text_ids = self.tokenizer(text, return_tensors="pt")["input_ids"]
                text_len = text_ids.shape[1]

                if text_len + batch[-1][1] > self.translation_model.config.max_length:
                    batch.append([line, text_len])
                else:
                    batch[-1][0] += text
                    batch[-1][1] += text_len

        return [elem[0] for elem in batch]

    def convert_soup(self, soup: Tag) -> str:
        return self.process_tag(
            soup,
            convert_as_inline=False,
            children_only=True,
        )

    def process_tag(
        self, node: Tag, convert_as_inline: bool, children_only: bool = False
    ) -> str:
        attrs_words = self.attrs_extractor.get_attributes_values(node)
        start = " ".join(attrs_words)

        text = super().process_tag(node, convert_as_inline, children_only)

        if start:
            return f"\n- {start}:\n{text}"

        return text

    def process_text(self, el: Tag):
        text = super().process_text(el).strip()

        if self.should_translate_to_english and text and regex.findall(r"\p{L}+", text):
            doc = self.nlp(text)
            sentences = [sent.text for sent in doc.sents]

            self.text_lines_to_translate += sentences
            return "{} " * len(sentences)

        return text

    def _block_meta_tag(
        self, name: Optional[str], prop: Optional[str], content: Optional[str]
    ) -> bool:
        return (
            not bool(content)
            or url_regex_exp.search(content)
            or (
                not exists_and_includes_values(name, self.meta_acceptable_values)
                and not exists_and_includes_values(prop, self.meta_acceptable_values)
            )
        )

    def textify_meta_tags(self, soup: Tag, should_translate_to_english: bool = False):
        self._reset(should_translate_to_english)

        lines_to_translate = []
        chosen_any_tags = False
        text = ""

        for node in soup.findAll("meta"):
            name = node.attrs.get("name", None)
            content = node.attrs.get("content", None)
            prop = node.attrs.get("property", None)

            if self._block_meta_tag(name, prop, content):
                continue

            start = ""
            if name:
                start = " ".join(name.split(":"))
            elif prop:
                start = " ".join(prop.split(":"))

            if should_translate_to_english:
                chosen_any_tags = True
                doc = self.nlp(content)
                sentences = [sent.text for sent in doc.sents]

                lines_to_translate += sentences
                text += f"{start}: " + "{} " * len(sentences) + "\n"
            else:
                text += f"{start}: {content}\n"

        if chosen_any_tags and not lines_to_translate:
            raise NoTextToTranslateException("No meta text to translate")

        translated_text = self.translation_pipeline(
            lines_to_translate, max_length=512, num_beams=1
        )
        translated_text = [elem["translation_text"] for elem in translated_text]

        text = text.format(*translated_text)
        return text
