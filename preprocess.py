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

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print 'python %s <sentence_file>' % sys.argv[0]
        sys.exit(-1)

    if not os.path.exists(config.SENTENCES_JSON):
        # segmente sentences and store results to file
        segment_sentence(sys.argv[1], config.SENTENCES_JSON)

    if not os.path.exists(config.TRANSLATION_DIR) or len(os.listdir(config.TRANSLATION_DIR)) == 0:
        sentences = read_json(config.SENTENCES_JSON)
        # use wordreference.com API to cache translations
        grab_word_translations(sentences, config.WR_API_KEYS, config.TRANSLATION_DIR)
