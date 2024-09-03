import fitz

doc = fitz.open('./files/old_pdfs/CCI1.088_2024.pdf')
for page in doc:
    tables = page.get_textbox()
    for table in tables:
        print(table)