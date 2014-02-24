import os
import json
import time
import pickle
import requests
from util import extract_sentences, read_json

import config

def segment_sentence(sentences_file, out_file):
    # load on demand to reduce file loading time
    import jieba.posseg

    sentences = extract_sentences(sentences_file)

    segmented_sentences = []
    for i, st in enumerate(sentences, 1):
        print 'Processing', i, st
        # get segmented word with POS
        seg_st = [(p.word, p.flag) for p in jieba.posseg.cut(st)]
        print '      ===>', ' '.join('%s/%s' % t for t in seg_st)

        segmented_sentences.append(seg_st)

    # persist as json
    with open(out_file, 'wb') as out:
        dumped = json.dumps(segmented_sentences, ensure_ascii=False, indent=4)
        out.write(dumped.encode('utf-8'))


WR_API_ENDPOINT = 'http://api.wordreference.com/%s/json/zhen/%s'
def grab_word_translations(sentences, wr_api_keys, cache_dir):
    # try one sentence first
    word_set = set()
    i, N = 0, len(wr_api_keys)
    for idx, sentence in enumerate(sentences, 1):
        print 'Processing sentence', idx

        for w, pos in sentence:
            # do not process punctuations
            if pos == 'x' or w in word_set:
                continue

            print 'Grabbing translation for', w
            word_set.add(w)
            api_key = wr_api_keys[i]
            i = (i+1) % N # round robin
            endpoint = WR_API_ENDPOINT % (api_key, w.encode('utf-8'))
            res = requests.get(endpoint)
            if res.status_code != 200:
                print 'Unexpected response code:', res.status_code, 'aborting...'
                with open(config.GRABBDED_WORDS, 'wb') as out:
                    pickle.dump(word_set, out)
                return

            with open(os.path.join(cache_dir, w.encode('utf-8')), 'wb') as out:
                out.write(res.text.encode('utf-8'))

            # sleep a bit
            time.sleep(0.5)

def read_entries(entry_struct, side_entry=False):
    entries = []
    i = 0
    key = 'OriginalTerm' if side_entry else 'FirstTranslation'
    while str(i) in entry_struct:
        entry = entry_struct[str(i)]
        for term in entry[key]['term'].split(', '):
            # can have multiple terms
            entries.append((term, entry[key]['POS']))
        i += 1

    return entries


def generate_word_translations(trans_dir, word_trans_json):
    # save pwd
    pwd = os.getcwd()

    os.chdir(trans_dir)
    translations = {}
    for word in os.listdir('.'):
        data = read_json(word)

        candidates = []
        if 'Error' in data:
            print 'No translation for', word
        else:
            term = data['term0']
            if 'Entries' in term:
                candidates.extend(read_entries(term['Entries']))
            if 'OtherSideEntries' in term:
                candidates.extend(read_entries(term['OtherSideEntries'], side_entry=True))

            # print 'Translations for', word, candidates

        # ensure unicode
        translations[word.decode('utf-8')] = candidates

    # back to original directory
    os.chdir(pwd)

    with open(word_trans_json, 'wb') as out:
        content = json.dumps(translations, ensure_ascii=False, indent=4)
        out.write(content.encode('utf-8'))


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print 'python %s <sentence_file>' % sys.argv[0]
        sys.exit(-1)

    something_missing = False
    if not os.path.exists(config.SENTENCES_JSON):
        print config.SENTENCES_JSON, 'not found, segmenting sentences...'
        something_missing = True
        # segmente sentences and store results to file
        segment_sentence(sys.argv[1], config.SENTENCES_JSON)

    if not os.path.exists(config.TRANSLATION_DIR) or len(os.listdir(config.TRANSLATION_DIR)) == 0:
        print config.TRANSLATION_DIR, 'is empty, gather translations from wordreferences.com...'
        something_missing = True
        sentences = read_json(config.SENTENCES_JSON)
        # use wordreference.com API to cache translations
        grab_word_translations(sentences, config.WR_API_KEYS, config.TRANSLATION_DIR)

    if not os.path.exists(config.WORD_TRANSLATION_JSON):
        print config.WORD_TRANSLATION_JSON, 'not found, generating it...'
        something_missing = True
        generate_word_translations(config.TRANSLATION_DIR, config.WORD_TRANSLATION_JSON)

    if not something_missing:
        print 'All set. No processing is needed.'
