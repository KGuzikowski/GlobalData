## Translation
- **pl** to **eng** translation is best done by the `sparknlp` and `pyspark` with `opus_mt_pl_en` model.
- **eng** to **pl** translation is best done by 

## Plan
I need to create a product extraction details dataset that will be used to fine tune the T5 model.
T5 will be used to extract product details from the product pages and it will be using english language only.

### Data
Pages in polish will be translated to english (results will be later translated back to polish) and then the product details will be extracted.
ChatGPT will be used to construct the final dataset.

## Steps
1. Create dataset and train T5 model to extract product details from the product pages. (need to modify web page simplification algorithms)
2. Create a data scraping and data extraction simplification/modification pipeline (preferably in RUST).
3. Create a web platform that will allow users to create their own reports based on my data.

# What product info to extract?
- title
- brand
- price
- quantity (of each size)
- discounts
- description
- specifications
- material
- measurements
- sizes
- categories
- breadcrumbs
- colors
- variants
- ratings
- opinions
- delivery information????
- similar products
- recommended for me
- related products
- Products You May Also Like


Prompt to be used for ChatGPT:
Extract all information about the product from this text from a web store. Extract product title, brand, current price, old price, specifications (including material and dimensions), description, all sizes, all colors, all variants, categories, breadcrumbs, ratings (including number per each rating), opinions, number of available items (for each size) if provided else return null, similar products, products I may also like, related products, recommended for me. Categorize the product yourself (provide one general and one specific category). For each opinion return only the opinion text itself. If there's no information return: null. Answer should be in a proper JSON format. The text:

# How to modify tree modification?
- Don't merge sibling nodes with just text into one. Let them be separate ???? IDK - test both and decide
- include header
- remove title from header?

# Questions
- How to categorize products? How do I say which are similar or the same? The name might not be enough. Maybe I should use the description?

# Uwaga
- remove douglas, ikea, deguns z zbioru danych


# html parser vs lxml:
- lxml simplify time: 0.18664660945099995
- html parser simplify time: 0.10447529040329413

- lxml md time: 0.0016778466235480365
- html parser md time: 0.017234264529081146


All `aside` tags can be removed.

### Classes/ids that can be removed:
#### Most important ones:
- nav
- banner
- footer
- shipping
- popup
- checkout
- payments
- returns
- delivery
- support
- warranty

#### Rest:
- privacy
- benefit
- sign-in
- sign-up
- login
- password
- add-to-cart
- announcement
- notification
- wishlist
- social
- json
- alert
- disclaimer
- contact
- cookies
- newsletter
- basket
- askforproduct
- ask-about-product
- mobile-header
- header-menu
- customer


limoniapps????
