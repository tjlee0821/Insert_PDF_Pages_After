import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pypdf import PdfReader, PdfWriter


def get_pdf_page_count(pdf_path):
    reader = PdfReader(pdf_path)
    return len(reader.pages)


def cleanup_old_backups(base_pdf, days=90):
    base_dir = os.path.dirname(base_pdf)
    base_stem = os.path.splitext(os.path.basename(base_pdf))[0]
    tmp_dir = os.path.join(base_dir, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    cutoff = datetime.now() - timedelta(days=days)

    for name in os.listdir(tmp_dir):
        if name.startswith(f"{base_stem}_backup_") and name.lower().endswith(".pdf"):
            path = os.path.join(tmp_dir, name)
            if datetime.fromtimestamp(os.path.getmtime(path)) < cutoff:
                os.remove(path)


def make_backup(base_pdf):
    base_dir = os.path.dirname(base_pdf)
    base_stem = os.path.splitext(os.path.basename(base_pdf))[0]
    tmp_dir = os.path.join(base_dir, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(tmp_dir, f"{base_stem}_backup_{timestamp}.pdf")
    shutil.copy2(base_pdf, backup_path)
    return backup_path


def insert_pdfs_after_page(base_pdf, insert_pdfs, after_page):
    """
    after_page: 사용자 기준 페이지 번호, 1부터 시작
    """
    cleanup_old_backups(base_pdf)
    make_backup(base_pdf)

    base_reader = PdfReader(base_pdf)
    writer = PdfWriter()

    total_pages = len(base_reader.pages)

    if after_page < 1 or after_page > total_pages:
        raise ValueError(f"페이지 번호는 1부터 {total_pages} 사이여야 합니다.")

    # 기준 PDF 앞부분
    for i in range(after_page):
        writer.add_page(base_reader.pages[i])

    # 삽입 PDF들
    for pdf in insert_pdfs:
        insert_reader = PdfReader(pdf)
        for page in insert_reader.pages:
            writer.add_page(page)

    # 기준 PDF 뒷부분
    for i in range(after_page, total_pages):
        writer.add_page(base_reader.pages[i])

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        temp_path = tmp.name

    with open(temp_path, "wb") as f:
        writer.write(f)

    os.replace(temp_path, base_pdf)