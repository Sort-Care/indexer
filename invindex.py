import json
from pprint import pprint

class Indexer:
    def __init__(self, filename):
        # a list of scenes, each element is a dictionary
        self.scenes = None
        # json file name, which will be used in readIn() function
        self.filename = filename

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
        pass

    def prepocess_scenes(self):
        """
        Function that will seperate words in the 'text' of each scene
        It will add a key value pair ('tlist', text_list) 
        to each element in self.scenes
        """
        # for each scene
        for scd in self.scenes:
            text_list = scd['text'].split(" ")
            scd['tlist'] = text_list


# main
# ind = Indexer('shakespeare-scenes.json')
# ind.readIn()
# pprint(ind.scenes)
# print(type(ind.scenes))

