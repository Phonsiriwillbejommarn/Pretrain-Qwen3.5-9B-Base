import json
import re
import os
from extractor import extract_text

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
        match = re.match(r'^(มาตรา\s*[\d๑-๙]+((\\/|-)?[\d๑-๙]+)*)', section)
        
        if match:
             current_section_name = match.group(1).strip()
             content = section[len(current_section_name):].strip()
        else:
             content = section
              
        # สร้างข้อความเต็มของ chunk
        full_text = f"{current_section_name} {content}".strip()
        
        # ถ้า chunk ยาวเกิน 1500 ตัวอักษร ให้ซอยย่อยตาม \n\n (ย่อหน้า)
        if len(full_text) > 1500:
            sub_chunks = full_text.split('\n\n')
            for idx, sub in enumerate(sub_chunks):
                sub = sub.strip()
                if sub:
                    chunks.append({
                        "source": source_name,
                        "section": f"{current_section_name} (ส่วน {idx+1})" if len(sub_chunks) > 1 else current_section_name,
                        "text": sub,
                        "char_length": len(sub)
                    })
        else:
            chunks.append({
                "source": source_name,
                "section": current_section_name,
                "text": full_text,
                "char_length": len(full_text)
            })
        
    return chunks

def process_files_for_rag(input_folder, output_jsonl):
    """อ่านทุก PDF และ TXT ในโฟลเดอร์ แปลงและบันทึกเป็น RAG JSONL"""
    if not os.path.exists(input_folder):
         print(f"Folder not found: {input_folder}")
         return
         
    supported_ext = ('.pdf', '.txt')
    input_files = [f for f in os.listdir(input_folder) if f.lower().endswith(supported_ext)]
    
    if not input_files:
         print(f"No PDF/TXT files found in {input_folder}")
         return

    all_chunks = []
    
    # ดึงและแบ่ง Chunk ทีละไฟล์
    for filename in input_files:
        print(f"Processing {filename} for RAG...")
        file_path = os.path.join(input_folder, filename)
        cleaned_text = extract_text(file_path)
        chunks = split_into_rag_chunks(cleaned_text, source_name=filename)
        all_chunks.extend(chunks)
        
    # บันทึกเป็น JSONL
    os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
    print(f"Saving {len(all_chunks)} chunks to {output_jsonl}...")
    with open(output_jsonl, 'w', encoding='utf-8') as f:
        for chunk in all_chunks:
            json.dump(chunk, f, ensure_ascii=False)
            f.write('\n')
            
    print("Done RAG processing.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process PDFs/TXTs for RAG")
    parser.add_argument("--input", default="../raw_pdfs", help="Folder containing raw PDFs/TXTs")
    parser.add_argument("--output", default="../data_processed/rag_data.jsonl", help="Output JSONL file")
    args = parser.parse_args()
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    process_files_for_rag(args.input, args.output)

