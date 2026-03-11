import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

def download_file(url, output_folder):
    """ฟังก์ชันหลักสำหรับดาวน์โหลดไฟล์ 1 ไฟล์"""
    os.makedirs(output_folder, exist_ok=True)
    
    try:
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()
        
        # ถอดรหัสชื่อไฟล์ภาษาไทย (ถ้าชื่อยาวไปอาจต้องตัด)
        filename = unquote(url.split('/')[-1])
        if not filename.endswith('.pdf'):
            # เผื่อลิงก์ไม่มีนามสกุล .pdf ต่อท้าย แต่บังคับโหลดมาเป็น pdf
            filename += '.pdf'
            
        file_path = os.path.join(output_folder, filename)
        
        # ข้ามถ้าโหลดมาแล้ว
        if os.path.exists(file_path):
            print(f"[{filename}] Skip: Already exists.")
            return True

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print(f"[{filename}] Status: Download Success!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"[Error] Failed to download {url}: {e}")
        return False

def pull_pdfs_from_page(page_url, output_folder):
    """ควานหาและดาวน์โหลดไฟล์ PDF ทุกไฟล์ที่อยู่ในหน้าเว็บที่ระบุ"""
    print(f"\n--- Scanning Page: {page_url} ---")
    try:
        response = requests.get(page_url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # หา tag <a> ทั้งหมดที่มีลิงก์จบด้วย .pdf 
        links = soup.find_all('a', href=True)
        pdf_urls = []
        
        for a in links:
            href = a['href']
            # เช็คคำว่า .pdf ไม่ว่าพิมพ์ด้วยตัวเล็กหรือใหญ่
            if href.lower().endswith('.pdf') or '.pdf?' in href.lower():
                full_url = urljoin(page_url, href)
                pdf_urls.append(full_url)
                
        # กำจัดลิงก์ซ้ำ
        pdf_urls = list(set(pdf_urls))
        
        if not pdf_urls:
            print("No PDF links found on this page.")
            return

        print(f"Found {len(pdf_urls)} PDF(s). Starting download...")
        for pdf_url in pdf_urls:
            download_file(pdf_url, output_folder)
            
        print("--- Completed Page Scan ---\n")
            
    except requests.exceptions.RequestException as e:
        print(f"Error accessing the webpage: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Thai Legal PDF Downloader")
    parser.add_argument("--url", help="Direct PDF link or a Website URL to scan for PDFs")
    parser.add_argument("--file", help="Path to a text file containing a list of URLs (one per line)")
    parser.add_argument("--output", default="../raw_pdfs", help="Folder to save PDFs (default: ../raw_pdfs)")
    
    args = parser.parse_args()
    
    if args.url:
        if args.url.lower().endswith('.pdf'):
            download_file(args.url, args.output)
        else:
            pull_pdfs_from_page(args.url, args.output)
            
    elif args.file:
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found.")
            return
            
        with open(args.file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
            
        print(f"Found {len(urls)} URLs in file.")
        for url in urls:
            if url.lower().endswith('.pdf'):
                download_file(url, args.output)
            else:
                pull_pdfs_from_page(url, args.output)
    else:
        print("Please provide a --url or a --file containing links.")

if __name__ == "__main__":
    main()
