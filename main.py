import re                 # 正则匹配所需字符串
import time               # 延时 时间戳(文件、文件夹命名)
import json               # 字符串 转 dict
import urllib             # 解码
from pathlib import Path  # 路径操作
from typing import List   # 类型提示

import requests           # 发送请求

from model import Book, Doc
from config import COOKIE, XCSRFTOKEN, TIMEINTERVAL   # 配置项


# 获取所有知识库
def get_books() -> List[Book]:
    url = "https://www.yuque.com/api/mine/common_used"
    headers = {
        "accept": "application/json",
        "accept-language": "zh-CN,zh;q=0.9",
        "content-type": "application/json",
        "sec-ch-ua": "\"Chromium\";v=\"118\", \"Google Chrome\";v=\"118\", \"Not=A?Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-csrf-token": XCSRFTOKEN,
        "x-requested-with": "XMLHttpRequest",
        "cookie": COOKIE,
        "Referer": "https://www.yuque.com/",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }
    res = requests.get(url=url, headers=headers).json()
    books = res['data']['books']

    books = [Book(**{
        "id": book["target"]["id"],
        "name": book["target"]["name"],
        "slug": book["target"]["slug"],
        "user": book["target"]["user"]["login"],
    }) for book in books]
    return books


# 从字符串中匹配目录信息
def match_catalog_str(html: str, book: Book) -> str:
    r = r"window\.appData\s?=\s?JSON\.parse\(decodeURIComponent\(\"[\w\W\%]+?\"\)\);\s?\}\)\(\);"
    d = re.search(r, html)
    text = d.group() if d is not None else None
    if text is None:
        print('获取目录失败，程序退出:', book.name)
        exit()
        return None
    text = re.sub(
        r'window\.appData\s?=\s?JSON\.parse\(decodeURIComponent\(\"', '', text)
    text = re.sub(r'\"\)\);\s?\}\)\(\);', '', text)
    return text


# 获取指定知识库的所有文档
def get_book_docs(book: Book) -> List[Doc]:
    url = f'https://www.yuque.com/{book.user}/{book.slug}'
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "max-age=0",
        "sec-ch-ua": "\"Chromium\";v=\"118\", \"Google Chrome\";v=\"118\", \"Not=A?Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "service-worker-navigation-preload": "true",
        "upgrade-insecure-requests": "1",
        "cookie": COOKIE,
        "Referer": "https://www.yuque.com/dashboard",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }
    res = requests.get(url=url, headers=headers)

    # 正则匹配目录数据字符串
    text = match_catalog_str(res.text, book)

    # 解码
    text = urllib.parse.unquote(text)

    # str 转 dict
    data = json.loads(text)
    toc = data["book"]["toc"]
    mapping = dict(zip([i['uuid'] for i in toc], toc))

    # 获取上级目录信息
    def get_parents(d):
        if "parent_uuid" not in d or d["parent_uuid"] == "":
            return []
        p = [mapping[d["parent_uuid"]]]

        while True:
            pl = p[-1]
            if "parent_uuid" not in pl or pl["parent_uuid"] == "":
                break
            p.append(mapping[pl["parent_uuid"]])

        return p

    docs = []
    for doc in data["book"]["toc"]:
        if doc["type"] == "DOC":
            li = Doc(
                id=doc["id"],
                uuid=doc["uuid"],
                parent_uuid=doc["parent_uuid"],
                title=doc["title"],
                url=doc["url"],
                book=book,
                parents=get_parents(doc)
            )
            docs.append(li)
    return docs


# 下载指定文档
def download_doc(doc: Doc, path: str):
    url = f"https://www.yuque.com/{doc.book.user}/{doc.book.slug}/{doc.url}/markdown?attachment=true&latexcode=true&anchor=false&linebreak=false"

    headers = {
        "accept": "application/json",
        "accept-language": "zh-CN,zh;q=0.9",
        "content-type": "application/json",
        "sec-ch-ua": "\"Chromium\";v=\"118\", \"Google Chrome\";v=\"118\", \"Not=A?Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-csrf-token": XCSRFTOKEN,
        "x-requested-with": "XMLHttpRequest",
        "cookie": COOKIE,
        "Referer": "https://www.yuque.com/dashboard",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }

    res = requests.get(url=url, headers=headers)
    with open(path, 'wb') as f:
        f.write(res.content)
        f.close()


# 创建文件夹
def create_dir(path: str):
    # 创建连续多级目录
    folder = Path(path)
    if not folder.exists():
        folder.mkdir(parents=True)


# 文件名处理
def get_file_name(file_dir: str, title: str):
    create_dir(file_dir)

    not_support = {
        '|': '-',
        '/': '-',
        '\\': '-',
        ':': '-',
        '"': '\'',
        '<': '(',
        '>': ')',
        '?': '',
        ',': '',
    }
    for k in not_support:
        title = title.replace(k, not_support[k])

    file_name = Path(file_dir, f'{title}.md')
    if file_name.exists():
        file_name = Path(file_dir, f'{title}_{int(time.time()*1000)}.md')
    return file_name


def main():

    # 备份的根目录：当前文件所在文件夹下的 Backup_169****** 文件夹
    base_path = Path(__file__).parent
    base_path = Path(base_path, f'Backup_{int(time.time())}')
    create_dir(base_path)
    print('备份文件将被存储到：', base_path)

    # 遍历知识库
    books = get_books()
    for book in books:

        # 遍历知识库下所有文档
        docs = get_book_docs(book)
        count = 0
        for doc in docs:
            # 文档存储路径
            file_dir = Path(base_path, *[i["title"]
                            for i in doc.parents][::-1])
            file_name = get_file_name(file_dir, doc.title)

            # 下载文档
            download_doc(doc, file_name)
            count += 1
            print(f'备份进度  {book.name} :  {len(docs)} / {count}')

            # 延时，避免速度过快被封
            time.sleep(TIMEINTERVAL)

    print('备份文件完成，存储目录为：', base_path)


main()
