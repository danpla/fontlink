
def ext_to_glob(extension):
    '''Create case-insensetive search pattern from file extension.

    Extension can contain leading dot.

    For example:
        '.otf' => '*.[oO][tT][fF]'
    '''
    if extension.startswith('.'):
        extension = extension[1:]
    return '*.{}'.format(
        ''.join('[{}{}]'.format(c.lower(), c.upper()) for c in extension))


def unique_name(name, all_names):
    '''Make the name unique by appending "#n" at the end.'''

    if name in all_names:
        head, sep, tail = name.rpartition('#')
        if sep:
            try:
                i = int(tail)
                name = head.rstrip()
            except ValueError:
                pass
        else:
            i = 1

        similar_names = set(n for n in all_names if name in n)
        while True:
            new_name = '{} #{}'.format(name, i)
            if new_name not in similar_names:
                name = new_name
                break
            i += 1

    return name
