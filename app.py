import os
from flask import Flask, render_template
import requests
from lxml import html

app = Flask(__name__)
app.debug = True
# app.config.from_object(os.environ['APP_SETTINGS'])

BASE_URL = 'http://dlib.nyu.edu/awdl/isaw/isaw-papers/'
PAPERS_URLS = [f'{BASE_URL}{i}' for i in range(1,14)]

@app.route('/')
def homepage():
    return render_template('index.html')


@app.route('/authors')
def get_authors():

    authors_data = dict()
    authors = []
    for i, url in enumerate(PAPERS_URLS, 1):
        page = requests.get(url)
        html_content = html.fromstring(page.content)
        a1 = html_content.xpath('//span[@rel="dcterms:creator"]//text()')
        a2 = html_content.xpath('//span[contains(@property, "dcterms:creator")]/text()')
        a3 = html_content.xpath('//h2[contains(@property, "dcterms:creator")]/text()')
        a = sorted(list(set(a1+a2+a3)), key=lambda x: x.split()[-1]) # Fix for Bravo III
        authors_data[f'ISAW Papers {i}'] = a
    return render_template('author.html', authors_data=authors_data)


if __name__ == '__main__':
    app.run()