# -*- coding: utf-8 -*-
import re
import random
from util import read_json, translate_date

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

def match_pos(word_pos, trans_pos):
    if word_pos[0] == 'n':
        return trans_pos == 'n' or trans_pos == 'gerund'
    elif word_pos == 'v':
        return len(trans_pos) and trans_pos[0] == 'v'

    return word_pos in pos_map and pos_map[word_pos] == trans_pos

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

def translate_word(sentence, idx, dictionary):
    word, pos = sentence[idx]
    if pos == 'x':
        # punctuation
        return punctuation.get(word, word)

    if pos == 'eng':
        return word

    # translate normal word
    translations = dictionary[word]
    # handle multiple equivalence, e.g. 'express; indicate'
    translations = map(
        lambda t: (t[0][:t[0].index(';')], t[1]) if ';' in t[0] else t,
        translations)

    trans, pos = select_translation(sentence, idx, (word, pos), translations)

    return trans


if __name__ == '__main__':
    dev_sentences = get_development_set()
    for sentence in dev_sentences:
        translations = []
        for i in range(len(sentence)):
            w = translate_word(sentence, i, dictionary)
            if w:
                # omit empty translation
                translations.append(w)

        original = ' '.join('%s/%s'%tuple(t) for t in sentence)
        translated = ' '.join(translations)
        print '  Original:', original.encode('utf-8')
        print 'Translated:', translated.encode('utf-8')
        print
