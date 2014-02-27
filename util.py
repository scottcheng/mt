import json
import string

def translate_date(day):
    value = int(day) % 100
    if day[-1] == '1' and (value == 1 or value > 20):
        return day + 'st'
    elif day[-1] == '2' and (value == 2 or value > 20):
        return day + 'nd'
    elif day[-1] == '3' and (value == 3 or value > 20):
        return day + 'rd'
    else:
        return day + 'th'

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
        content = in_file.read()
        try:
            return json.loads(content)
        except:
            # patch errorneous json returned by wordreference.com JSON API
            return json.loads(content + '}')

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print 'python %s <sentence_file>' % sys.argv[0]
        sys.exit(-1)

    sts = extract_sentences(sys.argv[1])
    print 'read', len(sts), 'sentences:'
    for i, st in enumerate(sts, 1):
        print i, st
