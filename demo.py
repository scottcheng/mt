import jieba
from util import read_sentences

sentences_file = 'sentences.md'

sentences = read_sentences(sentences_file)

print 'Read', len(sentences), 'sentences:'
for i, st in enumerate(sentences, 1):
    # use accurate mode (cut_all=False)
    segmented = '/'.join(jieba.cut(st, cut_all=False))
    print i, segmented
