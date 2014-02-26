# -*- coding: utf-8 -*-
import re
import random
from util import read_json

from ngram import NGram
import config

# use manually corrected dataset
dictionary = read_json(config.WORD_TRANSLATION_JSON_CORRECTED)
segmented_sentences = read_json(config.SENTENCES_JSON_CORRECTED)
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

def match_pos(word_pos, trans_pos):
    if word_pos[0] == 'n':
        return trans_pos == 'n' or trans_pos == 'gerund'
    elif word_pos == 'v':
        return len(trans_pos) and trans_pos[0] == 'v'

    pos_map = {
        'a': 'adj',
        'ad': 'adv',
        'd': 'adv',
        'u': 'v aux',
        'r': 'pron',
        'p': 'prep',
        'prep': 'prep',
        'c': 'conj',
        't': 'n',
        'm': 'n'
    }
    return word_pos in pos_map and pos_map[word_pos] == trans_pos

def select_translate(sentence, idx, word, translations):
    # construct a list of translations with the same pos as word
    same_pos_translations = filter(lambda t: match_pos(word[1], t[1]), translations)
    ng = NGram()

    if len(same_pos_translations) > 0:
        max_unigram_trans = max(same_pos_translations, key=lambda t: ng.get(t[0]))
        return max_unigram_trans

    return translations[0]

def translate_word(sentence, idx, dictionary):
    word, pos = sentence[idx]
    if pos == 'x':
        # punctuation
        return punctuation.get(word, word)

    if pos == 'eng':
        return word

    # translate normal word
    translations = dictionary[word]
    trans, pos = select_translate(sentence, idx, (word, pos), translations)

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
