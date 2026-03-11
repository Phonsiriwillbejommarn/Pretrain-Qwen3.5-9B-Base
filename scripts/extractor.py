import fitz  # PyMuPDF
import re
import pythainlp
from pythainlp.util import normalize

def clean_thai_text(text):
    """
    ทำความสะอาดข้อความภาษาไทย:
    1. ลบช่องว่างที่มากเกินปกติ
    2. แก้ปัญหาสระลอย/จมด้วย PyThaiNLP normalize
    3. ลบ Header/Footer ขยะ (เช่น สำนักงานคณะกรรมการกฤษฎีกา)
    4. เชื่อมต่อบรรทัดที่โดนตัด (Heuristics ของภาษาไทย)
    """
    if not text:
        return ""
    
    # ลบ Whitespace ที่ซ้ำซ้อน แต่เก็บ \n ไว้ก่อนเพื่อจัดย่อหน้า
    text = re.sub(r'[ ]+', ' ', text)
    
    # ใช้ normalize ของ PyThaiNLP แก้สระลอย
    text = normalize(text)
    
    # กำจัดคำขยะ/ลายน้ำที่เจอบ่อย
    watermarks_to_remove = [
        "สำนักงานคณะกรรมการกฤษฎีกา",
    ]
    for wm in watermarks_to_remove:
        text = text.replace(wm, "")
    
    # แก้ปัญหาบรรทัดถูกตัดกลางประโยค
    lines = text.split('\n')
    cleaned_lines = []
    
    # ตัวอักษรที่บ่งบอกว่าประโยคจบแล้ว
    SENTENCE_ENDINGS = (')', ')', '"', '"', '>', '』', '।')
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # กรองบรรทัดขยะที่มักมีแต่เลข, ตัวคั่น, หรือข้อความสั้นเกิน
        if not line: continue
        if re.match(r'^(หน้า\s*)?\d+$', line): continue
        if re.match(r'^-\s*\d+\s*-$', line): continue # - ๑๐ - (เลขหน้าแนวนี้)
            
        if cleaned_lines:
            prev_line = cleaned_lines[-1]
            
            # ถ้าบรรทัดนี้ขึ้นต้นด้วย "มาตรา" เราให้มันแยกเป็นบรรทัดใหม่แน่นอน
            if re.match(r'^(มาตรา|ข้อ|หมวด|ส่วน|\d+\.)', line):
                cleaned_lines.append(line)
            # ถ้าบรรทัดก่อนหน้าจบด้วยเครื่องหมายที่บ่งบอกว่าจบประโยค → ขึ้นบรรทัดใหม่
            elif prev_line.endswith(SENTENCE_ENDINGS) or prev_line.endswith(' '):
                cleaned_lines.append(line)
            # ถ้าบรรทัดก่อนหน้าสั้นมาก (น่าจะเป็นหัวข้อ) → ขึ้นบรรทัดใหม่
            elif len(prev_line) < 20:
                cleaned_lines.append(line)
            else:
                # เชื่อมบรรทัดที่ถูกตัดกลางคัน
                cleaned_lines[-1] = prev_line + line
        else:
            cleaned_lines.append(line)
            
    # พอทำเสร็จ ลบช่องว่างส่วนเกินอีกที
    result = '\n'.join(cleaned_lines)
    result = re.sub(r'\n{3,}', '\n\n', result) # จำกัดจำนวนขึ้นบรรทัดใหม่
    return result

def extract_text_from_pdf(pdf_path):
    """ดึงข้อความทั้งหมดจากเอกสาร PDF และทำความสะอาด"""
    try:
        with fitz.open(pdf_path) as doc:
            full_text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text("text")
                full_text += text + "\n"
            
        return clean_thai_text(full_text)
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""

def extract_text_from_txt(txt_path):
    """อ่านข้อความจากไฟล์ .txt (ที่ scrape มาจากเว็บ) และทำความสะอาด"""
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return clean_thai_text(text)
    except Exception as e:
        print(f"Error reading {txt_path}: {e}")
        return ""

def extract_text(file_path):
    """ดึงข้อความจากไฟล์ รองรับทั้ง PDF และ TXT"""
    if file_path.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.lower().endswith('.txt'):
        return extract_text_from_txt(file_path)
    else:
        print(f"Unsupported file type: {file_path}")
        return ""

if __name__ == "__main__":
    print("Extractor initialized. Supports: .pdf, .txt")
    print("Usage: from extractor import extract_text")
