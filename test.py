from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# Service 経由でドライバーを設定
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# examtopicsのURL（マイクロソフトの資格であれば「https://www.examtopics.com/discussions/microsoft/」）
url = '{examtopicsでの対象ベンダーのURL}'

# 出力先ファイル
output_file = r'{URLの出力先}'

while url != '':
    driver.get(url)

    elements = driver.find_elements(By.CLASS_NAME, 'discussion-link')
    for element in elements:
        if 'AZ-104' in element.text:
            link = element.get_attribute('href')
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(link + '\n')

    # 次ページの確認
    elements_btn = driver.find_elements(By.CLASS_NAME, 'btn-sm')
    url = ''
    for element_btn in elements_btn:
        if 'Next' in element_btn.text:
            url = element_btn.get_attribute('href')
            break

driver.quit()
print(f'完了しました。結果は {output_file} に保存されました。')