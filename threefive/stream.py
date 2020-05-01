from .splice import Splice
from bitn import BitBin


class Stream:
    '''
    Parse mpegts files and streams for SCTE 35 packets
    '''
    PACKET_SIZE = 188
    PACKET_COUNT = 512
    SYNC_BYTE = 0x47
    NON_PTS_STREAM_IDS = [188, 190, 191, 240, 241, 242, 248]
    SCTE35_TID = 0xfc

    def __init__(self, tsfile = None, tsstream = None, show_null = False):
        self.SCTE35_PID = False
        self.PTS= False
        self.show_null = show_null
        if tsfile: self.parse_tsfile(tsfile) # for files
        if tsstream: self.parse_tsdata(tsstream) # for reading from stdin

    def parse_tsfile(self, tsfile):
        '''
        used only to open a local file
        '''
        with open(tsfile, 'rb') as tsdata:
            self.parse_tsdata(tsdata)
        return     

    def parse_tsdata(self, tsdata):
        '''
         split tsdata into packets for parsing
        '''
        while tsdata:
            chunky = tsdata.read(self.PACKET_SIZE * self.PACKET_COUNT)
            if not chunky: break
            [self.parse_tspacket(chunky[i:i+self.PACKET_SIZE] )
                     for i in range(0, len(chunky), self.PACKET_SIZE)]
        return
  
    def has_sync_byte(self,first_byte):
        '''
        return True if first_byte
        is equal to self.SYNC_BYTE,
        
        '''
        return (first_byte == self.SYNC_BYTE)
    
    def next_two_bytes(self,two_bytes):
        '''
        returns the second and third
        header bytes as an int
        '''
        return int.from_bytes(two_bytes,byteorder='big')
  
    def the_packet_pid(self,two_bytes):
        '''
        parse packet pid from two bytes
        of the header
        '''
        return two_bytes & 0x1fff
        
    def has_scte35_tid(self,byte5):
        '''
        byte 5 of a SCTE 35 packet must be
        self.SCTE35_TID to be valid
        '''
        return (byte5 == self.SCTE35_TID)

    def try_splice(self,payload,pid):
        try:
            tf = Splice(payload,pid=pid)
            tf.show()
            return True
        except:
            return False
        
    def parse_tspacket(self, packet):
        '''
        parse an mpegts packet for SCTE 35 messages
        '''
        if not self.has_sync_byte(packet[0]):return
        if self.has_scte35_tid(packet[5]) : 
            two_bytes=self.next_two_bytes(packet[1:3])
            pid = self.the_packet_pid(two_bytes)
            if self.SCTE35_PID and (pid != self.SCTE35_PID): return
            if not self.show_null:
                if packet[18] == 0: return
            if not self.try_splice(packet[5:],pid): return
            if not self.SCTE35_PID: self.SCTE35_PID = pid
        return
