from funcsigs import signature


def funcsigs_test():

    def foo(a, b=None, *args, **kwargs):
        pass

    sig = signature(foo)
    ba = sig.bind(5,10, c=3)
    print ba.args


if __name__ == '__main__':
    funcsigs_test()