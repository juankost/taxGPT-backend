import os
from langchain.document_loaders import PyMuPDFLoader

FILE_EXTENSIONS = ["docx", "doc", "pdf", "zip", "xlsx"]
ROOT_URL = "https://www.fu.gov.si"
MAIN_URL = ROOT_URL + "/podrocja"
SRC_DIR = "/Users/juankostelec/Google_drive/Projects/tax_backend/src"
METADATA_DIR = "/Users/juankostelec/Google_drive/Projects/tax_backend/data"
RAW_DATA_DIR = "/Users/juankostelec/Google_drive/Projects/tax_backend/data/raw_files"
PROCESSED_DATA_DIR = "/Users/juankostelec/Google_drive/Projects/tax_backend/data/processed_files"


def parse_pdf(path, processed_data_dir, file_name=None):
    if file_name is None:
        file_name = path.rsplit("/", maxsplit=1)[-1].rsplit(".", maxsplit=1)[0]
    data = PyMuPDFLoader(path).load()
    text = "".join([d.page_content for d in data])
    with open(os.path.join(processed_data_dir, file_name + ".txt"), "w") as f:
        f.write(text)
