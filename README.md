# Pretrain-Qwen3.5-9B-Base: Thai Legal PDF Extraction Pipeline

โปรเจกต์นี้มีเป้าหมายเพื่อแปลงไฟล์ PDF กฎหมายไทย (เช่น ประมวลกฎหมายอาญา, พรบ. ต่างๆ) และ**ข้อมูลจากเว็บไซต์** ให้อยู่ในฟอร์แมตข้อมูลคุณภาพสูงสำหรับการพัฒนา AI ด้านกฎหมายไทย โดยรองรับ 2 รูปแบบหลัก:

1. **RAG (Retrieval-Augmented Generation):** ซอยเอกสารเป็นก้อน (Chunks) ตามราย "มาตรา" หรือ "หมวด" เพื่อให้ Search ดึงข้อมูลความแม่นยำสูง
2. **CPT (Continued Pre-Training):** รวบรวมข้อความเป็นบริบทเนื้อหายาวๆ เพื่อ Fine-tune/Pretrain โมเดล Foundation อย่าง `Qwen3.5-9B-Base` ให้ซึมซับภาษากฎหมายไทย

---

## 📂 โครงสร้างโฟลเดอร์ (Directory Structure)

```text
├── raw_pdfs/            # (Input) โฟลเดอร์เก็บไฟล์ PDF และ TXT ต้นฉบับ
├── scripts/             # โฟลเดอร์เก็บโค้ด Python สำหรับสกัดข้อมูล
│   ├── downloader.py    # โหลดไฟล์ PDF หรือดึงข้อความจากเว็บไซต์
│   ├── extractor.py     # ระบบอ่าน PDF/TXT และลบคำขยะ (เช่น สำนักงานกฤษฎีกา, สระลอย)
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
pip3 install -r requirements.txt
```

*(ไลบรารีหลักๆ: `PyMuPDF` อ่าน PDF, `PyThaiNLP` จัดการสระลอย, `requests` + `beautifulsoup4` ดึงข้อมูลจากเว็บ)*

### 2. นำข้อมูลเข้าสู่ระบบ
คุณสามารถนำข้อมูลเข้ามาได้ 3 วิธี:

- **วิธีที่ 1: ใส่ไฟล์ PDF เอง** — นำไฟล์ PDF กฎหมายมาวางในโฟลเดอร์ `raw_pdfs/`

- **วิธีที่ 2: โหลด PDF จากเว็บอัตโนมัติ** — สแกนหา PDF ในหน้าเว็บ
  ```bash
  cd scripts

  # โหลดจากลิงก์ PDF โดยตรง
  python3 downloader.py --url https://example.com/law.pdf

  # ค้นหาและดูดทุก PDF ที่ซ่อนอยู่ในหน้าเว็บ
  python3 downloader.py --url https://www.krisdika.go.th/laws
  ```

- **วิธีที่ 3: ดึงข้อความจากหน้าเว็บธรรมดา** — สำหรับเว็บที่ไม่มี PDF
  ```bash
  cd scripts

  # ระบบจะสแกนหา PDF ก่อน ถ้าไม่เจอจะ scrape ข้อความแทนอัตโนมัติ
  python3 downloader.py --url https://www.supremecourt.or.th/ประวัติศาลฎีกา

  # หรือบังคับ scrape ข้อความโดยข้าม PDF ไปเลย
  python3 downloader.py --url https://example.com/page --scrape
  ```

### 3. รันสคริปต์สกัดข้อความ
เปิด Terminal และรันคำสั่ง:

**สำหรับข้อมูล RAG:**
```bash
cd scripts
python3 rag_chunk.py
```
*ระบบจะสร้างไฟล์ `data_processed/rag_data.jsonl` โดยอัตโนมัติ*

**สำหรับข้อมูล CPT (Pre-training):**
```bash
cd scripts
python3 cpt_format.py
```
*ระบบจะสร้างไฟล์ `data_processed/cpt_data.jsonl` โดยอัตโนมัติ*

---

## 🧹 ระบบทำความสะอาดข้อมูลภาษาไทย (Thai Text Cleaning)
สคริปต์ `extractor.py` ถูกออกแบบมาให้แก้ปัญหายอดฮิตของ PDF กฎหมายไทย ได้แก่:
- ลบลายน้ำหรือ Footer เช่น `"สำนักงานคณะกรรมการกฤษฎีกา"`
- แก้ปัญหาสระลอย/จม โดยใช้ `PyThaiNLP.util.normalize`
- เชื่อมประโยคที่ถูกเว้นวรรคขาดตอนจากบรรทัดใหม่ ให้กลับมาเป็นย่อหน้าเดียวกัน
- กรองเลขหน้า และสัญลักษณ์จัดหน้าออกไป
- รองรับไฟล์ทั้ง `.pdf` และ `.txt`

---

พัฒนาเพื่อรองรับโครงสร้างการเทรน **Qwen3.5-9B-Base** สำหรับงานกฎหมายในประเทศไทยโดยเฉพาะ
