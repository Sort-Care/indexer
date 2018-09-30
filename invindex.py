import json
from pprint import pprint

class Indexer:
    def __init__(self, filename):
        # a list of scenes, each element is a dictionary
        self.scenes = None
        # json file name, which will be used in readIn() function
        self.filename = filename
        # inverted index
        self.inv_index = dict()

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


    def vbyte_encoding(self):
        """
        Encode content using vbyte
        """
        pass

    def vbyte_decoding(self):
        pass

    def delta_encoding(self):
        pass

    def index_dump(self):
        pass


# main
# ind = Indexer('shakespeare-scenes.json')
# ind.readIn()
# pprint(ind.scenes)
# print(type(ind.scenes))

