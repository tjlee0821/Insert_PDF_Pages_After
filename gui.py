import os
import tkinter as tk
import tkinter.messagebox as messagebox
import tkinter.simpledialog as simpledialog
from tkinterdnd2 import DND_FILES

from pdf_utils import (
    get_pdf_page_count,
    cleanup_old_backups,
    insert_pdfs_after_page,
)

from image_utils import files_to_pdf_list, cleanup_temp_files


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 특정 페이지 뒤에 삽입")
        self.root.geometry("460x460")
        self.root.resizable(False, False)

        self.base_pdf = None
        self.total_pages = 0
        self.selected_page = None

        self.label = tk.Label(
            root,
            text="PDF 또는 이미지를 드래그하세요\n\n첫 번째 PDF = 기준 PDF\n그 이후 파일 = 선택한 페이지 뒤에 삽입",
            font=("Arial", 14),
            justify="center"
        )
        self.label.pack(pady=25)

        self.status = tk.Label(
            root,
            text="기준 PDF: 없음",
            font=("Arial", 11),
            fg="gray"
        )
        self.status.pack(pady=10)

        self.page_info = tk.Label(
            root,
            text="페이지 선택: 기준 PDF 선택 후 표시됩니다",
            font=("Arial", 11)
        )
        self.page_info.pack(pady=8)

        self.page_frame = tk.Frame(root)
        self.page_frame.pack(pady=10)

        self.page_var = tk.IntVar(value=1)

        self.page_scale = tk.Scale(
            self.page_frame,
            from_=1,
            to=1,
            orient="horizontal",
            length=260,
            variable=self.page_var,
            command=self.on_scale_change,
            state="disabled"
        )
        self.page_scale.grid(row=0, column=0, padx=8)

        self.page_entry = tk.Entry(
            self.page_frame,
            width=8,
            font=("Arial", 13),
            justify="center",
            state="disabled"
        )
        self.page_entry.grid(row=0, column=1, padx=8)
        self.page_entry.bind("<Return>", self.on_entry_change)
        self.page_entry.bind("<FocusOut>", self.on_entry_change)

        self.help_text = tk.Label(
            root,
            text="아직 기준 PDF가 없습니다.",
            font=("Arial", 10),
            fg="blue"
        )
        self.help_text.pack(pady=15)

        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.on_drop)

    def on_scale_change(self, value):
        page = int(float(value))
        self.selected_page = page

        self.page_entry.config(state="normal")
        self.page_entry.delete(0, tk.END)
        self.page_entry.insert(0, str(page))

    def on_entry_change(self, event=None):
        if not self.base_pdf:
            return

        value = self.page_entry.get().strip()

        if not value.isdigit():
            messagebox.showwarning("경고", "숫자만 입력하세요.")
            return

        page = int(value)

        if page < 1 or page > self.total_pages:
            messagebox.showwarning(
                "경고",
                f"페이지 번호는 1부터 {self.total_pages} 사이여야 합니다."
            )
            return

        self.selected_page = page
        self.page_var.set(page)

    def set_base_pdf(self, pdf_path):
        self.base_pdf = pdf_path
        cleanup_old_backups(self.base_pdf)

        self.total_pages = get_pdf_page_count(self.base_pdf)
        self.selected_page = None

        self.status.config(
            text=f"기준 PDF: {os.path.basename(self.base_pdf)}"
        )

        self.page_info.config(
            text=f"삽입 위치 선택: 1 ~ {self.total_pages} 페이지 뒤"
        )

        self.page_scale.config(
            from_=1,
            to=self.total_pages,
            state="normal"
        )

        self.page_entry.config(state="normal")
        self.page_entry.delete(0, tk.END)

        self.help_text.config(
            text=f"1부터 {self.total_pages} 사이 숫자를 선택하거나 입력하세요."
        )

    def ask_page_if_needed(self):
        if self.selected_page:
            return self.selected_page

        page = simpledialog.askinteger(
            "삽입 위치 선택",
            f"집어넣을 파일을 몇 페이지 뒤에 넣을까요?\n\n1 ~ {self.total_pages} 사이 숫자 입력",
            minvalue=1,
            maxvalue=self.total_pages
        )

        if page is None:
            return None

        self.selected_page = page
        self.page_var.set(page)
        self.page_entry.delete(0, tk.END)
        self.page_entry.insert(0, str(page))

        return page

    def on_drop(self, event):
        files = list(self.root.tk.splitlist(event.data))

        if not files:
            return

        temp_files = []

        if not self.base_pdf:
            first_file = files[0]

            if not first_file.lower().endswith(".pdf"):
                messagebox.showwarning("경고", "첫 번째 기준 파일은 PDF여야 합니다.")
                return

            self.set_base_pdf(first_file)

            if len(files) == 1:
                return

            insert_files = files[1:]
            insert_pdfs, temp_files = files_to_pdf_list(insert_files)

        else:
            insert_pdfs, temp_files = files_to_pdf_list(files)

        if not insert_pdfs:
            messagebox.showwarning("경고", "PDF 또는 이미지 파일만 드롭하세요.")
            return

        page = self.ask_page_if_needed()

        if page is None:
            self.help_text.config(text="삽입이 취소되었습니다. 페이지를 먼저 선택하세요.")
            cleanup_temp_files(temp_files)
            return

        try:
            insert_pdfs_after_page(self.base_pdf, insert_pdfs, page)

            self.total_pages = get_pdf_page_count(self.base_pdf)
            self.page_scale.config(to=self.total_pages)
            self.page_info.config(
                text=f"삽입 위치 선택: 1 ~ {self.total_pages} 페이지 뒤"
            )

            messagebox.showinfo(
                "완료",
                f"{len(insert_pdfs)}개 파일을 {page}페이지 뒤에 삽입했습니다."
            )

        except Exception as e:
            messagebox.showerror("오류", str(e))

        finally:
            cleanup_temp_files(temp_files)