import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

############ START PARAMS ############ 
####################################

BASE_URL = "https://80-cs-abcde.cloudshell.dev/"
OUTPUT_DIR = "downloaded_files"  
MAX_WORKERS = 5 

COOKIES = {
    "CloudShellAuthorization": "Bearer ya29.-",
    "CloudShellPartitionedAuthorization": "Bearer ya29.",
}

############ END PARAMS ############ 
#################################### 


HEADERS = {
 
}

def download_file(url, file_path):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure directory exists

        # if file exists and size matches before downloading
        response_head = requests.head(url, headers=HEADERS, cookies=COOKIES, allow_redirects=True)
        if response_head.status_code == 200:
            file_size = int(response_head.headers.get('content-length', 0))
            if os.path.exists(file_path) and os.path.getsize(file_path) == file_size:
                print(f"✅ Skipping {file_path} (already exists with same size)")
                return

        response = requests.get(url, headers=HEADERS, cookies=COOKIES, stream=True)
        response.raise_for_status()

        # Show download progress
        total_size = int(response.headers.get('content-length', 0))
        with open(file_path, "wb") as f, tqdm(
            desc=file_path, total=total_size, unit="B", unit_scale=True, leave=False
        ) as bar:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))
        
        print(f"✅ Downloaded: {file_path}")
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")

def get_links(url):
    """Fetches and extracts file and directory links from an NGINX index page."""
    try:
        response = requests.get(url, headers=HEADERS, cookies=COOKIES)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        links = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href in ["../", "./"]:
                continue  # Skip parent and self references
            full_url = urljoin(url, href)
            links.append(full_url)

        return links
    except Exception as e:
        print(f"❌ Error accessing {url}: {e}")
        return []

def crawl_and_download(url):
    """Recursively crawls and downloads files/directories in parallel."""
    links = get_links(url)

    files = [link for link in links if not link.endswith("/")]
    directories = [link for link in links if link.endswith("/")]

    # Download files in parallel
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(download_file, file, os.path.join(OUTPUT_DIR, urlparse(file).path.lstrip("/"))) for file in files]
        for future in futures:
            future.result()

    # Recursively crawl directories
    for directory in directories:
        crawl_and_download(directory)

if __name__ == "__main__":
    print("🚀 Starting recursive download...")
    crawl_and_download(BASE_URL)
    print("✅ Download completed!")
