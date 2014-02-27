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

def get_test_set():
    return segmented_sentences[10:]

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

def find_clause(sentence, idx):
    """find the clause that the word at idx belongs to"""
    start = 0
    end = len(sentence)
    for i, word in enumerate(sentence):
        if word[1] == 'x':
            if i > idx:
                end = i
                break
            else:
                start = i + 1
    return (sentence[start:end], start)

def translate_word(sentence, idx, dictionary, translated):
    clause, clause_start = find_clause(sentence, idx)

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

    if pos_zh == 'v':
        # 被 <v> -> be <v>.pp
        # 被 <n> <v> -> be <v>.pp by <n>
        if idx > 0 and sentence[idx - 1][0] == u'被' and sentence[idx - 1][1] == 'p' or \
           idx > 1 and sentence[idx - 2][0] == u'被' and sentence[idx - 2][1] == 'p' and sentence[idx - 1][1] == 'n':
            be = 'is' # default to 'is'
            if u'我' in clause[:idx - clause_start]:
                be = 'am'
            elif u'你' in clause[:idx - clause_start] or u'们' in clause[:idx - clause_start]:
                be = 'are'
            trans = transform_word(trans, 'pp')
            if sentence[idx - 1][1] == 'n':
                translated[idx - 2] = ''
                # swap <n> and <v>
                noun = translated[idx - 1]
                translated[idx - 1] = '%s %s by' % (be, trans)
                trans = noun
            else:
                translated[idx - 1] = ''
                trans = '%s %s' % (be, trans)
        # <v> <ul>|<ug> -> past tense
        elif idx < len(sentence) - 1 and sentence[idx + 1][1] in ['ul', 'ug']:
            trans = transform_word(trans, 'past')
        # <v> <u> <ul> -> past tense
        elif idx < len(sentence) - 2 and sentence[idx + 1][1] == 'u' and sentence[idx + 2][1] == 'ul':
            trans = transform_word(trans, 'past')
        # <tps> <adv>? <v> -> third-person singular form of <v>
        elif idx > 0 and sentence[idx - 1][0] in [u'他', u'她', u'它'] or \
             idx > 1 and sentence[idx - 2][0] in [u'他', u'她', u'它'] and sentence[idx - 1][1] in ['ad', 'd']:
            trans = transform_word(trans, 'tps')

    # remove <ul>, <ug> in <v> <u>? <ul>|<ug>
    if pos_zh in ['ul', 'ug']:
        if idx > 0 and sentence[idx - 1][1] == 'v' or \
           idx > 1 and sentence[idx - 2][1] == 'v' and sentence[idx - 1][1] == 'u':
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

    #10. remove <adj> 的 <n>
    if idx > 0 and word == u'的' and pos_zh == 'uj' and sentence[idx - 1][1] == 'a':
        return ''        

    #11. <n1> 的 <n2> -> <n1>’s <n2>
    if idx > 0 and word == u'的' and pos_zh == 'uj' and sentence[idx - 1][1][0] == 'n':
        return "'s" 

    #12. 我/r 的/uj -> my
    if idx > 0 and word == u'我' and sentence[idx + 1][0] == u'的':
        del sentence[idx + 1]
        return "my"   

    #   你/r 的/uj -> my
    if idx > 0 and word == u'你' and sentence[idx + 1][0] == u'的':
        del sentence[idx + 1]
        return "your" 

    #   他/r 的/uj -> my
    if idx > 0 and word == u'他' and sentence[idx + 1][0] == u'的':
        del sentence[idx + 1]
        return "his" 

    #   她/r 的/uj -> my
    if idx > 0 and word == u'她' and sentence[idx + 1][0] == u'的':
        del sentence[idx + 1]
        return "her"   

    #13. 还/d 会/v ->还会
    if idx > 0 and word == u'还' and sentence[idx + 1][0] == u'会':
        del sentence[idx + 1]
        return "also"  

    return trans


if __name__ == '__main__':
    # dev_sentences = get_development_set()
    # for sentence in dev_sentences:
    #     # since we remove '的' from the original sentence, keep a copy of original sentence
    #     sentence_cp = sentence[:]
    #     translations = []
    #     i = 0
    #     while i< len(sentence_cp):
    #         w = translate_word(sentence_cp, i, dictionary, translations)
    #         translations.append(w)
    #         i+=1

    #     original = ' '.join('%s/%s'%tuple(t) for t in sentence)
    #     # omit empty translation
    #     translated = ' '.join(filter(lambda t: t, translations))
    #     print '  Original:', original.encode('utf-8')
    #     print 'Translated:', translated.encode('utf-8')
    #     print

    test_sentences = get_test_set()
    for sentence in test_sentences:
        # since we remove '的' from the original sentence, keep a copy of original sentence
        sentence_cp = sentence[:]
        translations = []
        i = 0
        while i< len(sentence_cp):
            w = translate_word(sentence_cp, i, dictionary, translations)
            translations.append(w)
            i+=1

        original = ' '.join('%s/%s'%tuple(t) for t in sentence)
        # omit empty translation
        translated = ' '.join(filter(lambda t: t, translations))
        print '  Original:', original.encode('utf-8')
        print 'Translated:', translated.encode('utf-8')
        print
