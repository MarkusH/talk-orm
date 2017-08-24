#!/usr/bin/env python

import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "talk.settings")
django.setup()

import requests
from pyquery import PyQuery as pq

from literature.models import Author


BASE_URL = 'https://www.lovelybooks.de'
AUTHORS_URL = BASE_URL + '/autoren/romane/Die-bedeutendsten-Autoren-aller-Zeiten-464890265/'


def fetch(url):
    response = requests.get(url)
    response.raise_for_status()
    return pq(response.content)


def fetch_authors():
    d = fetch(AUTHORS_URL)
    selector = d('.author a[itemprop=url]')
    for item in selector:
        yield (item.attrib['href'], item.getchildren()[0].text)


def main():
    for author_path, author_name in fetch_authors():
        author = Author.objects.create(name=author_name)


if __name__ == "__main__":
    main()
