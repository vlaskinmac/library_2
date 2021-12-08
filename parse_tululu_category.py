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


def download_txt(content_book, book_id, payload, user_path):
    url_download = f'https://tululu.org/txt.php'
    response_download = requests.get(url_download, params=payload)
    check_for_redirect(response_download)
    os.makedirs(user_path, exist_ok=True)
    books_path = os.path.relpath(os.path.join(user_path, "books_txt"))
    os.makedirs(books_path, exist_ok=True)
    filename = sanitize_filename(f"{book_id}.{content_book['title'].strip()}.txt")
    file_path = os.path.relpath(os.path.join(books_path, filename))
    with open(file_path, 'w') as file:
        file.write(response_download.text)
    return file_path


def download_image(url_image, book_id, user_path):
    url_name, url_tail = get_tail_url(url=url_image)
    response_download_image = requests.get(url_image)
    response_download_image.raise_for_status()
    check_for_redirect(response_download_image)
    os.makedirs(user_path, exist_ok=True)
    image_path = os.path.relpath(os.path.join(user_path, "image"))
    os.makedirs(image_path, exist_ok=True)
    filename = sanitize_filename(f"{book_id}{url_tail}")
    file_path = os.path.relpath(os.path.join(image_path, filename))
    with open(file_path, 'wb') as image:
        image.write(response_download_image.content)
    return file_path


def get_content_book(
        content_book, book_id, payload, user_path, url_image, skip_text_file, skip_image_file):
    if not skip_text_file:
        file_path_book = download_txt(content_book, book_id, payload, user_path)
        content_book['book_path'] = file_path_book

    if not skip_image_file:
        file_path_image = download_image(url_image, book_id, user_path)
        content_book['img_src'] = file_path_image
    return content_book


def get_tail_url(url):
    parse_path_url = urlparse(url)
    path_clean = urllib.parse.unquote(parse_path_url.path)
    _, url_file_name = os.path.split(path_clean)
    url_name, url_tail = os.path.splitext(url_file_name)
    return url_name, url_tail


def parse_book_page(soup):
    host = 'https://tululu.org/'
    title_book_tag = soup.select_one("#content h1").get_text(strip=True)
    genre_book = soup.select_one('span.d_book a')['title'].split(' -')[0]
    comments = soup.select(".texts")
    image_link = soup.select_one('.bookimage img')['src']
    url_image = urljoin(host, image_link)
    title_book, author = title_book_tag.split('::')
    comments_book = [comment_tag.select_one(".black").get_text(strip=True) for comment_tag in comments]
    content_book = {
        'title': title_book.strip(),
        'author': author,
        'genres': genre_book,
        'comments': comments_book,
    }
    return content_book, url_image


def get_arguments():
    parser = argparse.ArgumentParser(
        description='The code collects book data from an online library.'
    )
    parser.add_argument(
        '-s', '--start_page', type=int, required=True,
        help="Set the initial page, use arguments: '-s or --start_page'"
    )
    parser.add_argument(
        '-e', '--end_page', default=get_last_page(), type=int,
        help="Install the last page, use arguments: '-e or --end_page'"
    )
    parser.add_argument(
        '-d', '--dest_folder', default="./", action='store_const', const=True, help="Set path to the directory with parsing results: '-d or --dest_folder'"
    )
    parser.add_argument(
        '-j', '--json_path', default='./', help="Set the path to the json file, use the argument: '-j or --json_path'"
    )
    parser.add_argument(
        '-t', '--skip_txt', action='store_const', const=True,
        help="Set not to download books, use argument: '-t or --skip_txt'"
    )
    parser.add_argument(
        '-i', '--skip_imgs', action='store_const', const=True,
        help="Set not to download images, use argument: '-i or --skip_imgs'"
    )
    args = parser.parse_args()
    return args.start_page, args.end_page, args.dest_folder, args.json_path, args.skip_txt, args.skip_imgs


def get_last_page():
    genre = 55
    url = f"https://tululu.org/l{genre}"
    response_link_book = requests.get(url)
    response_link_book.raise_for_status()
    soup = BeautifulSoup(response_link_book.text, "lxml")
    title_book_tag = soup.select(".npage")
    last_page = [page.get_text(strip=True) for page in title_book_tag[-1]]
    return int(*last_page)


def get_book_page_ids(start, end):
    genre = 55
    ids = []
    for page in range(start, end + 1):
        url = f"https://tululu.org/l{genre}/{page}"
        response_link_book = requests.get(url)
        response_link_book.raise_for_status()
        soup = BeautifulSoup(response_link_book.text, "lxml")
        ids += [tag.select_one("a")["href"] for tag in soup.select(".d_book")]
    return ids


def main():
    logging.basicConfig(
        level=logging.WARNING,
        filename='logs.log',
        filemode='w',
        format='%(asctime)s - [%(levelname)s] - %(funcName)s() - [line %(lineno)d] - %(message)s',
    )

    json_books = []
    start, end, user_path, json_path, skip_text_file, skip_image_file = get_arguments()
    identifier_books = get_book_page_ids(start, end)
    for parse_book_id in identifier_books:
        book_id = re.search(r'\d+', parse_book_id).group()
        payload = {'id': book_id}
        url_book = f"https://tululu.org/b{book_id}"
        book_response = requests.get(url_book)
        try:
            book_response.raise_for_status()
            soup = BeautifulSoup(book_response.text, "lxml")
            content_book, url_image = parse_book_page(soup)
            collections_books = get_content_book(
                content_book, book_id, payload, user_path, url_image, skip_text_file, skip_image_file)
            json_books.append(collections_books)
        except HTTPError as exc:
            logging.warning(exc)

    with open(f'{json_path}filejson.json', 'w', encoding='utf8') as json_file:
        json.dump(json_books, json_file, ensure_ascii=False, indent=3)


if __name__ == "__main__":
    main()

