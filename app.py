from ner import stanfordNE2BIO, geonames_query, stanfordNE2tree
from places import places_dict
from constants import USERNAME, BASE_URL, PAPERS_URLS
import os
from flask import Flask, render_template, flash
import requests
from lxml import html
import re
from nameparser import HumanName
from tqdm import tqdm #for progress bar
from lxml.etree import tostring
import math

import xml.etree.ElementTree as ET
import json
import requests
import random

from nltk.tag import StanfordNERTagger
from nltk.tokenize import word_tokenize
from nltk.tree import Tree

import folium

from pprint import pprint
from tqdm import tqdm #for progress bar
from flask_cors import CORS
from lxml.etree import tostring


app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = "This key need to be changed and kept secret"

app.debug = True
# app.config.from_object(os.environ['APP_SETTINGS'])



# Helper functions
def _sort_names(names):
    # Should check for 'last' in keys
    parsed_names = [HumanName(name) for name in names]
    return [' '.join(name) for name in sorted(parsed_names, key=lambda x: x['last'])]

def _update_cash() :
    for i, url in enumerate(PAPERS_URLS, 1):
        page = requests.get(url)
        html_content = page.text
        with open("data/papers/isaw-papers-%s.xhtml"%i,"w") as paper:
            paper.write(str(html_content))

# Uncomment inorder to get the newest verion of the articles
# _update_cash()

# Routes
@app.route('/')
def homepage():
    ''' Route to the homepage
    '''
    authors_data = dict()
    for i, url in enumerate(PAPERS_URLS, 1):
        with open("data/papers/isaw-papers-%s.xhtml" % (i), "r") as paper:
            html_content = html.parse(paper)
        a1 = html_content.xpath('//span[@rel="dcterms:creator"]//text()')
        a2 = html_content.xpath('//span[contains(@property, "dcterms:creator")]/text()')
        a3 = html_content.xpath('//h2[contains(@property, "dcterms:creator")]/text()')
        a = _sort_names(list(set(a1+a2+a3)))
        authors_data[str(i)] = a
    return render_template('index.html',  authors_data=authors_data, BASE_URL=BASE_URL)

@app.route('/authors_reversed')
def get_papers():
    '''
     Route to a page listing the papers by authors
    '''
    authors_papers = dict()
    for i, url in enumerate(PAPERS_URLS, 1):
        with open("data/papers/isaw-papers-%s.xhtml" % i, "r") as paper:
            html_content = html.parse(paper)
        authors = html_content.xpath('//span[@rel="dcterms:creator"]//text()')
        authors += html_content.xpath('//span[contains(@property, "dcterms:creator")]/text()')
        authors += html_content.xpath('//h2[contains(@property, "dcterms:creator")]/text()')
        authors = list(set(_sort_names(authors)))
        for author in authors :
            try :
                authors_papers[author]["articles"].append(str(i))
            except KeyError :
                try :
                    authors_papers[author]["article"] = list()
                except KeyError :
                    authors_papers[author] = dict()
                    authors_papers[author]["articles"] = list()
                authors_papers[author]["articles"].append(str(i))
            authors_papers[author]["viaf"] = html_content.xpath('//span[@rel="dcterms:creator"]/a[.="%s"]/@href'%author)
    return render_template('author_reversed.html', authors_papers=authors_papers, BASE_URL=BASE_URL)


@app.route('/places')
def get_places():
    '''
    Route to a page listing the places mentionned in the papers
    '''
    places_data = dict()
    for i, url in enumerate(PAPERS_URLS, 1):
        with open("data/papers/isaw-papers-%s.xhtml" % (i), "r") as paper:
            html_content = html.parse(paper)
        place_name = html_content.xpath('//a[starts-with(@href,"https://pleiades.stoa.org/place")]/text()')
        place_pleiades = html_content.xpath('//a[starts-with(@href,"https://pleiades.stoa.org/place")]/@href')
        places = list()
        for j in range(len(place_name)):
            data = requests.get(place_pleiades[j] + "/json")
            try :
                coordinates = data.json()['features'][0]['geometry']['coordinates']
            except :
                coordinates = []
            places += [place_name[j] + ": " + place_pleiades[j] + " (" + str(coordinates) + ")"]
            places = list(set(places))
            places.sort()
        if places:
            places_data[f'ISAW Papers {i}'] = places
    return render_template('places.html', places_data=places_data)



@app.route('/map/<article_id>')
@app.route('/<article_id>/map')
@app.route('/map')
def map_places(**kwargs):
    '''
    Route to a pages with a map of all the places mentionned in the articles (one of the paper if the number is give as an argument)
    '''
    if kwargs :
        with open("data/papers/isaw-papers-%s.xhtml" % (kwargs["article_id"]), "r") as paper:
            html_contents = [html.parse(paper)]
        i = kwargs["article_id"]

        places = places_dict(html_contents, i)
        article = "ISAW Papers " + str(i)
    else :
        article = "ISAW Papers"
        places = dict()
        for i, url in enumerate(PAPERS_URLS, 1):
            with open("data/papers/isaw-papers-%s.xhtml" % (i), "r") as paper:
                html_contents = [html.parse(paper)]
            places_article = places_dict(html_contents, i)
            for k,v in places_article.items() :
                if k in places :
                    for p in places_article[k][2] :
                        places[k][2].append(p)
                        if str(i) not in places[k][3] :
                            places[k][3].append(str(i))
                    places[k][3] = ' and '.join(places[k][3])
                else :
                    places[k] = v
    for k, v in places.items():
        # size of the circle on the map (places[k][5])
        radius = math.log10(len(places[k][2]) + 1) * 150000
        places[k].append(radius)
        if type(places[k][3]) is list:
            places[k][3] = ''.join(places[k][3])

    if not places :
        flash("We do not have any places associated with that article", "warning")
    return render_template('map.html', places=places, article=article)

