#!/usr/bin/env python

import os
import random
import time

import django
import requests
from pyquery import PyQuery as pq

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "talk.settings")
django.setup()

from literature.models import Author, Book, Genre

BASE_URL = "https://www.goodreads.com"
URLS = (
    "/choiceawards/best-fiction-books-2018",
    "/choiceawards/best-mystery-thriller-books-2018",
    "/choiceawards/best-historical-fiction-books-2018",
    "/choiceawards/best-fantasy-books-2018",
    "/choiceawards/best-of-the-best-2018",
    "/choiceawards/best-romance-books-2018",
    "/choiceawards/best-science-fiction-books-2018",
    "/choiceawards/best-horror-books-2018",
    "/choiceawards/best-humor-books-2018",
    "/choiceawards/best-nonfiction-books-2018",
    "/choiceawards/best-memoir-autobiography-books-2018",
    "/choiceawards/best-history-biography-books-2018",
    "/choiceawards/best-science-technology-books-2018",
    "/choiceawards/best-food-cookbooks-2018",
    "/choiceawards/best-graphic-novels-comics-2018",
    "/choiceawards/best-poetry-books-2018",
    "/choiceawards/best-debut-author-2018",
    "/choiceawards/best-young-adult-fiction-books-2018",
    "/choiceawards/best-childrens-books-2018",
    "/choiceawards/best-picture-books-2018",
)


def fetch(url: str, *, relative=True) -> pq:
    if relative:
        url = BASE_URL + url
    while True:
        try:
            response = requests.get(url)
            response.raise_for_status()
            return pq(response.content)
        except:
            time.sleep(10)
            print("* Retrying")


def id_from_path(path):
    path = path.rsplit("/", 1)[-1]
    path = path.split("-", 1)[0]
    path = path.split(".", 1)[0]
    assert str.isdigit(path)
    return int(path)


def fetch_author_books(author_id: int, page: pq):
    selector = page(".bookTitle")
    for link in selector:
        href = link.attrib["href"]
        if not href.startswith("/book/show/"):
            continue
        print(f"      > Fetching book {href}")
        book_page = fetch(href)
        id = id_from_path(href)
        fetch_book(id, book_page)


def fetch_book(book_id: int, page: pq, *, follow_author=False):
    if Book.objects.filter(id=book_id).exists():
        return
    title = page("#bookTitle")[0].text_content().strip()
    votes = int(page("[itemprop=ratingCount]")[0].attrib["content"])
    author_dom = page("a.authorName")[0]
    author_id = id_from_path(author_dom.attrib["href"])
    author_name = author_dom.text_content().strip()
    author, _ = Author.objects.get_or_create(
        id=author_id, defaults={"name": author_name}
    )
    genres = [
        Genre.objects.get_or_create(name=link.text_content().strip())[0]
        for link in page(".left .bookPageGenreLink")
    ]
    book = Book.objects.create(id=book_id, title=title, author=author, votes=votes)
    book.genres.set(genres)
    if follow_author:
        href = author_dom.attrib["href"]
        print(f"    > Fetching author {href}")
        author_page = fetch(href, relative=False)
        fetch_author_books(author_id, author_page)


def fetch_books(page: pq):
    selector = page(".pollAnswer__bookLink")
    for link in selector:
        href = link.attrib["href"]
        print(f"  > Fetching book {href}")
        book_page = fetch(href)
        book_id = id_from_path(href)
        fetch_book(book_id, book_page, follow_author=True)


def main():
    for url in URLS:
        print(f"> Fetching book list {url}")
        page = fetch(url)
        fetch_books(page)


if __name__ == "__main__":
    main()
