import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote, urlparse

def get_browser_headers(url=None):
    """ส่งคืน Headers ที่ปลอมตัวเป็น Web Browser ปกติ"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    }
    if url:
        # ใช้ hostname ของ URL เป็น Referer หลอก
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        headers['Referer'] = f"https://{domain}/"
        headers['Host'] = domain
        
    return headers

def download_file(url, output_folder):
    """ฟังก์ชันหลักสำหรับดาวน์โหลดไฟล์ PDF 1 ไฟล์"""
    os.makedirs(output_folder, exist_ok=True)
    
    headers = get_browser_headers(url)
    filename = unquote(url.split('/')[-1])
    if not filename.endswith('.pdf'):
        filename += '.pdf'
        
    file_path = os.path.join(output_folder, filename)
    
    # ข้ามถ้าโหลดมาแล้ว
    if os.path.exists(file_path):
        print(f"[{filename}] Skip: Already exists.")
        return True
        
    try:
        response = requests.get(url, stream=True, timeout=30, headers=headers)
        response.raise_for_status()

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print(f"[{filename}] Status: Download Success!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"[Warning] requests failed for {url}: {e}. Retrying with Urllib fallback...")
        try:
            print(f"[Warning] requests failed for {url}. Retrying with curl fallback...")
            import subprocess
            
            # ใช้ curl นอก python เพื่อหลบ WAF fingerprinting
            cmd = [
                "curl", "-sL", "-A", headers['User-Agent'],
                "--compressed", "-k", "-o", file_path, url
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            
            # โชคร้ายที่บางเว็บส่ง 403 html กลับมาแทนไฟล์ pdf ใน curl
            # เช็คว่าไฟล์ที่ได้มามีขนาดมากกว่า 1KB ไหม (ถ้าเล็กกว่าแปลว่าเป็น HTML error page)
            if os.path.getsize(file_path) > 1024:
                print(f"[{filename}] Status: Download Success via curl!")
                return True
            else:
                os.remove(file_path)
                print(f"[Error] curl downloaded an invalid file/error page for {url}.")
                return False
                
        except Exception as fallback_e:
            print(f"[Error] Fallback also failed for {url}: {fallback_e}")
            return False

def scrape_page_text(page_url, output_folder):
    """ดึงข้อความจากหน้าเว็บธรรมดา (ไม่ใช่ PDF) และบันทึกเป็น .txt"""
    print(f"\n--- Scraping Text: {page_url} ---")
    os.makedirs(output_folder, exist_ok=True)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(page_url, timeout=15, headers=headers)
        response.raise_for_status()
        response.encoding = response.apparent_encoding  # แก้ปัญหา encoding ภาษาไทย
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ลบ tag ที่ไม่ต้องการ (เมนู, script, style ฯลฯ)
        for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
            tag.decompose()
        
        # ดึงข้อความจาก main content หรือ body
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        
        if not main_content:
            print("No text content found on this page.")
            return False
            
        # ดึงข้อความแต่ละ element แล้วรวม
        paragraphs = []
        for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'td', 'th', 'div', 'span']):
            text = element.get_text(strip=True)
            if text and len(text) > 5:  # กรองข้อความสั้นเกินไป
                paragraphs.append(text)
        
        # กำจัดบรรทัดซ้ำ (เพราะ div ซ้อน div อาจได้ข้อความเดิม)
        seen = set()
        unique_paragraphs = []
        for p in paragraphs:
            if p not in seen:
                seen.add(p)
                unique_paragraphs.append(p)
        
        full_text = '\n\n'.join(unique_paragraphs)
        
        if len(full_text.strip()) < 50:
            print("Page has too little text content. Skipping.")
            return False
        
        # สร้างชื่อไฟล์จาก URL
        parsed = urlparse(page_url)
        page_name = unquote(parsed.path.strip('/').replace('/', '_'))
        if not page_name:
            page_name = parsed.netloc.replace('.', '_')
        # ตัดให้ชื่อไม่ยาวเกิน
        page_name = page_name[:100]
        filename = f"{page_name}.txt"
        
        file_path = os.path.join(output_folder, filename)
        
        if os.path.exists(file_path):
            print(f"[{filename}] Skip: Already exists.")
            return True
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
            
        print(f"[{filename}] Scraped {len(full_text)} characters. Saved!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error scraping {page_url}: {e}")
        return False

def pull_pdfs_from_page(page_url, output_folder):
    """ควานหาและดาวน์โหลดไฟล์ PDF ทุกไฟล์ที่อยู่ในหน้าเว็บที่ระบุ
       ถ้าไม่เจอ PDF จะ fallback ไปดึงข้อความจากหน้าเว็บแทน
    """
    print(f"\n--- Scanning Page: {page_url} ---")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(page_url, timeout=10, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # หา tag <a> ทั้งหมดที่มีลิงก์จบด้วย .pdf 
        links = soup.find_all('a', href=True)
        pdf_urls = []
        
        for a in links:
            href = a['href']
            if href.lower().endswith('.pdf') or '.pdf?' in href.lower():
                full_url = urljoin(page_url, href)
                pdf_urls.append(full_url)
                
        # กำจัดลิงก์ซ้ำ
        pdf_urls = list(set(pdf_urls))
        
        if pdf_urls:
            print(f"Found {len(pdf_urls)} PDF(s). Starting download...")
            for pdf_url in pdf_urls:
                download_file(pdf_url, output_folder)
            print("--- Completed Page Scan ---\n")
        else:
            # ไม่เจอ PDF → ดึงข้อความจากหน้าเว็บแทน
            print("No PDF links found. Falling back to web scraping...")
            scrape_page_text(page_url, output_folder)
            
    except requests.exceptions.RequestException as e:
        print(f"Error accessing the webpage: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Thai Legal PDF Downloader & Web Scraper")
    parser.add_argument("--url", help="Direct PDF link or a Website URL to scan")
    parser.add_argument("--file", help="Path to a text file containing a list of URLs (one per line)")
    parser.add_argument("--output", default="../raw_pdfs", help="Folder to save files (default: ../raw_pdfs)")
    parser.add_argument("--scrape", action="store_true", help="Force scrape text from web page (skip PDF search)")
    
    args = parser.parse_args()
    
    if args.url:
        if args.scrape:
            # บังคับดึงข้อความจากเว็บโดยตรง
            scrape_page_text(args.url, args.output)
        elif args.url.lower().endswith('.pdf'):
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
            if args.scrape:
                scrape_page_text(url, args.output)
            elif url.lower().endswith('.pdf'):
                download_file(url, args.output)
            else:
                pull_pdfs_from_page(url, args.output)
    else:
        print("Please provide a --url or a --file containing links.")
        print("Examples:")
        print("  python downloader.py --url https://example.com/law.pdf")
        print("  python downloader.py --url https://example.com/laws")
        print("  python downloader.py --url https://example.com/page --scrape")

if __name__ == "__main__":
    main()
