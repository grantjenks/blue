# Reference: https://github.com/grantjenks/blue/issues/53


def get_dec_dec():
    def get_dec():
        def dec(func):
            print(func)

        return dec

    return get_dec


@get_dec_dec()()
def foo():
    ...
