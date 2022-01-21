##############################################
#
# Author: Aniruddha Gokhale
#
# Created: Spring 2022
#
# Purpose: demonstrate a basic RPC server
#
#
##############################################

import argparse   # for argument parsing
import zmq  # ZeroMQ 

# ********************************************************************************
# In RPC style (particularly OO-style), we will need an implementation
# object that implements the interface. Recall that our interface is
#
#interface Registry {
#    void get (string key);
#    void put (string key, string value);
#}
#
# So we define an impl class that implements these methods which are invoked
# by the receiving logic
# ********************************************************************************

class ServerImpl ():

    def __init__ (self, args):
        self.port = args.port  # port on which we listen
        self.socket = None

    def bind (self, context):
        # get the socket
        print ("Initialize the socket of type REP")
        self.socket = context.socket (zmq.REP)
        
        # bind to the address
        print ("Binding to port {}".format (self.port))
        bind_str = "tcp://*:" + self.port
        self.socket.bind (bind_str)
        
    def get (self, key):
        # technically we should have done some lookup and returned the
        # value corresponding to the key. But here we don't care and just
        # return what we got.
        print ("Impl: received key {}".format (key))
        return key

    def put (self, key, value):
        # this function really does not return anything
        # as the interface declares it as void. But the REQ-REP
        # pattern needs a response. So we send a dummy ACK
        # We could use a diff ZMQ pattern where a reply is optional
        print ("Received a put msg with key={} and value = {}".format (key, value))
        return "ACK"

# ********************************************************************************
#
# Some representation of the underlying event loop that makes upcalls.
# Let's say we call it Reactor (based on the Reactor pattern)
#
# Note that such an event loop may also exist on client side but we just
# show it for server side
#
# ********************************************************************************

class Reactor ():

    # constructor
    def __init__ (self):
        self.context = zmq.Context ()  # maintain the global context
        self.poller = zmq.Poller ()  # used for our event loop
        self.impl = None

    # register an implementation so that an upcall can be made
    # In reality, a reactor can keep track of multiple such implementations
    # but here we just keep one.
    def register (self, impl):
        self.impl = impl
        self.poller.register (impl.socket, zmq.POLLIN)


    # run the event loop
    def event_loop (self):
        # Now just wait for events to occur (forever)
        print ("Running the event loop")
        while True:
            print ("Wait for the next event")
            events = dict (self.poller.poll ())

            # we are here means something showed up.  Make sure that the
            # event is on the registered socket
            if (self.impl.socket in events):
                print ("Message arrived on our socket; so handling it")
                self.handle_message (self.impl.socket)
            else:
                print ("Message is not on our socket; so ignoring it")
            

    # handle the incoming message and make upcall appropriately. This sort
    # of code is part of the server-side stub and is also usually autogenerated by
    # the IDL compiler.
    def handle_message (self, socket):
        # first thing is to receive whatever was received
        str = socket.recv_string ()
        print ("Received incoming message is: {}".format (str))

        # split the msg into its parts
        parts = str.split (" ")
        
        # check if the first characters are 
        if (parts[0] == "GET"):
            print ("Received a GET message, responding with a reply from the impl")
            # make the upcall on our impl object
            ret = self.impl.get (parts[1])
            socket.send_string (ret)
        elif (parts[0] == "PUT"):
            print ("Received a PUT message, responding with an ack")
            # make upcall
            self.impl.put (parts[1], parts[2])
            socket.send_string ("ack")
        else:
            print ("Unrecognized message type")
            socket.send_string ("Sorry, unrecognized command")
        
###################################
#
# Parse command line arguments
#
###################################
def parseCmdLineArgs ():
    # instantiate a ArgumentParser object
    parser = argparse.ArgumentParser (description="Message Passing Server")

    # Now specify all the optional arguments we support

    # server's port
    parser.add_argument ("-p", "--port", default="5557", help="Port number used by message passing server, default: 5557")

    return parser.parse_args()


##################################
#
#  message handler
#
##################################
##################################
#
#  main program
#
##################################
def main ():
    # first parse the arguments
    print ("Main: parse command line arguments")
    args = parseCmdLineArgs ()

    print ("Current libzmq version is %s" % zmq.zmq_version())
    print ("Current  pyzmq version is %s" % zmq.__version__)

    # obtain the reactor
    print ("Obtain the reactor")
    reactor = Reactor ()

    # start our server
    print ("Instantiate our server implementation")
    impl = ServerImpl (args)

    #make the server listen on a port
    print ("Bind the server to port")
    impl.bind (reactor.context)

    # register with reactor
    print ("register impl with the reactor for incoming requests")
    reactor.register (impl)

    # start event loop
    print ("start the event loop")
    reactor.event_loop ()

    

###################################
#
# Main entry point
#
###################################
if __name__ == "__main__":
    main ()
    
