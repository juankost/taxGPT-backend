# taxGPT-backend

The taxGPT-backend is part of the taxGPT project that was designed to provide information related to the Slovenian tax law to users (e.g. accountants, tax advisors) in real-time. This repository handles the Retrieval Augmented Generation (RAG) using OpenAI API and retrieving the relevant context from the FAISS vector store.

**Features**:

- OpenAI API using GPT-4o
- FAISS vector store
- Cohere Reranking of retrieved context

## Installation

Follow these steps to set up the taxGPT-backend project on your local machine.

### Prerequisites

Ensure you have the following installed on your system:

- Anaconda or Miniconda (for managing Python environments)
- Docker

### Step 1: Clone the Repository

```
git clone https://github.com/juankost/taxGPT-backend.git
cd taxGPT-backend
```

### Step 2: Create and Activate Conda Environment

```
conda create -n taxgpt-env python=3.11
conda activate taxgpt-env
```

### Step 3: Install Python Package (Editable Mode)

This command will install the project in editable mode, along with all its dependencies specified in `setup.py` and `requirements.txt`:

```
pip install -e .
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root directory and add the following variables:

```
# API keys for model providers
OPENAI_API_KEY=
COHERE_API_KEY=

# Model configs
GPT_MODEL="gpt-4o"
EMBEDDING_MODEL="text-embedding-3-small"
NUM_RETRIEVED_CHUNKS=25
NUM_RERANKED_CHUNKS=10
MAX_CONTEXT_LENGTH=4096

# Google Storage configs
PROJECT_ID=
STORAGE_BUCKET_NAME= <Google Storage Bucket where the vector store was saved>
VECTOR_DB_PATH=<Path to Vector Store in the Storage bucket>


```

Replace the placeholders with your actual credentials and project details.

### Step 7: Verify Installation

To ensure everything is set up correctly, run:

```
python -m app.app --local
```

This will run the server locally and you can use http://0.0.0.0:8080/docs to access the API documentation and test it.

## Deployment

We provide the cloudbuild.yaml file to allow for automated deployment to Google Cloud Run instance.
Note, you must first save the .env file as a Secret in Google Cloud Secret Manager. We use the
name 'taxgpt-backend-env' in the cloudbuild.yaml file for this Secret. You can additionally specify
build triggers in the Google Cloud Console to automatically deploy the latest version of the code
whenever a push is made to the repository.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
