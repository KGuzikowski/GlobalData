from bs4 import Tag
from markdownify import MarkdownConverter


# Create shorthand method for conversion
def create_md(**options):
    converter = MarkdownConverter(**options)

    def md(soup: Tag):
        return converter.convert_soup(soup)

    return md
