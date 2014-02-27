import json
import string

def translate_date(day):
    """Return proper date string from day.
    @param day int

    >>> translate_date(1)
    '1st'
    >>> translate_date(2)
    '2nd'
    >>> translate_date(3)
    '3rd'
    >>> translate_date(4)
    '4th'
    >>> translate_date(11)
    '11th'
    >>> translate_date(12)
    '12th'
    >>> translate_date(13)
    '13th'
    >>> translate_date(14)
    '14th'
    >>> translate_date(21)
    '21st'
    >>> translate_date(22)
    '22nd'
    >>> translate_date(23)
    '23rd'
    >>> translate_date(24)
    '24th'
    >>> translate_date(101)
    '101st'
    >>> translate_date(102)
    '102nd'
    >>> translate_date(103)
    '103rd'
    >>> translate_date(104)
    '104th'
    """
    last_digit = day % 10
    suffix = 'th'
    specials = [(1, 'st'), (2, 'nd'), (3, 'rd')]
    for ld, sfx in specials:
        if last_digit == ld and (day == ld or day > 20):
            suffix = sfx
            break

    return '%d%s' % (day, suffix)

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
