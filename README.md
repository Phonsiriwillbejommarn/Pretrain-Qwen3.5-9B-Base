# Pretrain-Qwen3.5-9B-Base: Thai Legal PDF Extraction Pipeline

โปรเจกต์นี้มีเป้าหมายเพื่อแปลงไฟล์ PDF กฎหมายไทย (เช่น ประมวลกฎหมายอาญา, พรบ. ต่างๆ) ให้อยู่ในฟอร์แมตข้อมูลคุณภาพสูงสำหรับการพัฒนา AI ด้านกฎหมายไทย โดยรองรับ 2 รูปแบบหลัก:

1. **RAG (Retrieval-Augmented Generation):** ซอยเอกสารเป็นก้อน (Chunks) ตามราย "มาตรา" หรือ "หมวด" เพื่อให้ Search ดึงข้อมูลความแม่นยำสูง
2. **CPT (Continued Pre-Training):** รวบรวมข้อความเป็นบริบทเนื้อหายาวๆ เพื่อ Fine-tune/Pretrain โมเดล Foundation อย่าง `Qwen3.5-9B-Base` ให้ซึมซับภาษากฎหมายไทย

---

## 📂 โครงสร้างโฟลเดอร์ (Directory Structure)

```text
├── raw_pdfs/            # (Input) โฟลเดอร์เก็บไฟล์ PDF ต้นฉบับ (ต้องเอา PDF มาวางที่นี่)
├── scripts/             # โฟลเดอร์เก็บโค้ด Python สำหรับสกัดข้อมูล
│   ├── extractor.py     # ระบบอ่าน PDF และลบคำขยะ (เช่น สำนักงานกฤษฎีกา, สระลอย)
│   ├── rag_chunk.py     # ตัวหั่นข้อความและแปลงเป็นไฟล์เอาไปทำ RAG
│   └── cpt_format.py    # ตัวรวมข้อความและแปลงเป็นไฟล์เอาไปทำ Pre-training
├── data_processed/      # (Output) โฟลเดอร์เก็บชุดข้อมูล JSONL ที่พร้อมใช้งาน
│   ├── rag_data.jsonl   # ข้อมูลถูกหั่นเป็น { "source", "section", "text", "char_length" }
│   └── cpt_data.jsonl   # ข้อมูลแบบ { "text", "source" }
├── requirements.txt     # รายการไลบรารีที่จำเป็น
└── README.md
```

---

## 🚀 วิธีการใช้งาน (How to use)

### 1. ติดตั้งไลบรารี
```bash
pip install -r requirements.txt
```

*(ไลบรารีหลักๆ ประกอบไปด้วย: `PyMuPDF` (fitz) เพื่ออ่าน PDF, `pythainlp` เพื่อจัดการสระลอย)*

### 2. นำไฟล์ PDF มาประมวลผล
ให้นำไฟล์เอกสารกฎหมายที่คุณต้องการ (ตย. `ประมวลกฎหมายอาญา.pdf`) มาใส่ไว้ในโฟลเดอร์ `raw_pdfs/`

### 3. รันสคริปต์สกัดข้อความ
เปิด Terminal และรันคำสั่ง:

**สำหรับข้อมูล RAG:**
```bash
cd scripts
python rag_chunk.py
```
*ระบบจะสร้างไฟล์ `data_processed/rag_data.jsonl` โดยอัตโนมัติ*

**สำหรับข้อมูล CPT (Pre-training):**
```bash
cd scripts
python cpt_format.py
```
*ระบบจะสร้างไฟล์ `data_processed/cpt_data.jsonl` โดยอัตโนมัติ*

---

## 🧹 ระบบทำความสะอาดข้อมูลภาษาไทย (Thai Text Cleaning)
สคริปต์ `extractor.py` ถูกออกแบบมาให้แก้ปัญหายอดฮิตของ PDF กฎหมายไทย ได้แก่:
- ลบลายน้ำหรือ Footer เช่น `"สำนักงานคณะกรรมการกฤษฎีกา"`
- แก้ปัญหาสระลอย/จม โดยใช้ `PyThaiNLP.util.normalize`
- เชื่อมประโยคที่ถูกเว้นวรรคขาดตอนจากบรรทัดใหม่ ให้กลับมาเป็นย่อหน้าเดียวกัน
- กรองเลขหน้า และสัญลักษณ์จัดหน้าออกไป

---

พัฒนาเพื่อรองรับโครงสร้างการเทรน **Qwen3.5-9B-Base** สำหรับงานกฎหมายในประเทศไทยโดยเฉพาะ
