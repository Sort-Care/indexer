"""
File: invindex.py
Function: Defines the class Indexer for reading in json file and build
          indexes for it.
Class for building inverted index
TODO: 
1. Add tracking for the doc length -- DONE
For each Lists do sth!
2. offset for writing to disk
3. offset{List.key} = {offset, size, List.tdf, List.tcf} 
   Where to read and hbow many bytes to read
   size =   Write(file, offset, compressedFlag)
   writeOffsets();
   writeDocIds()
4. Combine scenes into Plays
5. WriteLengths()
6. Build the tf df DS: term: {tf}
"""

import json
# from pprint import pprint
import linecache
import numpy as np


# self-defined
from inv_util import *

class Indexer:
    def __init__(self,
                 infilename,  # the file that feeds the program with json data
                 outfilename, # the one that used for dumping indexes
                 flag = True,
                 verbose = False):
        # a list of scenes, each element is a dictionary
        self.scenes = None
        # doc length
        self.doc_length = dict()
        # json file name, which will be used in readIn() function
        self.filename = infilename
        # inverted index: term : (docID, Pos) ....
        self.inv_index = dict()
        # delta encoded index
        self.delta_index = dict()
        # need another map of (docID, sceneID)
        self.sce_map = dict()
        # compact index of the structure [docId, wordCount, pos1, pos2...]
        self.cmp_index = dict()
        # uncompressed index
        self.ucmp_index = dict()
        # a flag that indicates whether to compress or not
        self.compress = flag
        # vbyte encoded index
        self.vbyte_index = dict()
        # vocabulary (term, term frequency)
        self.vocabulary = dict()
        # file offset and size (term, (offset, size))
        self.term_offset_size = dict()
        # uncompressed file line number (term, linenumber)
        self.ucmp_linenum = dict()
        # term frequency
        self.term_frequency = dict()

        # print tag
        self.verbose = verbose
        # dump file name
        self.dump_file = outfilename

        # term ID
        self.termtoid = dict()
        # id to term
        self.idtoterm = dict()
        # tf table ndarray
        self.tf = None
        # df array
        self.df = None


    def get_longest_scene(self):
        """
        Get the longest scene name and play name
        """
        # get longest scene
        scene_max = 0
        scene_longest = 0

        scene_min = 100000
        scene_shortest = 0
        for did in self.doc_length:
            if self.doc_length[did] > scene_max:
                scene_max = self.doc_length[did]
                scene_longest = did
            if self.doc_length[did] < scene_min:
                scene_min = self.doc_length[did]
                scene_shortest = did
        longest_name = self.sce_map[scene_longest]
        shortest_name = self.sce_map[scene_shortest]

        # get longest
        return (longest_name, scene_max, shortest_name, scene_min)

    def get_longest_play(self):
        play_length_dic = dict()
        for sce in self.scenes:
            if sce['playId'] not in play_length_dic:
                play_length_dic[sce['playId']] = self.doc_length[sce['sceneNum']]
            else:
                play_length_dic[sce['playId']] += self.doc_length[sce['sceneNum']]

        play_max = 0
        longest_name = None
        
        play_min = 100000
        shortest_name = None
        for play in play_length_dic:
            if play_length_dic[play] > play_max:
                play_max = play_length_dic[play]
                longest_name = play
            if play_length_dic[play] < play_min:
                play_min = play_length_dic[play]
                shortest_name = play
        return (longest_name, play_max, shortest_name, play_min)
            

    def count_tf_df(self):
        """
        Count term frequency and document frequency
        """
        tmid = 0
        row_size = len(self.inv_index.keys()) # get how many terms in total
        column_size = len(self.scenes) # get how many documents
        self.tf = np.zeros(shape = (row_size, column_size), dtype = int) # build the table
        self.df = np.zeros(row_size, dtype = int)
        for term in self.inv_index:
            # store the tmid and term
            self.termtoid[term] = tmid
            self.idtoterm[tmid] = term
            # update the row
            for t in self.inv_index[term]: # for each tuple
                if self.tf[tmid][t[0]] == 0: # first time increment
                    self.df[tmid] += 1
                self.tf[tmid][t[0]] += 1
            tmid += 1

    def dump_tfdf(self):
        with open('termid.json', 'w') as f:
            json.dump(self.termtoid, f)
        with open('idterm.json', 'w') as f:
            json.dump(self.idtoterm, f)
        with open('tf.dat', 'w') as f:
            # dump ndarray
            self.tf.tofile(f)
            # read this with np.fromfile(fobj, dtype = int)
        with open('df.dat', 'w') as f:
            # dump list
            self.df.tofile(f)
            


    def build_and_save(self):
        # read in the json file
        self.readIn()
        # do some preprocessing
        self.prepocess_scenes()
        # build the inverted index
        self.build_inverted_index()
        # if compress tag set to true, compress it
        if self.compress:
            self.delta_encoding()
            self.compact_index()
            self.apply_vbyte()
            self.dump_compressed_index()
        # then dump the index to file
        else:
            self.process_uncompressed_index()
            self.dump_index()

    def readIn(self):
        with open(self.filename) as f:
            # load dic from json file
            scdata= json.load(f)
            # then get the list of scenes
            self.scenes = scdata['corpus']

    def build_inverted_index(self):
        """
        Function that builds the inverted index
        """
        # for each doc
        for sce in self.scenes:
            # use sec['sceneNum'] as the
            docId = sce['sceneNum']
            # update doc lengths ds
            self.doc_length[docId] = len(sce['tlist'])
            # for each term in that scene:
            for i in range(len(sce['tlist'])):
                t = sce['tlist'][i]
                if t not in self.term_frequency:
                    self.term_frequency[t] = 1;
                else:
                    self.term_frequency[t] += 1;
                
                if t not in self.inv_index:
                    self.inv_index[t] = []
                self.inv_index[t].append((docId, i))
            # if it is already presented in self.inv_index
            # then add (docId, position) to its value
            # else if it is not, first add an array to self.inv_index[term]
            # then add (docId, position) to its value

    def prepocess_scenes(self):
        """
        Function that will seperate words in the 'text' of each scene
        It will add a key value pair ('tlist', text_list) 
        to each element in self.scenes
        """
        # for each scene
        for scd in self.scenes:
            text_list = scd['text'].split(" ")
            scd['tlist'] = list(filter(None, text_list))
            # for each scene, add (sceneNum, sceneID) into the mapping
            self.sce_map[scd['sceneNum']] = scd['sceneId']


    def delta_encoding(self):
        """
        Encode the inverted index using delta encoding
        Encode both docID and position informations
        The rule for the delta encoding of the index are:
        - First element of a word, remain unchanged
        - Following items compute delta with the previous one
        - One exception is that, once there is a document change, only delta encode docid
          but not the position. The reason for this is that the difference between
          the last occurance of a word in the previous doc and the first occurance of it
          in the next doc could be a large number.
        Data Structure Changed: self.delta_encoding
        """
        # loop through any keys in the self.inv_index dictionary
        for word in self.inv_index.keys():# for every word in that dic
            prevDoc = None
            curDoc = None
            prevPos = None
            curPos = None
            self.delta_index[word] = [] # add the array that will be holding new values
            # process the list self.inv_index[word]
            pos_list = self.inv_index[word]
            for t in pos_list:# for each (doc, pos) tuple in the list
                if prevDoc is None:# first loop
                    prevDoc = t[0]
                    prevPos = t[1]
                    self.delta_index[word].append((prevDoc, prevPos))
                else:
                    curDoc = t[0]
                    curPos = t[1]
                    delDoc = curDoc - prevDoc
                    
                    if curDoc == prevDoc: # if the same doc
                        delPos = curPos - prevPos
                    else:
                        delPos = curPos
                        
                    self.delta_index[word].append((delDoc, delPos))
                    prevDoc = curDoc
                    prevPos = curPos

    def compact_index(self):
        """
        Compact the indexes to remove unnecessary docIDs
        """
        for word in self.delta_index.keys():
            docNum = None
            cnt = 0
            tmp_list = []
            
            self.cmp_index[word] = [] # create a new array
            
            for t in self.delta_index[word]:# for each tuple
                if docNum == None:# first loop
                    docNum = t[0]
                    cnt = 1
                    self.cmp_index[word].append(docNum)
                    tmp_list.append(t[1])
                    continue

                if t[0] > 0 and docNum != None : # that means a start of a new doc
                    # dump the old count and tmp list
                    self.cmp_index[word].append(cnt)
                    self.cmp_index[word].extend(tmp_list)
                    cnt = 1 # set counter back to 1
                    tmp_list = []# create a new empty one
                    docNum = t[0]
                    
                    # append the next docID
                    self.cmp_index[word].append(docNum)
                    tmp_list.append(t[1])# append the first position
                else: # document didn't change
                    tmp_list.append(t[1]) # append position
                    cnt += 1
            self.cmp_index[word].append(cnt)
            self.cmp_index[word].extend(tmp_list)

    def process_uncompressed_index(self):
        """
        Transfer self.inv_index to another form
        Target: self.uncmp_index[term] = [docid, cnt, pos1, pos2, pos3...]
        """
        for word in self.inv_index.keys():
            docNum = None
            cnt = 0
            tmp_list = []
            self.ucmp_index[word] = []
            for t in self.inv_index[word]:
                if docNum == None:
                    docNum = t[0]
                    cnt = 1
                    self.ucmp_index[word].append(docNum)
                    tmp_list.append(t[1])
                    continue
                if t[0] != docNum and docNum != None:
                    self.ucmp_index[word].append(cnt)
                    self.ucmp_index[word].extend(tmp_list)
                    cnt = 1
                    tmp_list = []
                    docNum = t[0]

                    self.ucmp_index[word].append(docNum)
                    tmp_list.append(t[1])
                else:
                    tmp_list.append(t[1])
                    cnt += 1
            self.ucmp_index[word].append(cnt)
            self.ucmp_index[word].extend(tmp_list)

    def apply_vbyte(self):
        """
        Apply vbyte to every term's array
        """
        for word in self.cmp_index.keys():
            encode_arr = self.vbyte_encoding(self.cmp_index[word])
            self.vbyte_index[word] = encode_arr
                    
    def vbyte_encoding(self, arr):
        """
        Encode content using vbyte
        """
        ol = bytearray()
        for i in arr:
            while i >= 128:
               ol.append(i & 0x7F)
               i = rshift(i, 7)
            ol.append( i | 0x80)
        return ol

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

    def dump_index(self):
        """
        dump uncompressed data to file
        Data that needs to be dumped: self.inv_index
        For this method, each list will take up a whole line in the file
        """
        fn = 'ucmp_' + self.dump_file
        uf = open(fn, 'w')
        lnum = 1
        for word in self.ucmp_index:
            self.ucmp_linenum[word] = lnum
            uf.write(str(self.ucmp_index[word]) + '\n')
            lnum += 1
        uf.close()
        with open('linenum.json', "w") as f:
            json.dump(self.ucmp_linenum, f)

    def dump_compressed_index(self):
        """
        Save Compressed Inverted List to file(self.cmp_index)
        Keep tracking of each list's offset and how many bytes it take to store
        it. That is, update self.term_offset_size
        """
        bf = open(self.dump_file, "wb")# when writing, should open with 'wb'
        offset = 0 # offset starts from zero
        for term in self.vbyte_index:
            size = self.write_data(bf, offset, self.vbyte_index[term])
            self.term_offset_size[term] = (offset, size)
            offset += size
            # My dream provided directions to my life.
        # close compressed binary file
        bf.close()
        # save offset data to file as well
        with open('offset.json', "w") as f:
            json.dump(self.term_offset_size, f)
            

    def write_data(self, filevar, offset, lst_data):
        bdata = bytearray(lst_data) # convert it to bytearray if it is not
        size = len(bdata)# get the length of bytes of the bytearray
        filevar.seek(offset)
        filevar.write(bdata)
        return size

    def read_data_chunk(self, filevar, offset, size):
        filevar.seek(offset)
        return filevar.read(size)
            



# main
# ind = Indexer('shakespeare-scenes.json')
# ind.readIn()
# pprint(ind.scenes)
# print(type(ind.scenes))

