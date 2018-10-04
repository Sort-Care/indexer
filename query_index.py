"""
File for operating queries
TODO:
1. Randomly select 7 terms from the vocabulary. Record the following
	{(term1, df1, tf1) ... (term7, ...)} x 100 times
2. Use Dice's Coefficient, identify the highest scoring two word phrase
   for each of the 7 terms in 100 set
3. Do query with the 100 set and perform a timing experiment
"""
import json
import linecache
import numpy as np
from inv_util import *

class Querier:
    def __init__(self):
        # index read from the compressed file
        self.cmp_index = dict()
        # index read from the uncompressed file
        self.ucmp_index = dict()
        # the target index form that is used for doing queries
        self.query_index = dict()

        # term num
        self.TERMMAX = 0
        # term id: a dictionary that maps term str to number
        self.termtoid = None
        # id to term
        self.idtoterm = None
        # tf (table of shape #term x #doc)
        self.tf = None
        # df (1darray where index represents termid)
        self.df = None
        # data structure for holding randomly generated terms


    def read_term_info(self):
        """
        Read in informations from file that are related to terms
        df.dat: read with np.fromfile: 1darray
        tf.dat: np.fromfile: 2darray
        idterm.json: 
        termjd.json:
        """
        self.df = np.fromfile('df.dat', dtype = int)
        self.tf = np.fromfile('tf.dat', dtype = int).reshape((self.df.size,-1))
        with open('termid.json', 'r') as f:
            self.termtoid = json.load(f)
        with open('idterm.json', 'r') as f:
            self.idtoterm = json.load(f, object_hook = jsonKeys2int)
        self.TERMMAX = self.df.size

    def generate_queries_randomly(self):
        """
        Generate 100 x (7 terms) query sets.
        """
        pass

    def get_dice_coefficient(self, tid1, tid2):
        """
        Return 2n_{ab} / (n_a + n_b)
        """
        na = self.df[tid1]
        nb = self.df[tid2]
        # multiply self.tf[tid1] and self.tf[tid2] elementwise, and count # > 0
        nab = np.count_nonzero(np.multiply(self.tf[tid1], self.tf[tid2]))
        return 2.0 * nab / (na + nb)
        

    def query(self, qry_terms):
        """
        Actually do queries according to terms in the qry_terms
        """
        pass
        

    def read_data_chunk(self, filevar, offset, size):
        """
        Read a chunk of data from binary file(compressed index)
        """
        filevar.seek(offset)
        return filevar.read(size)

    def read_line(self, filename, linenum):
        """
        Read a line of data from uncompressed index file
        """
        theline = linecache.getline(filename, linenum)
        dt = eval(theline)
        return dt

    def vbyte_decoding(self, byarr):
        """
        Decode vbyte encoded strings
        """
        ol = []
        for i in range(len(byarr)):
            position = 0
            res = int( byarr[i] & 0x7f)

            while (byarr[i] & 0x80) == 0:
                i += 1
                position += 1
                unsignedByte = int( byarr[i] & 0x7f)
                res |= ( unsignedByte << (7 * position))
            ol.append(res)
        ol = self.remove_after_big(ol)
        return ol
