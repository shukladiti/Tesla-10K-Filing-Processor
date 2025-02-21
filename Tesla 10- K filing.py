"""
Libraries sto import :

!pip install -U sec-edgar-downloader
!pip install sec_api
!pip install -U langchain-community
!pip install langchain_chroma
!pip install langchain_google_genai


"""

import os
from langchain.vectorstores import Chroma
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.docstore.document import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA, create_retrieval_chain
from google.oauth2 import service_account
from sec_edgar_downloader import Downloader
from langchain.text_splitter import Language, RecursiveCharacterTextSplitter, CharacterTextSplitter
import re
from sec_api import XbrlApi,ExtractorApi
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import gdown


class SECDataProcessor:

    def __init__(self, email, company):
        self.downloader = Downloader(email_address=email, company_name=company)
        self.base_url = "https://www.sec.gov/Archives/edgar/data/1318605/"
        self.root_directory = f"/content/sec-edgar-filings/{company}/10-K/"
        self.xbrl_api = XbrlApi("insert your key here")
        self.extractor_api = ExtractorApi(api_key="insert your key here")

    def initialize_apis(api_key):
        """
        Initializes XBRL and Extractor APIs with the provided API key.

        Args:
            api_key (str): The API key for authentication.

        Returns:
            tuple: A tuple containing initialized XbrlApi and ExtractorApi instances.
        """
        xbrl_api = XbrlApi(api_key)
        extractor_api = ExtractorApi(api_key=api_key)
        return xbrl_api, extractor_api

    def authenticate_with_google(self, service_account_path):
        try:
            credentials = service_account.Credentials.from_service_account_file(service_account_path)
            scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/cloud-platform'])
            scoped_credentials.refresh(Request())
            print("Google Cloud Authentication successful!")
            return scoped_credentials
        except Exception as e:
            print(f"Google Cloud Authentication failed: {e}")
            return None

    def download_google_credentials(self, file_id, output_path):
        url = f'https://drive.google.com/uc?id={file_id}'
        gdown.download(url, output_path, quiet=False)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = output_path
        print("Google Cloud credentials downloaded and set.")

    def generate_document_urls(root_dir):
        """Generates document URLs from downloaded filings.

            Returns:
            list: A list of URLs for the extracted documents.
        """
        urls = []
        import os

        root_directory = "/content/sec-edgar-filings/TSLA/10-K"

        for subdir, dirs, files in os.walk(root_directory):
            # Skip processing for the root directory itself
            if subdir == root_directory:
                continue
            doc_name = os.path.basename(subdir).replace("-", "")
            if 'full-submission.txt' in files:
                file_path = os.path.join(subdir, 'full-submission.txt')
                with open(file_path, "r", encoding='utf-8') as file:
                    content = file.read()
                    match = re.search(r"<FILENAME>([^<]+\.htm)", content, re.IGNORECASE)
                    if match:
                        extracted_filename = match.group(1).strip()  # Extract and strip any whitespace
                        url = base_url + doc_name + '/' + extracted_filename
                        urls.append(str(url))
                    else:
                        print("No <FILENAME> tag found.")

                # else:
        return urls

    def process_filings(self, sections_to_extract):
        """Processes filings, extracting relevant sections and XBRL data.

        Args:
            sections_to_extract (list): List of section identifiers to extract.
        """
        urls = self.generate_document_urls()
        for i, filing_url in enumerate(urls, 1):
            try:
                print(f"Processing filing: {filing_url}")
                xbrl_json = self.xbrl_api.xbrl_to_json(htm_url=filing_url)
                extracted_sections = {}
                for section in sections_to_extract:
                    try:
                        section_text = self.extractor_api.get_section(filing_url, section, "text")
                        extracted_sections[section] = section_text
                    except Exception as e:
                        print(f"Error extracting section {section}: {e}")

                filename = f"{self.root_directory}/Tesla_filings_{i}.txt"
                with open(filename, 'w') as f:
                    if "CoverPage" in xbrl_json:
                        for key, value in xbrl_json["CoverPage"].items():
                            f.write(f"{key}: {value}\n")
                    for section, text in extracted_sections.items():
                        f.write(f"\nSection {section}:\n{text}\n")
            except Exception as e:
                print(f"Error processing filing {filing_url}: {e}")

    def split_text_into_chunks(self):
        """Splits extracted text into chunks for further analysis.

        Returns:
            list: A list of Document objects representing text chunks.
        """
        all_text_chunks = []
        text_splitter = CharacterTextSplitter(separator="\n\n", chunk_size=1000, chunk_overlap=200)
        for filename in os.listdir(self.root_directory):
            if filename.startswith("Tesla_filings_"):
                with open(os.path.join(self.root_directory, filename), "r") as file:
                    text = file.read()
                    split_texts = text_splitter.split_text(text)
                    documents = [Document(page_content=chunk) for chunk in split_texts]
                    all_text_chunks.extend(documents)
        print(f"Total chunks of text: {len(all_text_chunks)}")
        return all_text_chunks

    def create_vectorstore(self, all_text_chunks):
        """Creates a vector store from text chunks.

        Args:
            all_text_chunks (list): List of Document objects containing text chunks.

        Returns:
            Chroma: A vector store created from the document chunks.
        """
        embedding_function = SentenceTransformerEmbeddings(model_name='all-MiniLM-L6-v2')
        vectorstore = Chroma.from_documents(documents=all_text_chunks, embedding=embedding_function)
        print("Vectorstore created successfully.")
        return vectorstore

    def query_rag_system(vectorstore, questions):
        """Queries a retrieval-augmented generation (RAG) system with given questions.

        Args:
            vectorstore (Chroma): The vector store to retrieve context from.
            questions (list): List of questions to query the RAG system.
        """
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0, max_tokens=None, timeout=None)
        retriever = vectorstore.as_retriever()
        qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

        for question in questions:
            try:
                response = qa_chain.run(question)
                print(f"Question: {question}\nResponse: {response}\n")
            except Exception as e:
                print(f"Error processing question '{question}': {e}")

if __name__ == "__main__":
    processor = SECDataProcessor(email="insert your email here", company="TSLA", api_key="insert your key here")
    file_id = 'insert your key here'
    credentials_path = '/content/GOOGLE_APPLICATION_CREDENTIALS.json'
    processor.download_google_credentials(file_id, credentials_path)
    processor.authenticate_with_google(credentials_path)

    processor.process_filings(["1A", "7", "8"])
    text_chunks = processor.split_text_into_chunks()
    vectorstore = processor.create_vectorstore(text_chunks)

    questions = [
        "What operational challenges did Tesla highlight for the past fiscal year?",
        "How does Tesla describe its competitive strategy in the automotive market?"
    ]

    processor.query_rag_system(vectorstore, questions)
