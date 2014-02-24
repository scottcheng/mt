import json
import string

def extract_sentences(f):
    """Read sentences from file f."""
    sentences = []
    with open(f) as infile:
        for line in infile:
            # the sentence line starts with a digit
            if line[0] in string.digits:
                # strip the number
                sentences.append(line[line.index(' ')+1:].strip())

    return sentences

def read_json(json_file):
    with open(json_file, 'rb') as in_file:
        return json.load(in_file)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print 'python %s <sentence_file>' % sys.argv[0]
        sys.exit(-1)

    sts = extract_sentences(sys.argv[1])
    print 'read', len(sts), 'sentences:'
    for i, st in enumerate(sts, 1):
        print i, st
