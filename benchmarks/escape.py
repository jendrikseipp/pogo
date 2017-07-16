#!/usr/bin/env python

import timeit

data = 'ajsdbajdb&ajsdbaks&asjkdbas&asdks<asdf>dasd<asdnsa>aksdn&aksnd>aasd<aksdn>'
NB_ITERS = 500

# ---


def escape():
    # must do ampersand first
    global data
    data = data.replace("&", "&amp;")
    data = data.replace(">", "&gt;")
    data = data.replace("<", "&lt;")
    return data


# ---

def htmlEscape():
    output = ''
    global data

    for c in data:
        if c == '&':
            output += '&amp;'
        elif c == '<':
            output += '&lt;'
        elif c == '>':
            output += '&gt;'
        else:
            output += c

    return output

# ---


t1 = timeit.Timer('escape()', 'from __main__ import escape')
t2 = timeit.Timer('htmlEscape()', 'from __main__ import htmlEscape')
t3 = timeit.Timer('e(data)', 'from glib import markup_escape_text as e; from __main__ import data')

print
print 'Escaping "%s"' % data
print ' * with saxutils escape() :', t1.timeit(NB_ITERS)
print ' * with custom htmlEscape():', t2.timeit(NB_ITERS)
print ' * with glib.markup_escape_text():', t3.timeit(NB_ITERS)
