import time
import os
from selenium import webdriver
from bs4 import BeautifulSoup

ROOT_URL = "https://www.fu.gov.si/podrocja/"
PROCESSED_DATA_DIR = "/Users/juankostelec/Google_drive/Projects/tax_backend/data"

"""
Plan:
(all local)
1. Access the website with the scraper 
2. Determine the "Podrocja" 
3. Create main table from the initial page: extact podrocje descriptionm, ...
3. Loop through the text & files in each "Podrocje"
4. Access the website and check the html of the website
5. Scrape the website
6. Make fucntion to link a specific law article to the URL where it can be foud
7. Deploy the code a database and server --> figure out deployment options

Database logic:

ID table:
podrocje_id: string (primary key)
podrocje: string
podrocje_description
pravilnik_id: string
zakonodaja_id: string
pojasnila_id: string

Zakonodaja table:
zakonodaja_id: string (primary key)
law_article: string
article_text: string
article_embedding: string

Pojasnila table:
pojasnila_id: string (primary key)
article: string/number  --> What if there are multiple levels, but not all mandatory
article_text: string
article_embedding: floats



There is a shit ton of different tables and laws, I don't really know how to structure them.

MVP: Just do the one related to the Davki!!, but complete it

"""


def get_website_html(url, exit_driver=False):
    driver.get(url)

    # Give the page some time to load all contents.
    # This is important especially for webpages with dynamic content.
    time.sleep(2)

    # Fetch the HTML source code of the webpage
    html = driver.page_source

    # Create a BeautifulSoup instance with the HTML source code
    soup = BeautifulSoup(html, "html.parser")

    if exit_driver:
        # Remember to close the WebDriver instance
        driver.quit()

    return soup


def extract_podrocja_titles(soup):
    driver.get(url)

    # Give the page some time to load all contents.
    # This is important especially for webpages with dynamic content.
    time.sleep(2)

    anchor_elements_with_title = driver.find_elements(By.XPATH, "//a[@title]")
    titles = [element.get_attribute("title") for element in anchor_elements_with_title]
    podrocja = [item for item in titles if ("Odpri vsebino" in item or "Zapri vsebino" in item)]


def extract_article_urls(url):
    soup = get_webpage(url)
    print(soup)

    # # function to extract information based on the node level
    # def process_node(node, hierarchy):
    #     node_id = node.get("id", "")
    #     node_text = node.find("a").text if node.find("a") else None

    #     # Determine the node level and update hierarchy dictionary
    #     if "TIT_" in node_id and "CHP_" not in node_id:
    #         hierarchy["title_info"] = node_text
    #     elif "CHP_" in node_id and "SEC_" not in node_id:
    #         hierarchy["chapter_info"] = node_text
    #     elif "SEC_" in node_id and "SUB_" not in node_id:
    #         hierarchy["section_info"] = node_text
    #     elif "SUB_" in node_id:
    #         hierarchy["subsection_info"] = node_text
    #     elif "ART_" in node_id:  # Extract information for 'toc-leaf' nodes
    #         article_name = node_text
    #         article_url = node.find("a")["href"] if node.find("a") and "href" in node.find("a").attrs else None
    #         rows.append(
    #             {
    #                 "title_info": hierarchy.get("title_info", None),
    #                 "chapter_info": hierarchy.get("chapter_info", None),
    #                 "section_info": hierarchy.get("section_info", None),
    #                 "subsection_info": hierarchy.get("subsection_info", None),
    #                 "article_name": article_name,
    #                 "article_url": article_url,
    #             }
    #         )

    #     # Recursively process the children nodes
    #     list_node = node.find("ul", class_="w3-ul", recursive=False)
    #     if list_node:
    #         for child_node in list_node.find_all("li", recursive=False):
    #             process_node(child_node, hierarchy.copy())

    # # Use BeautifulSoup to find all 'li' elements with class 'toc-node' at the top level
    # rows = []
    # root_node = soup.find_all("ul", id="toccordion", recursive=True)
    # assert len(root_node) == 1
    # root_node = root_node[0]
    # title_nodes = root_node.find_all("li", class_="toc-node", recursive=False)
    # for title_node in title_nodes:
    #     process_node(title_node, {})
    # df = pd.DataFrame(rows)
    # return df


# @retry(ValueError, tries=3, delay=2)
# def extract_article_text(law_url, article_url):
#     complete_url = law_url + article_url
#     soup = get_webpage(complete_url)
#     paragraphs = []

#     # Find the div that contains the article
#     article_node = soup.find("div", id="article")

#     # Find all the paragraphs in the article div
#     extracted_paragraphs = article_node.find_all("p")

#     # Extract text from all paragraphs
#     for p in extracted_paragraphs:
#         paragraphs.append(p.get_text(strip=False))

#     output_text = "\n".join(paragraphs)
#     if output_text is None or output_text == "":
#         raise ValueError

#     return output_text


# def scrape_articles_from_website(root_url, law_url, df_partial=None):
#     # Get the articles and their higher level information
#     df_required_info = extract_article_urls(law_url)

#     # Loop over the articles. If we already have partially extracted
#     # only loop over the missing articles
#     if df_partial is not None:
#         df_missing_info = df_partial[df_partial["article_text"].apply(lambda x: len(x[13:]) == 0)][
#             ["article_name"]
#         ]  # TODO: hacky, not robust
#         df_complete_info = pd.merge(df_partial, df_missing_info, how="outer", indicator=True)
#         df_complete_info = df_complete_info[df_complete_info["_merge"] == "left_only"].drop(columns=["_merge"])
#         df_required_info = pd.merge(df_required_info, df_missing_info, on="article_name", how="inner")

#     # Loop over the rows and extract the article text
#     article_text_list = []
#     for idx, row in tqdm.tqdm(df_required_info.iterrows()):
#         text = extract_article_text(root_url, row["article_url"][4:])
#         article_text_list.append(text)

#     df_required_info["article_text"] = article_text_list
#     if df_partial is not None:
#         df_complete = pd.concat([df_complete_info, df_required_info], ignore_index=True, axis=0)
#         df_complete = df_complete.drop(columns=["_merge"])
#     else:
#         df_complete = df_required_info

#     return df_complete


if __name__ == "__main__":
    from selenium.webdriver.common.by import By

    driver = webdriver.Chrome()
    result = get_webpage(ROOT_URL)
    print(result)
    print(titles)

    driver.quit()
