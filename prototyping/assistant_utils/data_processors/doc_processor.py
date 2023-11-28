import markdown
import tiktoken
from bs4 import BeautifulSoup
import nltk

CHUNK_SIZE = 200
MIN_CHUNK_SIZE_CHARS = 350  # The minimum size of each text chunk in characters
MIN_CHUNK_LENGTH_TO_EMBED = 5  # Discard chunks shorter than this
MAX_NUM_CHUNKS = 300  # The maximum number of chunks to generate from a text
ENDPAGE_NUM = 282  # the last page number


class DocProcessor:
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

    @staticmethod
    def clear_text(file: str) -> str:
        """Saves the contents of the given markdown file to a string.

        Args:
            link (str): Path to the markdown file.

        Returns:
            str: Cleaned markdown content.
        """
        with open(file, "r", encoding="utf-8") as input_file:
            text = input_file.read()

        html = markdown.markdown(text)
        soup = BeautifulSoup(html, "html.parser")

        text = soup.get_text().strip()
        if text.startswith("Page settings") and "\n\n" in text:
            text = text[str(text).find("\n\n") + 2:]
        return text

    @staticmethod
    def get_text_chunks(text: str, chunk_token_size: int = CHUNK_SIZE) -> list[str]:
        """Splits a text into chunks of ~CHUNK_SIZE tokens, based on punctuation and newline boundaries.

        Args:
            text (str): Text content to split into chunks.
            chunk_token_size (int, optional): The target size of each chunk in tokens. Defaults to CHUNK_SIZE.

        Returns:
            list: List of text chunks.
        """
        tokens = DocProcessor.encoding.encode(text)

        chunks = []
        chunk_size = chunk_token_size
        num_chunks = 0

        while tokens:
            chunk = tokens[:chunk_size]

            chunk_text = DocProcessor.encoding.decode(chunk)

            if not chunk_text or chunk_text.isspace():
                tokens = tokens[len(chunk):]
                continue

            last_punctuation = max(chunk_text.rfind(
                "."), chunk_text.rfind("\n"), chunk_text.rfind("\n\n"))

            if last_punctuation != -1 and last_punctuation > MIN_CHUNK_SIZE_CHARS:
                chunk_text = chunk_text[: last_punctuation + 1]

            chunk_text_to_append = chunk_text.replace("\n", " ").strip()

            if len(chunk_text_to_append) > MIN_CHUNK_LENGTH_TO_EMBED:
                chunks.append(chunk_text_to_append)

            tokens = tokens[len(DocProcessor.encoding.encode(chunk_text)):]
            num_chunks += 1

        if tokens:
            remaining_text = DocProcessor.encoding.decode(tokens).replace("\n", " ").strip()
            if len(remaining_text) > MIN_CHUNK_LENGTH_TO_EMBED:
                chunks.append(remaining_text)

        return chunks

    @staticmethod
    def split_text_with_overlap(text, num_sentences=3, overlap=1):
        """
        Splits the input text into multiple chunks, where each chunk contains
        a specified number of sentences with an overlap of a specified number
        of sentences.


        Args:
        - text (str): The input text to be split.
        - num_sentences (int): The number of sentences to include in each chunk.
          Default is 3.
        - overlap (int): The number of sentences to overlap between adjacent
          chunks. Default is 1.

        Returns:
        - A list of text chunks, where each chunk contains a specified number
          of sentences with an overlap of a specified number of sentences.
        """

        # Tokenize the text into sentences using NLTK
        sentences = nltk.sent_tokenize(text)

        # Initialize the list of text chunks
        chunks = []

        # Split the sentences into chunks with the specified overlap
        start_idx = 0
        while start_idx < len(sentences):
            end_idx = min(start_idx + num_sentences, len(sentences))
            chunk = ' '.join(sentences[start_idx:end_idx])
            chunks.append(chunk)
            start_idx += num_sentences - overlap

        return chunks


