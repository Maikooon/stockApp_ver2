import requests
from bs4 import BeautifulSoup
import re
import logging

source = 'https://kabuyoho.ifis.co.jp/index.php?action=tp1&sa=report_top&bcode=' 
CODE = "6758"


# 決算日取得関数 
def get_settleInfo(CODE):
    # クローリング
    try:
        logging.debug('read web data cord = ' + CODE)  # logging
        r = requests.get(source + CODE)
        
    except ValueError:
        logging.debug('read web data ---> Exception Error')  # vlogging
        return None, 'Exception error: access failed'
    
    # スクレイピング
    soup = BeautifulSoup(r.content, "html.parser")
    settleInfo = soup.find("div", class_="header_main").text
    settleInfo = re.sub(r'[\n\t]+', ',', settleInfo)  # メタ文字の除去
    settleInfo = re.sub(r'(^,)|(,$)', '', settleInfo)  # 行頭行末のカンマ除去
    settleInfo = re.sub(r'[\xc2\xa0]', '', settleInfo)  # &nbsp(\xc2\xa0)問題の処置
    logging.debug('settleInfo result = ' + settleInfo)  # logging

    if not settleInfo:
        settleInfo = 'not found'

    return settleInfo


output = get_settleInfo(CODE)


def transformStyle(inputText):
    parts = inputText.split(',')
    date = parts[7].strip()
    dateParts = date.split('/')
    if len(dateParts) != 3:
        return "日付の形式が正しくありません。"
    formattedDate = f"{dateParts[0]}.{dateParts[1]}"
    title = parts[1].strip()
    quarter = parts[5].strip()
    result = f"{formattedDate}\n{dateParts[2]} {title} {quarter}決算発表"
    return result


if __name__ == '__main__':
    output = get_settleInfo(CODE)
    result = transformStyle(output)
    with open('output.txt', 'w') as f:
        f.write(result)
