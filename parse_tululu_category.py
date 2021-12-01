import argparse
import json
import logging
import os
import re
import urllib

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from requests import HTTPError
from urllib.parse import urljoin, urlparse


def check_for_redirect(response):
    if response.history:
        raise HTTPError(f'{response.history} - {HTTPError.__name__}')


def download_txt(content_book, count, payload, folder='books'):
    url_download = f'https://tululu.org/txt.php'
    response_download = requests.get(url_download, params=payload)
    check_for_redirect(response_download)
    os.makedirs(folder, exist_ok=True)
    filename = sanitize_filename(f"{count}.{content_book['title'].strip()}.txt")
    file_path = os.path.join(folder, filename)
    content_book['book_path'] = file_path
    with open(file_path, 'w') as file:
        file.write(response_download.text)
        return content_book


def get_tail_url(url):
    parse_path_url = urlparse(url)
    path_clean = urllib.parse.unquote(parse_path_url.path)
    _, url_file_name = os.path.split(path_clean)
    url_name, url_tail = os.path.splitext(url_file_name)
    return url_name, url_tail


def download_image(content_book, book_id, folder):
    os.makedirs(folder, exist_ok=True)
    url_name, url_tail = get_tail_url(url=content_book['image_link'])
    response_download_image = requests.get(content_book['image_link'])
    response_download_image.raise_for_status()
    check_for_redirect(response_download_image)
    filename = sanitize_filename(f"{book_id}{url_tail}")
    file_path = os.path.join(folder, filename)
    content_book['img_src'] = file_path
    with open(file_path, 'wb') as image:
        image.write(response_download_image.content)
    return generates_info_books(content_book)


def parse_book_page(soup):
    host = 'https://tululu.org/'
    title_book_tag = soup.find(id='content').find('h1').get_text(strip=True)
    genre_book = [genre.text for genre in soup.find('span', class_='d_book').find_all('a')]
    comments = soup.find_all(class_="texts")
    image_link = soup.find(class_='bookimage').find('img')['src']
    url_image = urljoin(host, image_link)
    title_book, author = title_book_tag.split('::')
    comments_book = [comment_tag.find('span', class_="black").get_text(strip=True) for comment_tag in comments]
    content_book = {
        'title': title_book.strip(),
        'author': author,
        'genres': genre_book,
        'image_link': url_image,
        'comments': comments_book,
    }
    return content_book


def get_arguments():
    parser = argparse.ArgumentParser(
        description='The code collects book data from an online library.'
    )
    parser.add_argument(
        '-s', '--start_id', type=int, help="Set the initial id for book use arguments: '-s or --start_id'"
    )
    parser.add_argument(
        '-e', '--end_id', type=int, help="Set the end id for book use arguments: '-e or --end_id'"
    )
    args = parser.parse_args()
    return args.start_id, args.end_id


def get_link_book():
    genre = 55
    content = []
    for page in range(1, 5):
        url = f"https://tululu.org/l{genre}/{page}"
        response_link_book = requests.get(url)
        response_link_book.raise_for_status()
        content.append(BeautifulSoup(response_link_book.text, "lxml"))
    return content


def get_id_book_page():
    content = get_link_book()
    pre_links = []
    for line in content:
        first_book = line.find_all(class_="d_book")
        pre_links.append([indexes.find("a")["href"] for indexes in first_book])
    return pre_links


def get_links_book():
    indexies_book = get_id_book_page()
    for id_book in indexies_book:
        for index_book in id_book:
            yield index_book


def generates_info_books(content_book):
    return {
            'title': content_book['title'],
            'author': content_book['author'],
            'img_src': content_book['img_src'],
            'book_path': content_book['book_path'],
            'comments': content_book['comments'],
    }


def main():
    logging.basicConfig(
        level=logging.WARNING,
        filename='logs.log',
        filemode='w',
        format='%(asctime)s - [%(levelname)s] - %(funcName)s() - [line %(lineno)d] - %(message)s',
    )

    # start, end = get_arguments()
    start=1
    end=7
    count = 1
    json_books = []
    for book_id in get_links_book():
        payload = {'id': str(*re.findall(r'[0-9]+', str(book_id)))}
        url_title_book = f"https://tululu.org/b{str(*re.findall(r'[0-9]+', str(book_id)))}"
        response_title_book = requests.get(url_title_book)
        try:
            try:
                response_title_book.raise_for_status()
                check_for_redirect(response_title_book)
            except HTTPError as exc:
                logging.warning(exc)
            soup = BeautifulSoup(response_title_book.text, "lxml")
            content_book = parse_book_page(soup)
            download_txt(content_book, count, payload, folder="books")
            json_books.append(download_image(content_book, payload['id'], "image"))
        except HTTPError as exc:
            logging.warning(exc)

        count += 1

    with open('filename.json', 'w', encoding='utf8') as json_file:
        json.dump(json_books, json_file, ensure_ascii=False, indent=3)


if __name__ == "__main__":
    main()




