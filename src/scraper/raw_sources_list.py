"""
This script crawls the fu.gov.si website and extracts all the references denoted there that cover most of the
areas of tax laws.
"""
import os
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import yaml


FILE_EXTENSIONS = ["docx", "doc", "pdf", "zip", "xlsx"]
ROOT_URL = "https://www.fu.gov.si"
MAIN_URL = ROOT_URL + "/podrocja"
SRC_DIR = "/Users/juankostelec/Google_drive/Projects/tax_backend/src"
METADATA_DIR = "/Users/juankostelec/Google_drive/Projects/tax_backend/data"
RAW_DATA_DIR = "/Users/juankostelec/Google_drive/Projects/tax_backend/data/raw_files"
PROCESSED_DATA_DIR = "/Users/juankostelec/Google_drive/Projects/tax_backend/data/processed_files"

# Open a yaml file with the configurations
with open(os.path.join(SRC_DIR, "configs.yaml"), "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
    print(config)


def extract_davcna_podrocja_info(metadata_dir):
    """
    First we extract all the URL/hrefs from teh website. this includes also hrefs to the same website, but which contain
    additional information on the financial area.

    Next, we just extract these links that contain the descriptions of the financial area, and we enrich the
    rest of the links with this additional information.


    """
    driver = webdriver.Chrome()
    driver.get(MAIN_URL)
    html = driver.page_source
    driver.close()
    soup = BeautifulSoup(html, "html.parser")
    div_content = soup.find("div", id="content")
    podrocja_elements = div_content.find_all("div", class_="card dark")

    data_links = []
    for group_idx, podrocje in enumerate(podrocja_elements):
        anchors = podrocje.find_all("a")
        for podrocje_idx, anchor in enumerate(anchors):
            podrocje_name = anchor.text

            # Get the text inside the <em> element (if it exists)
            em_text = None
            em_element = anchor.find("em")
            if em_element:
                em_text = em_element.text.strip()

            full_text = anchor.text

            # Subtract the <em> text from the full text to get the remaining text
            if em_text:
                remaining_text = full_text.replace(em_text, "").strip()
            else:
                remaining_text = full_text.strip()

            podrocje_name = remaining_text
            podrocje_description = em_text
            href_value = anchor.get("href")
            data_links.append([group_idx, podrocje_idx, podrocje_name, podrocje_description, href_value])

    df = pd.DataFrame(
        data_links, columns=["group_idx", "podrocje_idx", "podrocje_name", "podrocje_description", "href"]
    )

    # Main table corresponds to the href from the main page, with the description of the "Podrocje"
    descr_data = (
        df.query("href == '#'")
        .rename(columns={"podrocje_name": "group", "podrocje_description": "group_description"})
        .drop(columns=["href", "podrocje_idx"])
    )

    # Join back to original table to add the description information to each row
    df = (
        pd.merge(df, descr_data, on="group_idx", how="inner")
        .query("href != '#'")
        .drop(columns=["podrocje_description"])
    )

    # Convert HREFs to full URLs, add a flag if the URL links to final source, or a new webpage
    df["is_final_source"] = df["href"].apply(lambda x: x.startswith("http"))
    df["url"] = df["href"].apply(lambda x: ROOT_URL + x if not x.startswith("http") else x)
    df["href_is_file"] = df["url"].apply(
        lambda x: x.endswith(".pdf")
        or x.endswith(".docx")
        or x.endswith(".doc")
        or x.endswith(".xlsx")
        or x.endswith(".xls")
        or x.endswith(".zip")
    )
    df["href_type"] = df[["is_final_source", "href_is_file"]].apply(
        lambda x: "file" if x[0] and x[1] else "website_source" if x[0] else "website_details", axis=1
    )

    df.to_csv(os.path.join(metadata_dir, "data_links.csv"), index=False)
    return df


def extract_source_files_paths(data, metadata_dir):
    """
    Now we iterate over all the links in the extracted data. Some of the links point already to a final srouce file,
    while some point to a different website that contains more links on the same financial topic.
    We want to scrape also these extra links.
    """

    website_data = []
    href_data = []
    new_websites = data.query("is_final_source == False and href_is_file == False")["url"].values.tolist()
    for idx, raw_url in enumerate(new_websites):
        if idx % 10 == 0:
            print("Started scraping {}/{}: {}".format(idx, len(new_websites), raw_url))

        url = (
            "/".join(raw_url.split("/")[:-1])
            if raw_url.split("/")[-1].startswith("#")
            else "/".join(raw_url.split("/"))
        )
        driver = webdriver.Chrome()
        driver.get(url)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        driver.close()

        # Get the text in the <h1> element  --> this gives the title of the page
        h1_text = None
        h1_element = soup.find("h1")
        if h1_element:
            h1_text = h1_element.text.strip()

        opis_text = None
        for h2 in soup.find_all("h2"):
            if h2.find("a") is None:
                continue
            a_text = h2.find("a").text.strip()

            # Exclude the text from the <i> elements to get only "Zakonodaja"
            for i in h2.find_all("i"):
                a_text = a_text.replace(i.text, "").strip()
            if "Opis" in a_text:
                opis_parent_element = h2.parent
                if opis_parent_element:
                    opis_p_elements = opis_parent_element.find_all("p")
                    opis_text = " ".join([x.text.strip() for x in opis_p_elements])
            elif "Zakonodaja" in a_text:
                zakonodaja_sister_elements = h2.find_next_siblings()
                for element in zakonodaja_sister_elements:
                    a_elements = element.find_all("a", href=True)
                    for a in a_elements:
                        # This is an anchor element, so extract the text and the href and save them as separate values
                        zakonodaja_text = a.text.strip()
                        zakonodaja_href = a.get("href")
                        href_data.append([raw_url, zakonodaja_text, zakonodaja_href])
            elif "Podrobnejši opisi" in a_text:
                podrobnejsi_opisi_sister_elements = h2.find_next_siblings()
                for element in podrobnejsi_opisi_sister_elements:
                    a_elements = element.find_all("a", href=True)
                    for a in a_elements:
                        # This is an anchor element, so extract the text and the href and save them as separate values
                        podrobnejsi_opisi_text = a.text.strip()
                        podrobnejsi_opisi_href = a.get("href")
                        href_data.append([raw_url, podrobnejsi_opisi_text, podrobnejsi_opisi_href])
        website_data.append([raw_url, h1_text, opis_text])

    # Create the two files, and combined them all together with the original data
    website_data = pd.DataFrame(website_data, columns=["url", "title", "opis"])
    href_data = pd.DataFrame(href_data, columns=["url", "source_desc", "source_href"])

    # Now I want to integrate the additiona information to the original dataset.
    # For the rows that were not directly potining to a source, but rather to a new website, we can now add the
    # links to the actual source files

    # First get the rows of the dataset that directly link to a specific source file
    # (these we'll just concatenate in the end)
    sources_data = (
        data.query("href_type != 'website_details'")
        .rename(
            columns={
                "group": "group_name",
                "group_description": "group_desc",
                "podrocje_name": "podrocje_name",
                "url": "file_url",
            }
        )[["group_name", "group_desc", "podrocje_name", "file_url"]]
        .drop_duplicates()
    )
    sources_data["podrocje_url"] = [None] * len(sources_data)
    sources_data["file_desc"] = [None] * len(sources_data)
    sources_data["podrocje_opis"] = [None] * len(sources_data)
    sources_data = sources_data[
        ["group_name", "group_desc", "podrocje_name", "podrocje_url", "file_desc", "file_url", "podrocje_opis"]
    ]

    # Second: get the rows form the dataset that point to a website with further links and details
    links_data = (
        data.query("href_type == 'website_details'")
        .rename(
            columns={
                "group": "group_name",
                "group_description": "group_desc",
                "podrocje_name": "podrocje_name",
                "url": "podrocje_url",
            }
        )[["group_name", "group_desc", "podrocje_name", "podrocje_url"]]
        .drop_duplicates()
    )

    # Enrich the links data with the
    href_data = href_data.rename(
        columns={"url": "podrocje_url", "source_desc": "file_desc", "source_href": "file_url"}
    )[["podrocje_url", "file_desc", "file_url"]].drop_duplicates()
    website_data = website_data.rename(
        columns={"url": "podrocje_url", "title": "podrocje_title", "opis": "podrocje_opis"}
    )[["podrocje_url", "podrocje_title", "podrocje_opis"]].drop_duplicates()
    links_data = pd.merge(links_data, website_data, on="podrocje_url", how="left")
    links_data = pd.merge(links_data, href_data, on="podrocje_url", how="left")
    links_data = links_data[
        ["group_name", "group_desc", "podrocje_name", "podrocje_url", "file_desc", "file_url", "podrocje_opis"]
    ]

    def get_file_type(href):
        for file_extension in FILE_EXTENSIONS:
            if str(href).endswith(file_extension):
                return file_extension
        if str(href).startswith("/"):
            # relative path to a website
            return "website"
        elif str(href).startswith("http"):
            return "website"
        else:
            return None

    # https://www.fu.gov.si/carina/poslovanje_z_nami/carinski_predpisi/#c1496
    data = pd.concat([links_data, sources_data], axis=0)
    data["file_type"] = data["file_url"].apply(lambda x: get_file_type(x))
    data = data.drop_duplicates()
    updated_urls = []
    for url in data["file_url"]:
        if str(url).startswith("/"):
            updated_urls.append(os.path.join("https://www.fu.gov.si/", url))
        else:
            updated_urls.append(url)
    data["file_url"] = updated_urls
    data.to_csv(os.path.join(metadata_dir, "furs_data.csv"), index=False)
    return data


def get_raw_sources_list(metadata_dir):
    data = extract_davcna_podrocja_info(metadata_dir)
    raw_sources_list = extract_source_files_paths(data, metadata_dir)
    return raw_sources_list
