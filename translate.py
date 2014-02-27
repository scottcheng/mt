# -*- coding: utf-8 -*-
import re
import random
from util import read_json, translate_date, transform_word

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

def match_pos(pos_zh, pos_en):
    if pos_zh[0] == 'n':
        return pos_en == 'n' or pos_en == 'gerund'
    elif pos_zh == 'v':
        return len(pos_en) and pos_en[0] == 'v'

    return pos_zh in pos_map and pos_map[pos_zh] == pos_en

subject_pronoun = {
    u'我': 'I',
    u'我们': 'we',
    u'她': 'she',
    u'她们': 'they',
    u'他': 'he',
    u'他们': 'they',
    u'它们': 'they',
    # it/you don't matter
}

DIGITS_PATTERN = re.compile(r'^\d+$')

def select_translation(sentence, idx, word, translations):
    # make sure the subject pronoun is in subject form
    # heuristic: if it's the first word or the previous word is punctuation
    # or conjunction, it's considered a subject
    if word[1] == 'r' and word[0] in subject_pronoun:
        if idx == 0 or sentence[idx-1][1] in ['x', 'c']:
            return (subject_pronoun[word[0]], 'pron')

    # handle special case: <digits>/m 日/m
    if word[1] == 'm':
        if DIGITS_PATTERN.match(word[0]):
            if idx+1 < len(sentence) and sentence[idx+1][0] == u'日':
                # return proper date string
                return (translate_date(int(word[0])), 'n')
            else:
                # return digits directly
                return (word[0], 'n')
        elif word[0] == u'日':
            # symmetric case
            if idx > 0 and DIGITS_PATTERN.match(sentence[i-1][0]):
                return ('', '')

    # construct a list of translations with the same pos as word
    same_pos_translations = filter(lambda t: match_pos(word[1], t[1]), translations)

    ng = NGram()

    if len(same_pos_translations) > 0:
        max_unigram_trans = max(same_pos_translations, key=lambda t: ng.get(t[0]))
        return max_unigram_trans

    return translations[0]

def translate_word(sentence, idx, dictionary, translated):
    word, pos_zh = sentence[idx]
    if pos_zh == 'x':
        # punctuation
        return punctuation.get(word, word)

    if pos_zh == 'eng':
        return word

    # remove '到' after verbs
    if idx > 0 and word == u'到' and pos_zh in ['u', 'p'] and sentence[idx - 1][1] == 'v':
        return ''

    # translate normal word
    translations = dictionary[word]
    # handle multiple equivalence, e.g. 'express; indicate'
    translations = map(
        lambda t: (t[0][:t[0].index(';')], t[1]) if ';' in t[0] else t,
        translations)

    trans, pos_en = select_translation(sentence, idx, (word, pos_zh), translations)

    # <v> <u>? <ul>|<ug> -> <v>'ed
    if pos_zh in ['ul', 'ug']:
        if idx > 0 and sentence[idx - 1][1] == 'v':
            translated[idx - 1] = transform_word(translated[idx - 1], 'past')
            trans = ''
        elif idx > 1 and sentence[idx - 2][1] == 'v' and sentence[idx - 1][1] == 'u':
            translated[idx - 2] = transform_word(translated[idx - 2], 'past')
            trans = ''

    # remove <uz> in <v> <uz>
    # (although <uz> sometimes implies the state of doing something)
    if pos_zh == 'uz':
        if idx > 0 and sentence[idx - 1][1] == 'v':
            trans = ''

    # remove <uv> in <ad>|<d> <uv>
    if pos_zh == 'uv':
        if idx > 0 and sentence[idx - 1][1] in ['ad', 'd']:
            trans = ''

    return trans


if __name__ == '__main__':
    dev_sentences = get_development_set()
    for sentence in dev_sentences:
        translations = []
        for i in range(len(sentence)):
            w = translate_word(sentence, i, dictionary, translations)
            if w:
                # omit empty translation
                translations.append(w)

        original = ' '.join('%s/%s'%tuple(t) for t in sentence)
        translated = ' '.join(translations)
        print '  Original:', original.encode('utf-8')
        print 'Translated:', translated.encode('utf-8')
        print
