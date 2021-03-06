'''
Created on Feb 14, 2012

@organization: cert.org
'''

import unittest
import os
import shutil
from certfuzz.fuzzers.bytemut import fuzz, _fuzzable
from certfuzz.fuzzers.bytemut import ByteMutFuzzer
from test_certfuzz.mocks import MockSeedfile, MockRange
import tempfile
from certfuzz.fuzztools.hamming import bytewise_hd

_input = lambda x: bytearray('A' * x)


class Test(unittest.TestCase):

    def setUp(self):
        self.sf = seedfile_obj = MockSeedfile()
        self.tempdir = tempfile.mkdtemp()
        self.outdir = outdir_base = tempfile.mkdtemp(prefix='outdir_base',
                                                     dir=self.tempdir)
        iteration = 0
        self.options = {'min_ratio': 0.1, 'max_ratio': 0.2}
        self.args = (seedfile_obj, outdir_base, iteration, self.options)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def _fail_if_not_fuzzed(self, fuzzed):
        for c in fuzzed:
            if c != 'A':
                # Skip over the else: clause
                break
        else:
            self.fail('Input not fuzzed')


    def _test_fuzz(self, inputlen=1000, iterations=100, rangelist=None):
        for i in xrange(iterations):
            fuzzed = fuzz(fuzz_input=_input(inputlen),
                                seed_val=0,
                                jump_idx=i,
                                ratio_min=0.1,
                                ratio_max=0.3,
                                range_list=rangelist,
                              )
            self.assertEqual(inputlen, len(fuzzed))
            self._fail_if_not_fuzzed(fuzzed)

            hd = bytewise_hd(_input(inputlen), fuzzed)

            self.assertGreater(hd, 0)
            self.assertLess(hd, inputlen)

            actual_ratio = hd / float(inputlen)
            self.assertGreaterEqual(actual_ratio, 0.1)
            self.assertLessEqual(actual_ratio, 0.3)

    def test_fuzz(self):
        self._test_fuzz()

    def test_fuzz_longinput(self):
        '''
        Test fuzz method with abnormally long input to find memory bugs
        '''
        self._test_fuzz(inputlen=10000000, iterations=2)


    def test_fuzzable(self):
        r = [(0, 100), (600, 1000), (3000, 10000)]
        for x in xrange(10000):
            if 0 <= x <= 100:
                self.assertFalse(_fuzzable(x, r), 'x=%d' % x)
            elif 600 <= x <= 1000:
                self.assertFalse(_fuzzable(x, r), 'x=%d' % x)
            elif 3000 <= x <= 10000:
                self.assertFalse(_fuzzable(x, r), 'x=%d' % x)
            else:
                self.assertTrue(_fuzzable(x, r), 'x=%d' % x)

    def test_fuzz_rangelist(self):
        inputlen = 10000
        iterations = 100
        r = [(0, 100), (600, 1000), (3000, 10000)]
        for i in xrange(iterations):
            fuzzed = fuzz(fuzz_input=_input(inputlen),
                                seed_val=0,
                                jump_idx=i,
                                ratio_min=0.1,
                                ratio_max=0.3,
                                range_list=r,
                              )
            self.assertEqual(inputlen, len(fuzzed))
            self._fail_if_not_fuzzed(fuzzed)

            for (a, b) in r:
                # make sure we didn't change the exclude ranges
                self.assertEqual(_input(inputlen)[a:b + 1], fuzzed[a:b + 1])

            hd = bytewise_hd(_input(inputlen), fuzzed)

            self.assertGreater(hd, 0)
            self.assertLess(hd, inputlen)

            # we excluded all but 2500 bytes in r above
            actual_ratio = hd / 2500.0
            self.assertGreaterEqual(actual_ratio, 0.1)
            self.assertLessEqual(actual_ratio, 0.3)

    def test_bytemutfuzzer_fuzz(self):
        self.assertTrue(self.sf.len > 0)
        for i in xrange(100):
            with ByteMutFuzzer(*self.args) as f:
                f.iteration = i
                f._fuzz()
                # same length, different output
                self.assertEqual(self.sf.len, len(f.output))
                self._fail_if_not_fuzzed(f.output)
                # confirm ratio
#                 self.assertGreaterEqual(f.fuzzed_byte_ratio(), MockRange().min)
#                 self.assertLessEqual(f.fuzzed_byte_ratio(), MockRange().max)


    def test_consistency(self):
        # ensure that we get the same result 20 times in a row
        # for 50 different iterations
        last_result = None
        last_x = None
        for x in range(50):
            if x != last_x:
                last_result = None
            last_x = x
            for _ in range(20):
                with ByteMutFuzzer(self.sf, self.outdir, x, self.options) as f:
                    f._fuzz()
                    result = str(f.output)
                    if last_result:
                        self.assertEqual(result, last_result)
                    else:
                        last_result = result

    def test_is_minimizable(self):
        f = ByteMutFuzzer(*self.args)
        self.assertTrue(f.is_minimizable)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
