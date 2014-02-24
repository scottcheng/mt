import jieba.posseg
from util import extract_sentences

sentences_file = 'sentences.md'

sentences = extract_sentences(sentences_file)

print 'Read', len(sentences), 'sentences:'
for i, st in enumerate(sentences, 1):
    # use accurate mode (cut_all=False)
    #segmented = '/'.join(jieba.cut(st, cut_all=False))
    segmented = ' '.join(str(p) for p in jieba.posseg.cut(st))
    print i, segmented
