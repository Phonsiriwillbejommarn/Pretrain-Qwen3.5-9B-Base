import json
import os
from extractor import extract_text_from_pdf

def format_for_cpt(text, source_name=""):
    """
    จัดเตรียมข้อความสำหรับการทำ Continued Pre-training 
    Qwen3.5-9B-Base ต้องการเอกสารเต็มๆ เพื่อเรียนรู้บริบท
    """
    
    # เพิ่ม Header ให้บอกโมเดลว่ากำลังอ่านอะไรอยู่ (ช่วยเรื่อง Instruction/Context)
    title = source_name.replace('.pdf', '').replace('_', ' ')
    
    cpt_content = f"เอกสารทางกฎหมาย: {title}\n\n"
    cpt_content += text
    
    return {
        "text": cpt_content,
        "source": source_name
    }

def process_pdfs_for_cpt(pdf_folder, output_jsonl):
    """อ่านทุก PDF ในโฟลเดอร์ แปลงและบันทึกเป็น CPT JSONL"""
    if not os.path.exists(pdf_folder):
         print(f"Folder not found: {pdf_folder}")
         return
         
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
    
    if not pdf_files:
         print(f"No PDF files found in {pdf_folder}")
         return

    all_docs = []
    
    # ดึงและสร้างเป็นก้อนเดียวทีละไฟล์
    for pdf_file in pdf_files:
        print(f"Processing {pdf_file} for CPT...")
        pdf_path = os.path.join(pdf_folder, pdf_file)
        cleaned_text = extract_text_from_pdf(pdf_path)
        doc = format_for_cpt(cleaned_text, source_name=pdf_file)
        all_docs.append(doc)
        
    # บันทึกเป็น JSONL
    print(f"Saving {len(all_docs)} documents to {output_jsonl}...")
    with open(output_jsonl, 'w', encoding='utf-8') as f:
        for doc in all_docs:
            json.dump(doc, f, ensure_ascii=False)
            f.write('\n')
            
    print("Done CPT processing.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process PDFs for CPT")
    parser.add_argument("--input", default="../raw_pdfs", help="Folder containing raw PDFs")
    parser.add_argument("--output", default="../data_processed/cpt_data.jsonl", help="Output JSONL file")
    args = parser.parse_args()
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    process_pdfs_for_cpt(args.input, args.output)
