# -*- coding: utf-8 -*-
import re
import random
from util import read_json

import config

dictionary = read_json(config.WORD_TRANSLATION_JSON)
segmented_sentences = read_json(config.SENTENCES_JSON)
# random shuffle the sentences in deterministic fashion
random.seed('CS124-MT')
random.shuffle(segmented_sentences)

def get_development_set():
    return segmented_sentences[:10]


# Chinese-to-English punctuation mapping
punctuation = {
    u'，': ',',
    u'。': '.',
}

alphanumeric_pattern = re.compile(r'^\w+$')

def translate_word(sentence, idx, dictionary):
    word, pos = sentence[idx]
    if pos == 'x':
        # punctuation
        return punctuation.get(word, word)

    if word not in dictionary:
        # should contain only alphanumeric characters
        if not alphanumeric_pattern.match(word):
            raise ValueError(u'Should have translation for word %s' % word)
        return word

    # translate normal word
    # for now, just use the first translation
    translations = dictionary[word]
    trans, pos = translations[0]

    # handle multiple equivalence, e.g. 'express; indicate'
    if ';' in trans:
        trans = trans[:trans.index(';')]

    return trans


if __name__ == '__main__':
    dev_sentences = get_development_set()
    for sentence in dev_sentences:
        translations = []
        for i in range(len(sentence)):
            translations.append(translate_word(sentence, i, dictionary))

        original = ' '.join('%s/%s'%tuple(t) for t in sentence)
        translated = ' '.join(translations)
        print '  Original:', original
        print 'Translated:', translated
        print
