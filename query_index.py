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
from random import randint
import re

class Querier:
    def __init__(self):
        # index read from the compressed file
        self.cmp_index = dict()
        # index read from the uncompressed file
        self.ucmp_index = dict()
        # the target index form that is used for doing queries
        self.query_index = dict()
        # compressed file offset
        self.offset = None
        # linenumber
        self.linenum = None

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
        self.randomQueries = []
        # random word's highest match
        self.highestMatch = []
        # selected terms' text, tf, df
        self.selectedTermInfo = []
        # term to term dice coefficient
        self.coefficient = None
        # highest score phrase
        self.phrases = []

    @staticmethod
    def get_vocabulary():
        q = Querier()
        q.read_term_info()
        q.read_offset_linenum()
        return q.linenum.keys()

    @staticmethod
    def do_query(set_num, compressed = True):
        """
        Takes in a number specifying which random set to use
        and then fetch query data
        """
        q = Querier()
        q.read_term_info()
        q.read_offset_linenum()
        q.load_term_and_phrase()
        res = None
        if compressed:
            res = q.query_compressed(set_num)
        else:
            res = q.query_uncompressed(set_num)
        return res 
        
    
    @staticmethod
    def get_term_info(term):
        q = Querier()
        q.read_term_info()
        id = q.termtoid[term]
        return (q.tf[id], q.df[id])

    def get_highest_match_term(self, tid):
        """
        get highest term id that have highest dice coefficient with tid
        """
        max_match = -1
        max_val = 0
        for i in range(self.TERMMAX):
            if i != tid:
                s = self.get_dice_coefficient(tid, i)
                if s > max_val:
                    max_val = s
                    max_match = i
        return max_match

    def save_highest_term(self):
        """
        NOT USED BECAUSE EFFICIENCY
        match terms and save them
        """
        for i in range(len(self.randomQueries)):
            res = []
            for j in range(7):
                term1 = self.idtoterm[self.randomQueries[i][j]]
                term2 = self.idtoterm[self.highestMatch[i][j]]
                res.append((term1, term2))
            self.phrases.append(res)

    def dump_term_and_phrase(self):
        """
        Save two files: 
        'random_term.txt'
        'term_phrase.txt'
        """
        f1 = open('random_term.txt', 'w')
        f2 = open('term_phrase.txt', 'w')
        for lst in self.randomQueries:
            for tid in lst:
                f1.write('%s\t' % self.idtoterm[tid])
                pid = self.get_highest_match_term(tid)
                f2.write('%s %s, ' % (self.idtoterm[tid], self.idtoterm[pid]))
            f1.write('\n')
            f2.write('\n')
        f1.close()
        f2.close()

    def load_term_and_phrase(self):
        """
        load term and phrase from file
        """
        self.randomQueries = []
        self.highestMatch = []
        with open('random_term.txt', 'r') as f:
            lines = f.readlines()
            for l in lines:
                res = []
                dat = l.strip().split('\t') # get a list of terms
                for term in dat:
                    res.append(self.termtoid[term])
                self.randomQueries.append(res)
        with open('term_phrase.txt', 'r') as f:
            lines = f.readlines()
            for l in lines:
                res = []
                dat = re.findall(r"[\w]+", l)
                for i in range(1, 15, 2):
                    res.append(self.termtoid[dat[i]])
                self.highestMatch.append(res)


        

    def compute_term_coe_matrix(self):
        """
        OPTIMIZATION IN ORDER TO SPEED UP self.get_highest_match_term
        Compute term with term dice coefficient using numpy
        """
        # matrix for nab
        bm = self.tf.astype(np.bool)
        im = bm.astype(np.int)
        nab = np.dot(im, im.T)
        t = np.tile(self.df, (self.TERMMAX, 1))
        plus = t + t.T
        self.coefficient = 2 * nab / plus

    def save_coefficient_to_file(self):
        with open('coefficient.dat','w') as f:
            self.coefficient.tofile(f)

    def read_coefficient_from_file(self):
        self.coefficient = np.fromfile('coefficient.dat', dtype = float)
        

    def find_highest_phrase(self):
        for lst in self.randomQueries:# for each 7term query
            res = []
            for tid in lst: # for each term id
                hm = self.get_highest_match_term(tid)
                res.append(hm)
            self.highestMatch.append(res)

    def find_phrase_for_query(self, query):
        """
        Find best match phrase for a single 7 term query
        Input:
        	query: a list with length 7
        """
        res = []
        for tmid in query:
            match = get_highest_match_term(tmid)
            res.append(match)
        return res
            


    def read_offset_linenum(self):
        with open('offset.json') as f:
            self.offset = json.load(f)
        with open('linenum.json') as f:
            self.linenum = json.load(f)

        
    def record_queries_info(self):
        for lst in self.randomQueries: # for each 7 term query
            res = []
            for tid in lst: # for each term id in this query
                termtext = self.idtoterm[tid]
                tf = self.tf[tid]
                df = self.df[tid]
                res.append((termtext, df, tf))
            self.selectedTermInfo.append(res)

    def get_random_ids(self, num = 7):
        """
        get 7 random ids for terms
        """
        res = []
        for i in range(num):
            res.append(randint(0, self.TERMMAX-1))
        return res

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
        for i in range(100):
            nres = self.get_random_ids()# get 7 random ids
            self.randomQueries.append(nres)

    def get_dice_coefficient(self, tid1, tid2):
        """
        Return 2n_{ab} / (n_a + n_b)
        """
        na = self.df[tid1]
        nb = self.df[tid2]
        # multiply self.tf[tid1] and self.tf[tid2] elementwise, and count # > 0
        nab = np.count_nonzero(np.multiply(self.tf[tid1], self.tf[tid2]))
        return 2.0 * nab / (na + nb)
        

    def query_compressed(self, set_num):
        """
        Actually do queries according to terms in the qry_terms
        This function should be called 100 times with different set number to do the experiment
        """
        res = dict()
        query_ids = self.randomQueries[set_num]
        query_phrase = self.highestMatch[set_num]
        for i in range(len(query_ids)):
            # print("Retrieving Compressed Index for Phrase: {}({}) {}({}) ".format(self.idtoterm[query_ids[i]],
            #                                                                       query_ids[i],
            #                                                                       self.idtoterm[query_phrase[i]],
            #                                                                       query_phrase[i]))
            term1 = self.idtoterm[query_ids[i]]
            term2 = self.idtoterm[query_phrase[i]]
            offset1, size1 = self.offset[term1]
            offset2, size2 = self.offset[term2]
            index1 = self.restore_compressed_data(offset1, size1)
            index2 = self.restore_compressed_data(offset2, size2)
            #print("Index for {} : {}".format(term1, index1))
            #print("Index for {} : {}".format(term2, index2))
            res[term1] = index1
            res[term2] = index2
        return res


    def restore_compressed_data(self, offset, size):
        """
        Read data and apply vbyte decoding and delta decoding
        """
        f = open('indx.dat', 'rb')
        data = self.read_data_chunk(f, offset, size)
        decoded = self.vbyte_decoding(data)
        # apply delta decoding
        real_index = self.delta_decoding(decoded)
        f.close()
        return real_index


    def delta_decoding(self, arry):
        """
        Decode delta encoded data (docID, cnt, pos1, pos2, ... docID2, cnt2)
        """
        res = []
        docID = arry[0]
        cnt = arry[1]
        firstPos = arry[2]
        res.append(docID)
        res.append(cnt)
        res.append(firstPos)
        anchor = 3

        
        while len(res) < len(arry):
            for i in range(cnt):
                if i != 0:
                    res.append(firstPos + arry[anchor])
                    firstPos += arry[anchor]
                    anchor += 1
            if anchor >= len(arry): break;
            docID += arry[anchor]
            cnt = arry[anchor + 1]
            firstPos = arry[anchor +2]
            res.append(docID)
            res.append(cnt)
            res.append(firstPos)
            anchor += 3
        return res
            

    def query_uncompressed(self, set_num):
        """
        Query the uncomprssed
        """
        res = dict()
        query_ids = self.randomQueries[set_num]
        query_phrase = self.highestMatch[set_num]
        for i in range(len(query_ids)):
            term1 = self.idtoterm[query_ids[i]]
            term2 = self.idtoterm[query_phrase[i]]
            #print("Processing uncompressed data to fetch Index for term {},{}".format(term1, term2))
            linenum1 = self.linenum[term1]
            linenum2 = self.linenum[term2]
            # next read the index
            index1 = eval(linecache.getline('ucmp_indx.dat', linenum1))
            index2 = eval(linecache.getline('ucmp_indx.dat', linenum2))
            #print("Index for {} : {}".format(term1, index1))
            #print("Index for {} : {}".format(term2, index2))
            res[term1] = index1
            res[term2] = index2
        return res

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

    def remove_after_big(self, arr):
        res = []
        igtag = False
        for a in arr:
            if igtag == False:
                res.append(a)
            else:
                igtag = False
                continue
            if a >= 128 :
                igtag = True
        return res

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
