# 必要なライブラリ
!pip install tqdm

import requests
from bs4 import BeautifulSoup
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# 入力
target_exam = input("検索する試験名を入力してください: ")
category_name = input("カテゴリ名を入力してください: ")
max_page = int(input("最終ページ番号を入力してください: "))
start_url = f'https://www.examtopics.com/discussions/{category_name}/'

# 処理対象のページURLを収集
all_urls = [f"{start_url}{i}" for i in range(1, max_page + 1)]

# 出力ファイル
output_filename = f'ExamTopics_{target_exam}_URL.txt'
output_filepath = os.path.join('/content', output_filename)
with open(output_filepath, mode='w') as f:
    pass  # ファイル初期化

# 各ページからリンク抽出（並列処理）
def fetch_and_extract_links(url, target_exam):
    try:
        # User-Agentヘッダーの設定
        # "https://whatmyuseragent.com/"などにアクセスし、自身のUser-Agentを設定してください
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        elements = soup.select('a.discussion-link')
        matches = []
        for element in elements:
            link_text = element.get_text()
            link_href = element.get('href')
            if target_exam.lower() in link_text.lower() and link_href:
                if not link_href.startswith('http'):
                    link_href = requests.compat.urljoin(url, link_href)
                matches.append(link_href)
        return matches
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return []

# 並列処理＋進捗表示＋バッチ書き込み
all_matches = []
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(fetch_and_extract_links, url, target_exam) for url in all_urls]
    for future in tqdm(as_completed(futures), total=len(futures), desc="🔍 ページ処理中", unit="ページ"):
        all_matches.extend(future.result())

# 一括書き込み
with open(output_filepath, mode='a') as f:
    for link in all_matches:
        print(link, file=f)

# ダウンロード
from google.colab import files
if os.path.exists(output_filepath):
    files.download(output_filepath)
else:
    print(f"Output file not found: {output_filepath}")

print("🎉 完了しました！")