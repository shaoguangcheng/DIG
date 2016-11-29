"""
Fixtures to get the external bundled dependencies tested.

This module gets loaded by test discovery scanners (such as nose) in
their collection scan.
"""


def path_test():
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))

    print sys.path


def funcsigs_test():
    from funcsigs import *

    def foo(a, b=None, *args, **kwargs):
        pass

    sig = funcsigs.signature(foo)
    ba = sig.bind(5,10, c=3)
    print ba.args


if __name__ == '__main__':
    funcsigs_test()


