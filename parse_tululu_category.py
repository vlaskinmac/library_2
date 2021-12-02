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


def create_file_path(folder, file):
    cwd = os.getcwd()
    os.makedirs(f"books_content/{folder}", exist_ok=True)
    common_path = os.path.abspath(os.path.join(cwd, "books_content"))
    books_path = os.path.abspath(os.path.join(common_path, folder))
    file_path = os.path.abspath(os.path.join(books_path, file))
    return file_path


def download_txt(content_book, count, payload, folder, skip=False):
    url_download = f'https://tululu.org/txt.php'
    if not skip:
        response_download = requests.get(url_download, params=payload)
        check_for_redirect(response_download)
        filename = sanitize_filename(f"{count}.{content_book['title'].strip()}.txt")
        file_path = create_file_path(folder, filename)
        content_book['book_path'] = file_path
        with open(file_path, 'w') as file:
            file.write(response_download.text)
    else:
        content_book['book_path'] = " "


def get_tail_url(url):
    parse_path_url = urlparse(url)
    path_clean = urllib.parse.unquote(parse_path_url.path)
    _, url_file_name = os.path.split(path_clean)
    url_name, url_tail = os.path.splitext(url_file_name)
    return url_name, url_tail


def download_image(content_book, book_id, folder, skip=False):
    url_name, url_tail = get_tail_url(url=content_book['image_link'])
    if not skip:
        response_download_image = requests.get(content_book['image_link'])
        response_download_image.raise_for_status()
        check_for_redirect(response_download_image)
        filename = sanitize_filename(f"{book_id}{url_tail}")
        file_path = create_file_path(folder, filename)
        content_book['img_src'] = file_path
        with open(file_path, 'wb') as image:
            image.write(response_download_image.content)
    else:
        content_book['img_src'] = " "


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
        'image_link': url_image,
        'comments': comments_book,
    }
    return content_book


def get_arguments():
    parser = argparse.ArgumentParser(
        description='The code collects book data from an online library.'
    )
    parser.add_argument(
        '-s', '--start_page', type=int, required=True,
        help="Set the initial page, use arguments: '-s or --start_page'"
    )
    parser.add_argument(
        '-e', '--end_page', type=int, default=701,
        help="Install the last page, use arguments: '-e or --end_page'"
    )
    parser.add_argument(
        '-d', '--dest_folder', action='store_const', const=True,
        help="Set path to the directory with parsing results: '-d or --dest_folder'"
    )
    parser.add_argument(
        '-j', '--json_path', help="Set the path to the json file, use the argument: '-j or --json_path'"
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


def get_link_book(start, end):
    genre = 55
    content = []
    for page in range(start, end+1):
        url = f"https://tululu.org/l{genre}/{page}"
        response_link_book = requests.get(url)
        response_link_book.raise_for_status()
        content.append(BeautifulSoup(response_link_book.text, "lxml"))
    return content


def get_id_book_page(start, end):
    content = get_link_book(start, end)
    pre_links = []
    for line in content:
        first_book = line.select(".d_book")
        pre_links.append([indexes.select_one("a")["href"] for indexes in first_book])
    return pre_links


def get_links_book(start, end):
    indexies_book = get_id_book_page(start, end)
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
            'genres': content_book['genres'],
    }


def main():
    logging.basicConfig(
        level=logging.WARNING,
        filename='logs.log',
        filemode='w',
        format='%(asctime)s - [%(levelname)s] - %(funcName)s() - [line %(lineno)d] - %(message)s',
    )

    count = 1
    json_books = []
    start, end, path_dir, json_path, skip_txt, skip_imgs = get_arguments()
    json_path_file = 'books_content/'
    if path_dir:
        print(os.path.abspath('books_content'))
    if json_path:
        json_path_file = json_path
    links_book = get_links_book(start, end)
    for book_id in links_book:
        payload = {'id': str(*re.findall(r'[0-9]+', str(book_id)))}
        url_title_book = f"https://tululu.org/b{str(*re.findall(r'[0-9]+', str(book_id)))}"
        response_title_book = requests.get(url_title_book)
        try:
            response_title_book.raise_for_status()
            check_for_redirect(response_title_book)
        except HTTPError as exc:
            logging.warning(exc)
        skiptxt = False
        skip_img = False
        try:
            soup = BeautifulSoup(response_title_book.text, "lxml")
            content_book = parse_book_page(soup)
            if skip_txt:
                skiptxt = True
            download_txt(content_book, count, payload, "books_txt", skip=skiptxt)
            if not skip_imgs:
                skip_img = True
            download_image(content_book, payload['id'], "image", skip=skip_img)
            json_books.append(generates_info_books(content_book))
        except HTTPError as exc:
            logging.warning(exc)
        count += 1
    with open(f'{json_path_file}filejson.json', 'w', encoding='utf8') as json_file:
        json.dump(json_books, json_file, ensure_ascii=False, indent=3)


if __name__ == "__main__":
    main()










