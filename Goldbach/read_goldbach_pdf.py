import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
import sys

def extract_pdf_content(pdf_path):
    """Extract text content from PDF using multiple methods"""
    
    print("GOLDBACH PDF ANALYSIS")
    print("=" * 50)
    
    # Method 1: PyPDF2
    print("\n--- METHOD 1: PyPDF2 ---")
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            print(f"Total pages: {len(reader.pages)}")
            
            # Extract first few pages
            for i in range(min(3, len(reader.pages))):
                page = reader.pages[i]
                text = page.extract_text()
                if text.strip():
                    print(f"\nPage {i+1} (PyPDF2):")
                    print(text[:1000] + "..." if len(text) > 1000 else text)
                    print("-" * 40)
    except Exception as e:
        print(f"PyPDF2 failed: {e}")
    
    # Method 2: pdfplumber
    print("\n--- METHOD 2: pdfplumber ---")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Total pages: {len(pdf.pages)}")
            
            for i in range(min(3, len(pdf.pages))):
                page = pdf.pages[i]
                text = page.extract_text()
                if text and text.strip():
                    print(f"\nPage {i+1} (pdfplumber):")
                    print(text[:1000] + "..." if len(text) > 1000 else text)
                    print("-" * 40)
    except Exception as e:
        print(f"pdfplumber failed: {e}")
    
    # Method 3: PyMuPDF (fitz)
    print("\n--- METHOD 3: PyMuPDF ---")
    try:
        doc = fitz.open(pdf_path)
        print(f"Total pages: {len(doc)}")
        
        for i in range(min(5, len(doc))):
            page = doc[i]
            text = page.get_text()
            if text.strip():
                print(f"\nPage {i+1} (PyMuPDF):")
                print(text[:1500] + "..." if len(text) > 1500 else text)
                print("-" * 40)
        
        doc.close()
    except Exception as e:
        print(f"PyMuPDF failed: {e}")

def search_goldbach_terms(pdf_path):
    """Search for specific Goldbach algorithm terms"""
    
    search_terms = [
        "algorithm 1", "algorithm 2", "algo 1", "algo 2",
        "OB", "RB", "FV", "LV", "MB", "BR", 
        "premium", "discount", "dealing range",
        "phase", "goldbach"
    ]
    
    print("\n" + "="*50)
    print("SEARCHING FOR KEY TERMS")
    print("="*50)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    text_lower = text.lower()
                    for term in search_terms:
                        if term.lower() in text_lower:
                            # Extract context around the term
                            lines = text.split('\n')
                            for line_num, line in enumerate(lines):
                                if term.lower() in line.lower():
                                    print(f"\nFound '{term}' on page {page_num+1}:")
                                    # Show context (line before, matching line, line after)
                                    start = max(0, line_num-1)
                                    end = min(len(lines), line_num+2)
                                    for i in range(start, end):
                                        marker = ">>> " if i == line_num else "    "
                                        print(f"{marker}{lines[i]}")
                                    print("-" * 30)
    except Exception as e:
        print(f"Search failed: {e}")

if __name__ == "__main__":
    pdf_path = "goldbach.pdf"
    
    # Extract content
    extract_pdf_content(pdf_path)
    
    # Search for key terms
    search_goldbach_terms(pdf_path)
