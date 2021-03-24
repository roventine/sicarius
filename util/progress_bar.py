import sys


def show(percent):
    percent_str = "%.2f%%" % (percent * 100)
    n = round(percent * 50)
    s = ('#' * n).ljust(50, '-')
    f = sys.stdout
    f.write(percent_str.ljust(8, ' ') + '[' + s + ']')
    f.flush()
    f.write('\r')
