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

word_forms = {
    'go': {
        'past': 'went'
    },
    'leave': {
        'past': 'left'
    },
    'be': {
        'tps': 'is',
        'ptps': 'was'
    }
}
vows = ['a', 'e', 'i', 'o', 'u']

def transform_word(word, form):
    """transform a word to a different form.
    @param form string 'past'
                       'pp' (past participle)
                       'tps' (third-person singular)
                       'ptps' (past third-person singular)
    """

    if word in word_forms and form in word_forms[word]:
        return word_forms[word][form]

    if form == 'past' or form == 'pp':
        # fallback transformation for past tense
        if word[-1] == 'e':
            return word + 'd'
        elif len(word) >= 2 and word[-2] in vows and word[-1] not in vows:
            return word + word[-1] + 'ed'
        else:
            return word + 'ed'

    return word

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print 'python %s <sentence_file>' % sys.argv[0]
        sys.exit(-1)

    sts = extract_sentences(sys.argv[1])
    print 'read', len(sts), 'sentences:'
    for i, st in enumerate(sts, 1):
        print i, st
