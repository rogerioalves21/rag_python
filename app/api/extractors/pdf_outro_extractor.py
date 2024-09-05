# Import PDFDataExtractor
from pdfdataextractor import Reader

# Spefify the path to the PDF file
path = r'the path to the PDF file'

# Create an instance
file = Reader()

# Read the file
pdf = file.read_file(path)

# Get Caption
pdf.caption()

# Get Keywords
pdf.keywords()

# Get Title
pdf.title()

# Get DOI
pdf.doi()

# Get Abstract
pdf.abstract()

# Get Journal
pdf.journal()

# Get Journal Name
pdf.journal('name')

# Get Journal Year
pdf.journal('year')

# Get Journal Volume
pdf.journal('volume')

# Get Journal Page
pdf.journal('page')

# Get Section titles and corresponding text
pdf.section()

# Get References
pdf.reference()