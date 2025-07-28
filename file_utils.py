# File processing utilities for PDFs and images
# Supports text extraction from PDFs and OCR for images

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("PyMuPDF is required but not installed. Install with: pip install PyMuPDF")

import pytesseract
from PIL import Image
import io
import logging
import shutil
import subprocess

logger = logging.getLogger(__name__)

class DependencyError(Exception):
    """Custom exception for missing dependencies"""
    pass

def check_pymupdf_installation():
    """
    Check if PyMuPDF is properly installed and working
    """
    try:
        # Test if we can create a basic document
        # Use getattr to avoid IDE warnings about fitz.open
        open_func = getattr(fitz, 'open')
        test_doc = open_func()
        test_doc.close()
        logger.info(f"PyMuPDF is available: version {fitz.version[0]}")
        return True
    except Exception as e:
        raise DependencyError(f"PyMuPDF is not working properly: {str(e)}")

def check_tesseract_installation():
    """
    Check if Tesseract OCR is properly installed and accessible
    """
    try:
        # Check if tesseract command is available
        if not shutil.which('tesseract'):
            raise DependencyError("Tesseract OCR is not installed or not in PATH")

        # Try to get version to ensure it's working
        result = subprocess.run(['tesseract', '--version'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            raise DependencyError("Tesseract OCR is installed but not functioning properly")

        logger.info(f"Tesseract OCR is available: {result.stdout.split()[1]}")
        return True

    except subprocess.TimeoutExpired:
        raise DependencyError("Tesseract OCR command timed out")
    except Exception as e:
        raise DependencyError(f"Failed to verify Tesseract installation: {str(e)}")

def detect_file_type(file_bytes):
    """
    Detect file type based on file signature/magic bytes
    """
    if not file_bytes:
        raise ValueError("Empty file provided")

    if file_bytes.startswith(b'%PDF'):
        return 'pdf'
    elif file_bytes.startswith(b'\x89PNG'):
        return 'png'
    elif file_bytes.startswith(b'\xff\xd8\xff'):
        return 'jpeg'
    elif file_bytes.startswith(b'GIF'):
        return 'gif'
    else:
        return 'unknown'

def extract_text_from_pdf(file_bytes, chunk_size=1000):
    """
    Extract text from PDF files using PyMuPDF
    """
    try:
        # Check PyMuPDF installation first
        check_pymupdf_installation()

        if not file_bytes:
            raise ValueError("Empty PDF file provided")

        doc = fitz.open(filetype="pdf", stream=file_bytes)
        full_text = ""

        for page_num, page in enumerate(doc):
            try:
                page_text = page.get_text()
                full_text += page_text
                logger.debug(f"Extracted text from PDF page {page_num + 1}")
            except Exception as e:
                logger.warning(f"Failed to extract text from PDF page {page_num + 1}: {str(e)}")
                continue

        doc.close()

        if not full_text.strip():
            return ["No text found in PDF file"]

        words = full_text.split()
        chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

        logger.info(f"Successfully extracted {len(chunks)} chunks from PDF")
        return chunks

    except fitz.FileDataError:
        raise ValueError("Invalid or corrupted PDF file")
    except DependencyError:
        raise
    except Exception as e:
        raise Exception(f"PDF processing failed: {str(e)}")

def extract_text_from_image(file_bytes, chunk_size=1000):
    """
    Extract text from image files using OCR (Tesseract)
    """
    try:
        # Check Tesseract installation first
        check_tesseract_installation()

        if not file_bytes:
            raise ValueError("Empty image file provided")

        # Open image from bytes
        image = Image.open(io.BytesIO(file_bytes))
        logger.debug(f"Opened image with mode: {image.mode}, size: {image.size}")

        # Convert to RGB if necessary (for PNG with transparency)
        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
            logger.debug("Converted image with transparency to RGB")
        elif image.mode != 'RGB':
            image = image.convert('RGB')
            logger.debug(f"Converted image from {image.mode} to RGB")

        # Extract text using OCR with custom configuration for better accuracy
        custom_config = r'--oem 3 --psm 6'  # OCR Engine Mode 3, Page Segmentation Mode 6
        full_text = pytesseract.image_to_string(image, config=custom_config)

        if not full_text.strip():
            logger.warning("No text detected in image")
            return ["No text found in image"]
        
        words = full_text.split()
        chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

        logger.info(f"Successfully extracted {len(chunks)} chunks from image using OCR")
        return chunks
        
    except DependencyError:
        raise
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"OCR processing failed: {str(e)}")

def extract_text_and_chunks(file_bytes, chunk_size=1000):
    """
    Universal text extraction function that handles both PDFs and images
    """
    try:
        file_type = detect_file_type(file_bytes)
        logger.info(f"Detected file type: {file_type}")

        if file_type.lower() == 'pdf':
            return extract_text_from_pdf(file_bytes, chunk_size)
        elif file_type.lower() in ['png', 'jpeg', 'gif']:
            return extract_text_from_image(file_bytes, chunk_size)
        else:
            supported_types = "PDF, PNG, JPEG, GIF"
            raise ValueError(f"Unsupported file type: {file_type}. Only {supported_types} files are supported.")

    except (ValueError, DependencyError):
        raise
    except Exception as e:
        logger.error(f"Failed to extract text from file: {str(e)}")
        raise Exception(f"File processing failed: {str(e)}")
