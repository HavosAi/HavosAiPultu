from pprint import pprint
import os
import pandas as pd
import argparse
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfdocument import PDFDocument, PDFNoOutlines
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTPage, LTChar, LTAnno, LAParams, LTTextBox, LTTextLine

SECTIONS = ["Acknowledgements", "reference", "appendix", "appendic", "declaration", "note", "literature"]

class PDFPageDetailedAggregator(PDFPageAggregator):
    def __init__(self, rsrcmgr, pageno=1, laparams=None):
        PDFPageAggregator.__init__(self, rsrcmgr, pageno=pageno, laparams=laparams)
        self.rows = []
        self.page_number = 0

    def receive_layout(self, ltpage):        
        def render(item, page_number):
            if isinstance(item, LTPage) or isinstance(item, LTTextBox):
                for child in item:
                    render(child, page_number)
            elif isinstance(item, LTTextLine):
                child_str = ''
                for child in item:
                    if isinstance(child, (LTChar, LTAnno)):
                        child_str += child.get_text()
                child_str = ' '.join(child_str.split()).strip()
                if child_str:
                    row = (page_number, item.bbox[0], item.bbox[1], item.bbox[2], item.bbox[3], child_str) # bbox == (x1, y1, x2, y2)
                    self.rows.append(row)
                for child in item:
                    render(child, page_number)
            return
        render(ltpage, self.page_number)
        self.page_number += 1
        self.rows = sorted(self.rows, key = lambda x: (x[0], -x[2]))
        self.result = ltpage

def extract_text_from_pdf(filename):
    pages = []
    with open(filename, 'rb') as fp:
        parser = PDFParser(fp)
        doc = PDFDocument(parser)

        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageDetailedAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        
        for pid, page in enumerate(PDFPage.create_pages(doc)):
            try:
                interpreter.process_page(page)
                # receive the LTPage object for this page
                layout = device.get_result()
                text = []
                for lt_obj in sorted(layout, key=lambda x:(x.bbox[0] >= 300, -x.bbox[1])):
                    try:
                        #print(lt_obj.bbox)
                        #print(lt_obj.get_text())
                        text.append(lt_obj.get_text())
                    except:
                        pass
                pages.append("\n".join(text))
            except Exception as err:
                print(err)
    return pages

def contains_keywords(text, keywords, startswith=False):
    for key_word in keywords:
        if startswith:
            if text.lower().startswith(key_word):
                return True
        else:
            if key_word in text.lower():
                return True
    return False

def contains_acknowldgements(text):
    return contains_keywords(text, ["acknowledgment", "acknowledgement", "funding", "we thank", "we would like to thank",
        "acknowledge", "funded by", "we are grateful", "we want to thank", "this work was supported",
        "this research was supported", "this study was supported", "this work was financially supported",
        "this research was financially supported", "this study was financially supported"], startswith=False)

def contains_other_section_keywords(text):
    return contains_keywords(text, ["reference", "appendix", "appendic", "declaration", "note", "literature"], startswith=True)

def extract_acknowledgement_part(filename):
    pages = extract_text_from_pdf(filename)
    text_to_use = []
    for page in range(len(pages)-1, -1, -1):
        if contains_acknowldgements(pages[page]):
            all_text = "\n\n".join(pages[page:])
            start = False
            for line in all_text.split("\n"):
                line_to_check = line.replace(" ", "").strip() if line.isupper() else line
                if contains_acknowldgements(line) or contains_acknowldgements(line_to_check):
                    start = True
                if contains_other_section_keywords(line) or contains_other_section_keywords(line_to_check):
                    if start:
                        start = False
                        break
                if start:
                    text_to_use.append(line)
            break
    return "\n".join(text_to_use).strip()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--folders_with_pdfs')
    parser.add_argument('--folder_to_save')
    args = parser.parse_args()

    print("Folder with pdfs: %s"%args.folders_with_pdfs)
    print("Folder to save: %s"%args.folder_to_save)

    os.makedirs(args.folder_to_save, exist_ok=True)
    for folder in os.listdir(args.folders_with_pdfs):
        print(folder)
        excel_result_filename = os.path.join(args.folder_to_save, "%s.xlsx" % folder)
        df = pd.DataFrame()
        existing_folders_in_df = set()
        if os.path.exists(excel_result_filename):
            df = pd.read_excel(excel_result_filename).fillna("")
            existing_folders_in_df = set(list(df["pdf_file"].values))

        df = pd.concat([df, pd.DataFrame(
            {"pdf_file": list(set(os.listdir(os.path.join(args.folders_with_pdfs, folder))) - existing_folders_in_df)})], axis=0).fillna("")
        print(len(df))
        if "acknowledgement_part" not in df.columns:
            df["acknowledgement_part"] = ""
        for i in range(len(df)):
            if not df["acknowledgement_part"].values[i].strip() or len(df["acknowledgement_part"].values[i].replace(" ", "").strip()) <= 50:
                print(df["pdf_file"].values[i])
                try:
                    df["acknowledgement_part"].values[i] = extract_acknowledgement_part(
                        os.path.join(args.folders_with_pdfs, folder, df["pdf_file"].values[i]))
                except Exception as err:
                    print(err)
        df.to_excel(excel_result_filename, engine="xlsxwriter", index=False, freeze_panes=(1, 0), header=True, encoding='utf8')