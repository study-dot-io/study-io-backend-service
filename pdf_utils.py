#We will process pdf on our own and not feed it to the LLM as garbage input = garbage output
# Assumption of only text based PDFs

import fitz 

def extract_text_and_chunks(pdf_file, chunk_size=1000):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    words = full_text.split()
    chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks

#testing
with open("test_files/cs446-d1-study.io.pdf", "rb") as f:
    chunks = extract_text_and_chunks(f)
    print(chunks)  