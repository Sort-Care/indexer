"""
File: invindex.py
Function: Defines the class Indexer for reading in json file and build
          indexes for it.
Class for building inverted index
"""

import json
from pprint import pprint

# self-defined
from inv_util import *

class Indexer:
    def __init__(self, filename, flag = True, verbose = False):
        # a list of scenes, each element is a dictionary
        self.scenes = None
        # json file name, which will be used in readIn() function
        self.filename = filename
        # inverted index
        self.inv_index = dict()
        # delta encoded index
        self.delta_index = dict()
        # need another map of (docID, sceneID)
        self.sce_map = dict()
        # compact index of the structure [docId, wordCount, pos1, pos2...]
        self.cmp_index = dict()
        # a flag that indicates whether to compress or not
        self.compress = flag
        # vbyte encoded index
        self.vbyte_index = dict()
        # vocabulary (term, term frequency)
        self.vocabulary = dict()
        # print tag
        self.verbose = verbose


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
            self.vbyte_encoding()
            self.compact_index()
            self.dump_compressed_index()
        # then dump the index to file
        else:
            dump_index()

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
            # for each term in that scene:
            for i in range(len(sce['tlist'])):
                t = sce['tlist'][i]
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
        pass

    def dump_compressed_index(self):
        pass



# main
# ind = Indexer('shakespeare-scenes.json')
# ind.readIn()
# pprint(ind.scenes)
# print(type(ind.scenes))