st = StanfordNERTagger('./stanford-ner/classifiers/english.all.3class.distsim.crf.ser.gz',
                       './stanford-ner/stanford-ner.jar',

                       encoding='utf-8')






@app.route('/ner')
def ner():
    st = StanfordNERTagger('./stanford-ner/classifiers/english.all.3class.distsim.crf.ser.gz',
                           './stanford-ner/stanford-ner.jar',

                           encoding='utf-8')

    with open("data/papers/isaw-papers-%s.xhtml" % (1), "r") as paper:
        html_parsed = html.parse(paper)
        work_cited = html_parsed.xpath('//p[@class="work_cited"]')
        html_parsed = [html_parsed]


    places_set = []
    for html_c in tqdm(html_parsed):
        html_c = tostring(html_c, encoding="unicode")
        for work in work_cited :
            work = tostring(work, encoding="unicode")
            html_c = html_c.replace(work, "")

        tokenized_marc = word_tokenize(html_c)
        classified_marc = st.tag(tokenized_marc)
        classified_marc = [item for item in classified_marc if item[0] != '']  # clean up parsing
        ne_tree = stanfordNE2tree(classified_marc)

        ne_in_sent = []
        for subtree in ne_tree:
            if type(subtree) == Tree:  # If subtree is a noun chunk, i.e. NE != "O"
                ne_label = subtree.label()
                ne_string = " ".join([token for token, pos in subtree.leaves()])
                ne_in_sent.append((ne_string, ne_label))

        locations = set([tag[0] for tag in ne_in_sent if
                         tag[1] == 'LOCATION'])  # If we don't make this a set, we can use frequency info for map weight

        places_set.append(locations)

    places_set = [sorted(item) for item in places_set]

    # Build list of likely coordinates for places

    places_list = []
    map = dict()

    for places in places_set:
        for place in places:
            ll = geonames_query(place)
            if ll != ():
                places_list.append(place)
                ll = list(ll)
                map[place] = list()
                for l in ll :
                    map[place].append((float(l)))
    print(len(map))

    return render_template('map_ner.html', places=map)


@app.route('/tfidf')
def tfidf() :
    """ Route displaying the 10 words of each articles with the highest tf-idf score
    	"""
    number_doc_containing = {}

    tf_idf = {}
    wordcount = {}
    total_word = {}
    for i, url in enumerate(PAPERS_URLS, 1):
        with open("data/papers/isaw-papers-%s.xhtml" % (i), "r") as paper:
            html_page = html.parse(paper)

            # deleting the bibliography
            work_cited = html_page.xpath('//p[@class="work_cited"]')
            for work in work_cited :
                work.getparent().remove(work)
            text_page = html_page.xpath("//body//text()")

        total_word[str(i)] = 0
        wordcount [str(i)] = {}
        tf_idf[str(i)] = {}

        # To eliminate duplicates, remember to split by punctuation
        for words in text_page :
            for word in words.lower().split():
                word = word.replace(".", "")
                word = word.replace(",", "")
                word = word.replace(":", "")
                word = word.replace("\"", "")
                word = word.replace("!", "")
                word = word.replace(";", "")
                word = word.replace("(", "")
                word = word.replace(")", "")
                word = word.replace("|", "")
                word = word.replace("â€œ", "")
                word = word.replace("â€˜", "")
                word = word.replace("*", "")

                # counting the occurrences of the words in each document and the number of doc where each word appears
                if word not in wordcount[str(i)]:
                    wordcount[str(i)][word] = 1
                    if word in number_doc_containing.keys() :
                        number_doc_containing[word] += 1
                    else :
                        number_doc_containing[word] = 1

                else:
                    wordcount[str(i)][word] += 1
            total_word[str(i)] += 1

    # calculating df and idf scores
    for i, url in enumerate(PAPERS_URLS, 1):
        for  word, number in wordcount[str(i)].items() :
            tf = wordcount[str(i)][word]/total_word[str(i)]

            tf_idf[str(i)][word] =  tf * math.log(i/number_doc_containing[word])
        # ordonning the dictionnary
        tf_idf[str(i)] = sorted(tf_idf[str(i)].items(), key=lambda x: x[1])

        # Taking the ten last values (best if-idf score
        tf_idf[str(i)] = tf_idf[str(i)][-10:]
    print(type(tf_idf["11"]))
    return render_template('tfidf.html', tf_idf = tf_idf)

if __name__ == '__main__':
    app.run()
