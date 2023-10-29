import copy
from typing import List, Optional, Union

from bs4 import NavigableString, Tag

from data_gathering.data_extraction.const import url_regex_exp


def handle_text(text: str) -> Optional[str]:
    if url_regex_exp.search(text):
        return None

    text = text.strip().replace("\n", " ")

    if len(text):
        return f" {text}. "


def handle_tag(
    node: Tag,
    text_formatting_tags: set,
    tags_to_include: set,
    class_id_to_exclude: List[str],
):
    child = None

    if node.name == "a":
        child = node
    elif node.name in text_formatting_tags:
        if node.string:
            child = handle_text(node.string)
        elif len(node.contents):
            elements = simplify_body(
                soup=node,
                text_formatting_tags=text_formatting_tags,
                tags_to_include=tags_to_include,
                class_id_to_exclude=class_id_to_exclude,
            )
            return elements
    elif node.name in tags_to_include:
        class_str = " ".join(node.attrs.get("class", [])).lower()
        id_str = node.attrs.get("id", "").lower()

        for name in class_id_to_exclude:
            if name in class_str or name in id_str:
                return None

        child = simplify_body(
            soup=node,
            text_formatting_tags=text_formatting_tags,
            tags_to_include=tags_to_include,
            class_id_to_exclude=class_id_to_exclude,
        )

    return child


def handle_tag_a(
    elem: Tag,
    soup: Tag,
    text_formatting_tags: set,
    tags_to_include: set,
    class_id_to_exclude: List[str],
):
    child = simplify_body(
        soup=elem,
        text_formatting_tags=text_formatting_tags,
        tags_to_include=tags_to_include,
        class_id_to_exclude=class_id_to_exclude,
    )
    if child:
        for node in child.contents:
            soup.append(node)


def simplify_body(
    soup: Tag,
    text_formatting_tags: set,
    tags_to_include: set,
    class_id_to_exclude: List[str],
) -> Optional[Union[List[str], Tag]]:
    """
    Simplifies DOM tree.

    :param class_id_to_exclude: a list containing class or id to exclude
    :type class_id_to_exclude: List[str]
    :param soup: a Tag Object
    :type soup: BeautifulSoup4 Tag
    :param text_formatting_tags: a set containing tags that should remain in the tree
    :type text_formatting_tags: set
    :param tags_to_include: a set containing text formatting tags (like "strong")
    :type tags_to_include: set

    :return: Returns different types which allows to recurrently clean the tree.
    :rtype: Optional[Union[List[str], Tag]]
    """
    if (
        soup.name in tags_to_include
        or soup.name == "a"
        or soup.name in text_formatting_tags
    ):
        children = []

        for node in soup.contents:
            child = None
            if isinstance(node, Tag):
                res = handle_tag(
                    node=node,
                    text_formatting_tags=text_formatting_tags,
                    tags_to_include=tags_to_include,
                    class_id_to_exclude=class_id_to_exclude,
                )

                if isinstance(res, list):
                    children += res
                else:
                    child = res
            elif isinstance(node, NavigableString):
                child = handle_text(node)

            if child:
                children.append(child)

        if len(children) and soup.name in text_formatting_tags:
            return children
        elif len(children):
            soup.contents = []

            for elem in children:
                if isinstance(elem, Tag) and elem.name == "a":
                    handle_tag_a(
                        elem=elem,
                        soup=soup,
                        text_formatting_tags=text_formatting_tags,
                        tags_to_include=tags_to_include,
                        class_id_to_exclude=class_id_to_exclude,
                    )
                else:
                    soup.append(elem)

            soup = copy.copy(soup)
            soup.smooth()

            return soup
