import os
import urllib2
import json
import math
import collections
import re
from util import read_json

import config

NG_API = 'http://web-ngram.research.microsoft.com/rest/lookup.svc/bing-body/jun09/3/jp?u=%s&format=%s'

def call_ng_api(phrase):
    format = 'json'
    api_key = config.NG_API_KEYS[0]
    return urllib2.urlopen(urllib2.Request(NG_API % (api_key, format), phrase)).read()

# def ngram(phrase):
#     # load cached ngrams
#     cache_file = open(config.NG_CACHE, 'r+')
#     if os.path.getsize(config.NG_CACHE) == 0:
#         cache = {}
#     else:
#         cache = json.load(cache_file)

#     words = phrase.split('\n')
#     results = {}
#     uncached_words = []
#     for word in words:
#         if word in cache:
#             results[word] = cache[word]
#         else:
#             uncached_words.append(word)

#     # load uncached ngrams from api
#     if len(uncached_words) > 0:
#         uncached_ngram_values = json.loads(call_ng_api('\n'.join(uncached_words)))
#         uncached_ngram = dict(zip(uncached_words, uncached_ngram_values))

#         results.update(uncached_ngram)
#         cache.update(uncached_ngram)

#     # write back to cache file
#     cache_file.seek(0)
#     cache_file.write(json.dumps(cache))
#     cache_file.close()

#     if len(words) == 1:
#         return results[words[0]]
#     else:
#         return results

def construct_cache():
    words = set()
    dictionary = read_json(config.WORD_TRANSLATION_JSON_CORRECTED)
    for word in dictionary:
        for trans in dictionary[word]:
            if ';' in trans[0]:
                words |= set(map(lambda s: s.strip(), trans[0].split(';')))
            else:
                words.add(trans[0].strip())
    phrase = '\n'.join(words)
    print phrase
    print ngram(phrase)

class NGram:
    def __init__(self):
        data = read_json(config.NG_CACHE)
        self.ngram = data['words']
        self.total = data['total']
        self.V = len(self.ngram)

    def get(self, phrase):
        if phrase in self.ngram:
            return self.ngram[phrase]
        else:
            return - math.log(self.total + self.V)

def train(corpus_file):
    # only train unigram for now
    unigram_counts = collections.defaultdict(lambda: 0)
    total = 0

    with open(corpus_file, 'r') as corpus:
        for line in corpus:
            for word in re.findall(r'[a-zA-Z]+', line):
                total += 1
                unigram_counts[word.lower()] += 1

    V = len(unigram_counts)
    ngram = {}
    for word in unigram_counts:
        ngram[word] = math.log(unigram_counts[word] + 1) - math.log(total + V)

    cache_file = open(config.NG_CACHE, 'w')
    cache_file.write(json.dumps({ 'words': ngram, 'total': total }))
    cache_file.close()

if __name__ == '__main__':
    # construct_cache()
    # train('data/corpus/wiki')
    ng = NGram()
    print ng.get('of')
    print ng.get('non-existent-word')
