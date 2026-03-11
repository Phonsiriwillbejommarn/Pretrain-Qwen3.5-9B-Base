import json
import re
import os
from extractor import extract_text_from_pdf

def split_into_rag_chunks(text, source_name=""):
    """
    แบ่งข้อความกฎหมายออกเป็น Chunk ตาม "มาตรา" หรือย่อหน้า
    เหมาะสำหรับการทำ RAG เพราะ 1 Chunk = 1 หัวข้อ (ระบุ Metadata ได้ชัดเจน)
    """
    chunks = []
    
    # 1. ลองแบ่งตามคำว่า "มาตรา {เลข}"
    # ใช้ Regex หาคำว่า มาตรา ตามด้วยตัวเลข เพื่อเป็นจุดตัด
    # รูปแบบอาจจะเป็น "มาตรา ๑", "มาตรา 1" เป็นต้น (กฎหมายไทยบางทีใช้เลขไทย)
    sections = re.split(r'(?=มาตรา\s*[\d๑-๙]+)', text)
    
    current_section_name = "ทั่วไป" # กรณีบทนำก่อนเข้าเนื้อหามาตรา
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        # หาชื่อมาตราใน chunk วางเป็น Metadata
        # ตัวอย่าง "มาตรา 14 ผู้ใดกระทำความผิด..."
        match = re.match(r'^(มาตรา\s*[\d๑-๙]+((\/|-)?[\d๑-๙]+)*)', section)
        
        if match:
             current_section_name = match.group(1).strip()
             content = section[len(current_section_name):].strip()
        else:
             content = section
             
        # ถ้าเนื้อหายังยาวเกินไป (เช่นเกิน 1000 ตัวอักษร) อาจจะต้องซอยย่อยด้วย \n ย่อหน้า
        # ในที่นี้จะเก็บเป็นก้อนเดียวกันก่อน
        chunks.append({
            "source": source_name,
            "section": current_section_name,
            "text": f"{current_section_name} {content}".strip(),
            "char_length": len(content)
        })
        
    return chunks

def process_pdfs_for_rag(pdf_folder, output_jsonl):
    """อ่านทุก PDF ในโฟลเดอร์ แปลงและบันทึกเป็น RAG JSONL"""
    if not os.path.exists(pdf_folder):
         print(f"Folder not found: {pdf_folder}")
         return
         
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
    
    if not pdf_files:
         print(f"No PDF files found in {pdf_folder}")
         return

    all_chunks = []
    
    # ดึงและแบ่ง Chunk ทีละไฟล์
    for pdf_file in pdf_files:
        print(f"Processing {pdf_file} for RAG...")
        pdf_path = os.path.join(pdf_folder, pdf_file)
        cleaned_text = extract_text_from_pdf(pdf_path)
        chunks = split_into_rag_chunks(cleaned_text, source_name=pdf_file)
        all_chunks.extend(chunks)
        
    # บันทึกเป็น JSONL
    print(f"Saving {len(all_chunks)} chunks to {output_jsonl}...")
    with open(output_jsonl, 'w', encoding='utf-8') as f:
        for chunk in all_chunks:
            json.dump(chunk, f, ensure_ascii=False)
            f.write('\n')
            
    print("Done RAG processing.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process PDFs for RAG")
    parser.add_argument("--input", default="../raw_pdfs", help="Folder containing raw PDFs")
    parser.add_argument("--output", default="../data_processed/rag_data.jsonl", help="Output JSONL file")
    args = parser.parse_args()
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    process_pdfs_for_rag(args.input, args.output)
