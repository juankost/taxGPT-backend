# Steps:
# 1. Extract the raw sources list
# 2. Scrape the PiSRIR data
# 3. Add the data to vector database
from scraper.raw_sources_list import get_raw_sources_list
from scraper.scrape_pisrs_sources import scrape_pisrs_data
from database.vector_store import add_text_to_vector_store


def main():
    # 1. Extract the raw sources list
    raw_sources_list = get_raw_sources_list()

    # 2. Scrape the PiSRIR data
    scrape_pisrs_data(raw_sources_list)
