# Tesla 10-K Filing Processing Script

## Overview

This script automates the retrieval, processing, and analysis of Tesla's SEC 10-K filings. It downloads SEC filings, extracts relevant financial data, processes the text into structured formats, and creates a vector store for efficient querying using retrieval-augmented generation (RAG).

## Features

- Downloads SEC 10-K filings using `sec-edgar-downloader`.
- Extracts relevant sections using `sec_api`.
- Splits extracted text into manageable chunks.
- Creates a vector store using `Chroma` for efficient search and retrieval.
- Integrates with `Google Generative AI` for querying extracted data.

## Installation

Ensure you have Python installed and install dependencies using:

```sh
pip install -r requirements.txt
```





### Dependencies

The required packages include:

```
sec-edgar-downloader
sec_api
langchain-community
langchain_chroma
langchain_google_genai
sentence-transformers
gdown
```

## Usage

### 1. Initialize and Download Filings

```python
from sec_data_processor import SECDataProcessor

processor = SECDataProcessor(email="your-email@example.com", company="TSLA", api_key="your-api-key")
```

### 2. Authenticate with Google Cloud

```python
file_id = 'your-google-drive-file-id'
credentials_path = '/path/to/credentials.json'
processor.download_google_credentials(file_id, credentials_path)
credentials = processor.authenticate_with_google(credentials_path)
```

### 3. Process SEC Filings

```python
if credentials:
    processor.process_filings(["1A", "7", "8"])
    text_chunks = processor.split_text_into_chunks()
    vectorstore = processor.create_vectorstore(text_chunks)
else:
    print("Skipping processing due to authentication failure.")
```

### 4. Query the Extracted Data

```python
questions = [
    "What operational challenges did Tesla highlight for the past fiscal year?",
    "How does Tesla describe its competitive strategy in the automotive market?"
]
processor.query_rag_system(vectorstore, questions)
```

## Configuration

- Google Cloud Credentials: Update the script to dynamically fetch credentials from an environment variable:
  ```python
  credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "path/to/default/credentials.json")
  ```
- Vector Store Validation: Before creating the vector store, ensure `text_chunks` is not empty:
  ```python
  if text_chunks:
      vectorstore = processor.create_vectorstore(text_chunks)
  else:
      print("No text chunks available for vector store creation.")
  ```

## Output

- Extracted text files are saved in `/content/sec-edgar-filings/TSLA/10-K/`
- Processed filings are stored as `.txt` files.
- A vector store is created for querying extracted text efficiently.

## License

This project is open-source and available under the MIT License.

## Contact

For any issues or contributions, please reach out at `your-email@example.com`.

