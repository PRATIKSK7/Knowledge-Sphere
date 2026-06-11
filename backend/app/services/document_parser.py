import os
import re
import csv
from datetime import datetime
from typing import Dict, Any, List, Tuple
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import pdfplumber
from docx import Document as DocxDocument
from app.core.config import settings

class DocumentParser:
    @staticmethod
    def parse_txt(filepath: str) -> str:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    @staticmethod
    def parse_csv(filepath: str) -> str:
        text_lines = []
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            for row in reader:
                text_lines.append(", ".join(row))
        return "\n".join(text_lines)

    @staticmethod
    def parse_html(filepath: str) -> str:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            # Remove scripts and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text(separator="\n")

    @staticmethod
    def parse_docx(filepath: str) -> str:
        doc = DocxDocument(filepath)
        text_lines = [p.text for p in doc.paragraphs if p.text]
        return "\n".join(text_lines)

    @staticmethod
    def parse_pdf(filepath: str) -> str:
        # We combine PyMuPDF (fast) and pdfplumber (precise tables/layouts fallback)
        text = ""
        try:
            doc = fitz.open(filepath)
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception:
            # Fallback to pdfplumber
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        return text

    @classmethod
    def extract_text(cls, filepath: str, mime_type: str) -> str:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found at {filepath}")
        
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".pdf" or "pdf" in mime_type:
            return cls.parse_pdf(filepath)
        elif ext in [".docx", ".doc"] or "word" in mime_type:
            return cls.parse_docx(filepath)
        elif ext == ".csv" or "csv" in mime_type:
            return cls.parse_csv(filepath)
        elif ext in [".html", ".htm"] or "html" in mime_type:
            return cls.parse_html(filepath)
        else: # Fallback to plaintext for .txt or unknown formats
            return cls.parse_txt(filepath)

    @classmethod
    def clean_text(cls, text: str) -> str:
        # Clean extra whitespaces, control characters, keep formatting readable
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    @classmethod
    def extract_metadata(cls, text: str, filename: str) -> Dict[str, Any]:
        """
        Extract Title, Authors, Abstract, Keywords, References, Publication Date.
        Heuristics are used as fallbacks if LLM/NLP-based extraction is not available yet.
        """
        metadata = {
            "title": os.path.splitext(filename)[0].replace("_", " ").title(),
            "authors": [],
            "abstract": "",
            "keywords": [],
            "publication_date": None,
            "references": []
        }

        # Try to find an abstract
        abstract_match = re.search(
            r'(?:abstract|summary|introduction)\b[:\s]*(.*?)(?=\n\s*(?:introduction|background|methods|1\s+\w+)|\n\n\d+|\n\n[A-Z][A-Z\s]{4,})', 
            text, 
            re.IGNORECASE | re.DOTALL
        )
        if abstract_match:
            metadata["abstract"] = cls.clean_text(abstract_match.group(1))[:1000]

        # Try to extract keywords
        keywords_match = re.search(
            r'(?:keywords|key\s*words|index\s*terms)\b[:\s]*(.*?)(?=\n)', 
            text, 
            re.IGNORECASE
        )
        if keywords_match:
            kw_list = re.split(r'[,;.]', keywords_match.group(1))
            metadata["keywords"] = [kw.strip().lower() for kw in kw_list if kw.strip()]

        # Try to find References/Bibliography section at the end of the text
        refs_match = re.search(
            r'(?:references|bibliography|works\s+cited)\b[:\s]*(.*)', 
            text, 
            re.IGNORECASE | re.DOTALL
        )
        if refs_match:
            ref_lines = refs_match.group(1).split("\n")
            refs = []
            current_ref = ""
            for line in ref_lines:
                line = line.strip()
                if not line:
                    continue
                # If it starts with [1] or 1. or (1) it indicates a new citation
                if re.match(r'^(\[\d+\]|\d+\.|\(\d+\))', line):
                    if current_ref:
                        refs.append(current_ref)
                    current_ref = line
                else:
                    if current_ref:
                        current_ref += " " + line
                    else:
                        current_ref = line
            if current_ref:
                refs.append(current_ref)
            metadata["references"] = [r.strip() for r in refs if len(r) > 10][:50] # cap to top 50

        # Try to extract Authors (from first 2000 chars of text, simple heuristic)
        first_lines = text[:2000].split("\n")
        author_list = []
        for line in first_lines[:15]:
            line = line.strip()
            # If line contains email addresses or institution words, ignore
            if "@" in line or any(word in line.lower() for word in ["university", "dept", "department", "institute", "laboratory"]):
                continue
            # Look for lines with 2-4 capitalized words that could represent names
            if re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+){1,3}(,\s*[A-Z][a-z]+(\s+[A-Z][a-z]+){1,3})*$', line):
                names = re.split(r'[,&]|\band\b', line)
                for name in names:
                    clean_name = name.strip()
                    if clean_name and len(clean_name) > 3:
                        author_list.append(clean_name)
        if author_list:
            metadata["authors"] = list(set(author_list))

        return metadata

    @classmethod
    def chunk_text(cls, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
        """
        Split document text into chunks of specified length with overlap.
        Preserves paragraph boundaries or line boundaries if possible.
        """
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            if end >= text_len:
                chunks.append(text[start:])
                break
            
            # Find the best split boundary (double newline or single newline) in the overlap region
            overlap_area = text[end - chunk_overlap : end]
            best_split = -1
            
            # Try to find a paragraph break
            p_break = overlap_area.rfind("\n\n")
            if p_break != -1:
                best_split = p_break + 2
            else:
                # Try to find a sentence break
                sentence_break = max(
                    overlap_area.rfind(". "),
                    overlap_area.rfind("? "),
                    overlap_area.rfind("! ")
                )
                if sentence_break != -1:
                    best_split = sentence_break + 2
                else:
                    # Try to split on newline or space
                    space_break = overlap_area.rfind(" ")
                    if space_break != -1:
                        best_split = space_break + 1
            
            if best_split != -1:
                end = (end - chunk_overlap) + best_split
            
            chunks.append(text[start:end])
            start = end - chunk_overlap
            if start < 0:
                start = 0
                
        return [c.strip() for c in chunks if c.strip()]
