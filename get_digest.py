import nnpy
import struct
import ipaddress
from p4utils.utils.topology import Topology
from p4utils.utils.sswitch_API import SimpleSwitchAPI

class DigestController():

    def __init__(self, sw_name):
        self.global_threshold = 1000
        self.local_threshold = 500
        self.min_threshold = 200
        self.sw_name = sw_name
        self.topo = Topology(db="topology.db")
        self.sw_name = sw_name
        self.thrift_port = self.topo.get_thrift_port(sw_name)
        self.controller = SimpleSwitchAPI(self.thrift_port)

    def recv_msg_digest(self, msg):

        topic, device_id, ctx_id, list_id, buffer_id, num = struct.unpack("<iQiiQi",
                                                                     msg[:32])
        #print num, len(msg)
        offset = 12
        msg = msg[32:]
        for sub_message in range(num):
            random_num, src, dst = struct.unpack("!III", msg[0:offset])
            print "packet counter:", random_num, "src ip:", str(ipaddress.IPv4Address(src)), "dst ip:", str(ipaddress.IPv4Address(dst))
            msg = msg[offset:]

        # THE LOGIC FOR DYNMAICALLY UPDATING THE THRESHOLD 
        # logic to update flow-entries based on random_num i.e. current counter
        flow_rules = ["s1-commands.txt", "s2-commands.txt", "s3-commands.txt"]

        if(random_num <= self.min_threshold):
         new_threshold = random_num
         print ("No change in the threshold :" , new_threshold)
        
        elif( random_num > self.min_threshold and random_num <= self.global_threshold):

            ratio = (float(random_num)/float(self.local_threshold))
            new_threshold = (int)(ratio * random_num)
            # for i in range(len(flow_rules)):
            #     self.update_threshold(new_threshold, flow_rules[i])

            print ("The New Theshold is :" , new_threshold," ", ratio)
        
        else:
            new_threshold = self.local_threshold
            # for i in range(len(flow_rules)):
            #  self.update_threshold(new_threshold, flow_rules[i])
            print ("The New Theshold since croosed the global threshold hence we can safely say this was  :" , new_threshold)    

        self.controller.client.bm_learning_ack_buffer(ctx_id, list_id, buffer_id)

    def run_digest_loop(self):

        sub = nnpy.Socket(nnpy.AF_SP, nnpy.SUB)
        notifications_socket = self.controller.client.bm_mgmt_get_info().notifications_socket
        print "connecting to notification sub %s" % notifications_socket
        sub.connect(notifications_socket)
        sub.setsockopt(nnpy.SUB, nnpy.SUB_SUBSCRIBE, '')

        while True:
            msg = sub.recv()
            self.recv_msg_digest(msg)


def main():
    DigestController("s1").run_digest_loop()

if __name__ == "__main__":
    main()