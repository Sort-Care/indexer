"""
File for operating queries
"""
import linecache


class Querier:
    def __init__(self):
        # index read from the compressed file
        self.cmp_index = dict()
        # index read from the uncompressed file
        self.ucmp_index = dict()
        # the target index form that is used for doing queries
        self.query_index = dict()


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
