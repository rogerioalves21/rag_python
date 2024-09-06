import pymupdf4llm
import pymupdf
import pathlib

md_text = pymupdf4llm.to_markdown("CCI1029.pdf")

doc = pymupdf.open("cci.txt", filetype="txt")

# now work with the markdown text, e.g. store as a UTF8-encoded file
pathlib.Path("output1029.md").write_bytes(md_text.encode())

md_txt = pymupdf4llm.to_markdown(doc)

# write markdown string to some file
pathlib.Path("cci.md").write_bytes(md_txt.encode())

print("FOI")

# https://github.com/search?q=repo%3Adiscourse%2Fdiscourse-ai+markdown&type=code