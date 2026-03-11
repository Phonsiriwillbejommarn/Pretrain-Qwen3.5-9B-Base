import json
import os
from extractor import extract_text

def format_for_cpt(text, source_name=""):
    """
    จัดเตรียมข้อความสำหรับการทำ Continued Pre-training 
    Qwen3.5-9B-Base ต้องการเอกสารเต็มๆ เพื่อเรียนรู้บริบท
    """
    
    # เพิ่ม Header ให้บอกโมเดลว่ากำลังอ่านอะไรอยู่ (ช่วยเรื่อง Instruction/Context)
    title = source_name.replace('.pdf', '').replace('.txt', '').replace('_', ' ')
    
    cpt_content = f"เอกสารทางกฎหมาย: {title}\n\n"
    cpt_content += text
    
    return {
        "text": cpt_content,
        "source": source_name
    }

def process_files_for_cpt(input_folder, output_jsonl):
    """อ่านทุก PDF และ TXT ในโฟลเดอร์ แปลงและบันทึกเป็น CPT JSONL"""
    if not os.path.exists(input_folder):
         print(f"Folder not found: {input_folder}")
         return
         
    supported_ext = ('.pdf', '.txt')
    input_files = [f for f in os.listdir(input_folder) if f.lower().endswith(supported_ext)]
    
    if not input_files:
         print(f"No PDF/TXT files found in {input_folder}")
         return

    all_docs = []
    
    # ดึงและสร้างเป็นก้อนเดียวทีละไฟล์
    for filename in input_files:
        print(f"Processing {filename} for CPT...")
        file_path = os.path.join(input_folder, filename)
        cleaned_text = extract_text(file_path)
        doc = format_for_cpt(cleaned_text, source_name=filename)
        all_docs.append(doc)
        
    # บันทึกเป็น JSONL
    os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
    print(f"Saving {len(all_docs)} documents to {output_jsonl}...")
    with open(output_jsonl, 'w', encoding='utf-8') as f:
        for doc in all_docs:
            json.dump(doc, f, ensure_ascii=False)
            f.write('\n')
            
    print("Done CPT processing.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process PDFs/TXTs for CPT")
    parser.add_argument("--input", default="../raw_pdfs", help="Folder containing raw PDFs/TXTs")
    parser.add_argument("--output", default="../data_processed/cpt_data.jsonl", help="Output JSONL file")
    args = parser.parse_args()
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    process_files_for_cpt(args.input, args.output)

