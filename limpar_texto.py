import re
from typing import List
from image_utils import ImageProcessing

def processar_paragrafos(list_of_extracted_text_strings: List[str]):
    print(f"Starting document processing. Total pages: {len(list_of_extracted_text_strings):,}")
    full_text = "\n\n".join(list_of_extracted_text_strings)
    print(f"Size of full text before processing: {len(full_text):,} characters")
    chunk_size, overlap = 300, 3
    # Improved chunking logic
    paragraphs = re.split(r'(\.\n)|(\,\n)', full_text)
    print(f"quantidade de paragrafos {len(paragraphs)}")
    chunks = []
    current_chunk = []
    current_chunk_length = 0
    for paragraph in paragraphs:
        paragraph_length = len(paragraph)
        if current_chunk_length + paragraph_length <= chunk_size:
            current_chunk.append(paragraph)
            current_chunk_length += paragraph_length
        else:
            # If adding the whole paragraph exceeds the chunk size,
            # we need to split the paragraph into sentences
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            current_chunk = []
            current_chunk_length = 0
            for sentence in sentences:
                sentence_length = len(sentence)
                if current_chunk_length + sentence_length <= chunk_size:
                    current_chunk.append(sentence)
                    current_chunk_length += sentence_length
                else:
                    if current_chunk:
                        chunks.append(" ".join(current_chunk))
                    current_chunk = [sentence]
                    current_chunk_length = sentence_length
    # Add any remaining content as the last chunk
    if current_chunk:
        chunks.append("\n\n".join(current_chunk) if len(current_chunk) > 1 else current_chunk[0])
    # Add overlap between chunks
    for i in range(1, len(chunks)):
        overlap_text = chunks[i-1].split()[-overlap:]
        chunks[i] = " ".join(overlap_text) + " " + chunks[i]
    print(f"Document split into {len(chunks):,} chunks. Chunk size: {chunk_size:,}, Overlap: {overlap:,}")
    return chunks

if __name__ == "__main__":
    img_processing = ImageProcessing()
    texto = img_processing.get_text_from_image('./files/to_img/cci1.0882024_0.png')
    chunks = processar_paragrafos(list_of_extracted_text_strings=[texto])
    print(' '.join(chunks))