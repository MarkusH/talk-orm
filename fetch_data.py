#!/usr/bin/env python

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "talk.settings")
django.setup()

import random
import requests
from pyquery import PyQuery as pq

from literature.models import Author, AuthorBookThrough, Book


BASE_URL = "https://www.lovelybooks.de"
AUTHORS_URL = (
    f"{BASE_URL}/autoren/romane/Die-bedeutendsten-Autoren-aller-Zeiten-464890265/"
)


def fetch(url):
    response = requests.get(url)
    response.raise_for_status()
    return pq(response.content)


def fetch_authors():
    d = fetch(AUTHORS_URL)
    selector = d(".author a[itemprop=url]")
    for item in selector:
        yield (item.attrib["href"], item.getchildren()[0].text)


def fetch_books(url):
    d = fetch(url)
    selector = d(".buchtitel a")
    for item in selector:
        yield item.text


def populate_random_m2m_authors():
    authors = list(Author.objects.all())
    books = Book.objects.select_related("author")
    for book in books:
        bulks = [AuthorBookThrough(author=book.author, book=book)]
        bulks.extend(
            [
                AuthorBookThrough(author=a, book=book)
                for a in random.choices(authors, k=random.randint(0, 4))
                if a.id != book.author_id
            ]
        )
        AuthorBookThrough.objects.bulk_create(bulks)


def main():
    for author_path, author_name in fetch_authors():
        author = Author.objects.create(name=author_name)
        for book_title in fetch_books(BASE_URL + author_path):
            Book.objects.create(author=author, title=book_title)

    populate_random_m2m_authors()


if __name__ == "__main__":
    main()
