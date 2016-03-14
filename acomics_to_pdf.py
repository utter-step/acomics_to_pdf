# coding: utf-8
import argparse
import sys
import tempfile

import lxml.html
import fpdf
import requests

HOST = 'http://acomics.ru'

BASE_URL_TEMPLATE = '{host}/~{comic}'
PAGE_URL_TEMPLATE = '{base}/{{i}}'.format(base=BASE_URL_TEMPLATE)
IMG_URL_TEMPLATE = '{host}{src}'


def get_page_count(comic_name):
    LAST_PAGE_LINK_XPATH = '//span[@class=\'icon icon-last\']/..'

    start_page = requests.get(BASE_URL_TEMPLATE.format(
        host=HOST,
        comic=comic_name,
    ))
    tree = lxml.html.fromstring(start_page.content)

    last_page_href = tree.xpath(LAST_PAGE_LINK_XPATH)[0].attrib['href']

    return int(last_page_href.split('/')[-1])


def get_img_urls(comic_name, start=None, end=None):
    IMG_XPATH = '//img[@id=\'mainImage\']'

    pages_count = get_page_count(comic_name)

    for i in xrange(start or 1, end or (pages_count + 1)):
        url = PAGE_URL_TEMPLATE.format(
            host=HOST,
            comic=comic_name,
            i=i,
        )
        current_page = requests.get(url)
        tree = lxml.html.fromstring(current_page.content)

        img = tree.xpath(IMG_XPATH)[0]
        src = img.attrib['src']

        yield IMG_URL_TEMPLATE.format(
            host=HOST,
            src=src,
        )

    raise StopIteration


def add_header(pdf, title):
    pdf.set_font('Arial', 'B', 30)

    w = pdf.get_string_width(title) + 6
    pdf.set_y(pdf.h / 2)
    pdf.set_x((210 - w) / 2)

    pdf.cell(w, txt=title)


def create_pdf(comic_name, start=None, end=None):
    pdf = fpdf.FPDF()
    pdf.add_page()

    add_header(pdf, comic_name)

    pdf.set_x(0)

    for i, url in enumerate(get_img_urls(comic_name, start, end), start):
        extension = '.' + url.split('.')[-1]
        file = requests.get(url).content

        with tempfile.NamedTemporaryFile(suffix=extension) as temp:
            temp.write(file)

            try:
                pdf.image(temp.name, w=pdf.w, h=pdf.h)
            except:
                print(i + 1, url)
                break

        sys.stdout.write('{0}\r'.format(i + 1))
        sys.stdout.flush()

    pdf.output('{0}_{1}_{2}.pdf'.format(comic_name, start or 1, end or i), 'F')

if __name__ == '__main__':
    start = None
    end = None

    if len(sys.argv) < 2:
        print('Usage: acomics_to_pdf.py <comics_slug>')
        sys.exit()

    if len(sys.argv) == 3:
        end = int(sys.argv[2])
    elif len(sys.argv) == 4:
        start, end = map(int, sys.argv[2:4])

    create_pdf(sys.argv[1], start, end)
