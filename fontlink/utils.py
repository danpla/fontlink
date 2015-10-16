
def string_to_glob(string):
    '''Create case-insensetive search pattern from the string.

    For example:
        '.otf' => '.[oO][tT][fF]'
    '''
    return ''.join(
        '[{}{}]'.format(c.lower(), c.upper()) if c.isalpha() else c
        for c in string)


def unique_name(name, all_names):
    '''Make the name unique by appending "#n" at the end.'''

    if not isinstance(all_names, set):
        all_names = set(all_names)

    if name not in all_names:
        return name

    i = 1
    head, sep, tail = name.rpartition('#')
    if sep:
        try:
            i = int(tail)
        except ValueError:
            pass
        else:
            name = head.rstrip()

    while True:
        new_name = '{} #{}'.format(name, i)
        if new_name in all_names:
            i += 1
        else:
            return new_name
