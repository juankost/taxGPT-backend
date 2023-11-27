import pandas as pd
import os
import wget
from selenium import webdriver
from bs4 import BeautifulSoup
from parser import parse_pdf

FILE_EXTENSIONS = ["docx", "doc", "pdf", "zip", "xlsx"]
ROOT_URL = "https://www.fu.gov.si"
MAIN_URL = ROOT_URL + "/podrocja"
SRC_DIR = "/Users/juankostelec/Google_drive/Projects/tax_backend/src"
METADATA_DIR = "/Users/juankostelec/Google_drive/Projects/tax_backend/data"
RAW_DATA_DIR = "/Users/juankostelec/Google_drive/Projects/tax_backend/data/raw_files"
PROCESSED_DATA_DIR = "/Users/juankostelec/Google_drive/Projects/tax_backend/data/processed_files"


def scrape_pisrs_data(data: pd.DataFrame, db=None, embeddings=None):
    total_rows = len(data)
    for idx, row in data[["file_url"]].iterrows():
        if idx % 10 == 0:
            print(f"Processing file {idx}/{total_rows}")

        file_url = row["file_url"]
        try:
            driver = webdriver.Chrome()
            driver.get(file_url)

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            # Extract the law title if available, this is the text in the <h1> element
            h1_text = None
            h1_element = soup.find("h1")
            if h1_element:
                h1_text = h1_element.text.strip()[:-1].strip()

            # Extract the URL from the website containing the link to the actual pdf/doc file
            div_element = soup.find("div", id="fileBtns")
            if div_element:
                a_elements = div_element.find_all("a", href=True)
                for a in a_elements:
                    href_value = a.get("href")
                    complete_url_path = os.path.join(file_url.rsplit("/", maxsplit=1)[0], href_value)
                    if href_value.endswith("pdf"):
                        # Use the actual name of the law for the file name, with the correct extension
                        if h1_text:
                            source_name = h1_text + ".pdf"
                        else:
                            source_name = href_value.split("/")[-1]

                        # Download file if it does not already exist
                        if not os.path.exists(os.path.join(RAW_DATA_DIR, source_name)):
                            print(f"Downloading pdf/doc file of law: {source_name} from website {complete_url_path}")
                            wget.download(complete_url_path, os.path.join(RAW_DATA_DIR, source_name))
                            print("\n")
                            # Process file and extract the articles from the law

                        # If the data was not yet extracted, do it now:
                        parsed_path = os.path.join(PROCESSED_DATA_DIR, f"{source_name.rsplit('.')[0]}.txt")
                        if not os.path.exists(parsed_path):
                            # Parse the pdf file
                            parse_pdf(parsed_path, PROCESSED_DATA_DIR)

                            # Add to Vector database
                            add_text_to_vector_store(path, law, embeddings=None, db=None)

        except Exception as e:
            driver.close()
            print("Tried to get the website html, but did not work. Exception: ", e)
            raise ValueError
    driver.close()
