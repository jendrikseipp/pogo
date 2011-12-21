import sys

sys.path.insert(0, '../')

def main():
    import pogo
    pogo.main()

import cProfile
import pstats
cProfile.run('main()', 'Profile.prof')
s = pstats.Stats("Profile.prof")
# time or cumulative
#s.sort_stats("cumulative").print_stats(r'.*Pogo.*py:\d+(?!\(\<module\>\))')
#s.sort_stats("cumulative").print_stats(r'.*Pogo.*py')
s.sort_stats("cumulative").print_stats()
#s.strip_dirs().sort_stats("time").print_stats()
