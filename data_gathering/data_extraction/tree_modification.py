import copy
from typing import List, Optional, Union

from bs4 import NavigableString, Tag


def handle_text(node: str) -> Optional[str]:
    text = node.strip().replace("\n", " ")

    if len(text):
        return f" {text} "


def handle_tag(node: Tag, text_formatting_tags: set, tags_to_include: set):
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
            )
            return elements
    elif node.name in tags_to_include:
        child = simplify_body(
            soup=node,
            text_formatting_tags=text_formatting_tags,
            tags_to_include=tags_to_include,
        )

    return child


def handle_tag_a(elem: Tag, soup: Tag, text_formatting_tags: set, tags_to_include: set):
    child = simplify_body(
        soup=elem,
        text_formatting_tags=text_formatting_tags,
        tags_to_include=tags_to_include,
    )
    if child:
        for node in child.contents:
            soup.append(node)


def simplify_body(
    soup: Tag, text_formatting_tags: set, tags_to_include: set
) -> Optional[Union[List[str], Tag]]:
    """
    Simplifies DOM tree.

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
                )

                if type(res) == list:
                    children += res
                else:
                    child = res
            elif isinstance(node, NavigableString) and type(node) == NavigableString:
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
                    )
                else:
                    soup.append(elem)

            soup = copy.copy(soup)
            soup.smooth()

            return soup


def includes_values(text: str, values: List[str]) -> bool:
    for value in values:
        if value in text:
            return True

    return False


def textify_simplified_head(soup: Tag, meta_acceptable_values: List[str]):
    assert soup.name == "head"

    text = ""

    for node in soup.contents:
        if isinstance(node, Tag):
            if node.name == "meta":
                name = node.attrs.get("name", None)
                content = node.attrs.get("content", None)
                property = node.attrs.get("property", None)

                if content is None or (
                    (name is None or not includes_values(name, meta_acceptable_values))
                    and (
                        property is None
                        or not includes_values(property, meta_acceptable_values)
                    )
                ):
                    continue

                start = (
                    " ".join(name.split(":"))
                    if name
                    else (" ".join(property.split(":")) if property else "")
                )

                text += f"{start}: {content}\n"

    return text
