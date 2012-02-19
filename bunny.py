#!/usr/bin/env python
import cmd
import functools
import getpass
from operator import methodcaller
import sys
from pyrabbit import api, http

# prefer 'input' in 2.7 (req'd in 3.2). Fall back to raw_input for 2.6.
input = getattr(__builtins__, 'input', None) or raw_input

def parse_keyval_args(func):
    @functools.wraps(func)
    def wrapper(inst, args):
        cmd = func.__name__[3:]
        try:
            d = dict(arg.split('=') for arg in args.split())
        except ValueError:
            # there were probably spaces around the '='
            print("Invalid input: Bad arg list, or remove spaces from around "
                             "the '=' sign in your argument(s)")
            inst.do_help(cmd)
        else:
            try:
                return func(inst, **d)
            except TypeError as out:
                print(out)
                inst.do_help(cmd)
    return wrapper



class Bunny(cmd.Cmd):
    """Represents a session between a client and a RabbitMQ server, so you can
     pass commands using syntax like "bunny.connect(), bunny.delete_queue" etc.

     """

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "--> "
        self.host = None
        self.port = None
        self.user = None
        self.password = None
        self.vhost = '/'

    def do_connect(self, line):
        if not self.host:
            self.host = raw_input("Host: ")
            self.port = raw_input("Port: ")
            self.user = raw_input("Username: ")
            self.password = getpass.getpass()

        try:
            print("Connecting to %s as %s" % (self.host, self.user))
            self.srv = api.Client('%s:%s' % (self.host, self.port),
                                  self.user,
                                  self.password)
            print("Success!")
            #connection/channel creation success, change prompt
            self.prompt = "%s.%s: " % (self.host, self.vhost)
        except Exception as out:
            print("Connection or channel creation failed")
            print("Error was: ", out)

    def request(self, call, *args):
        request = methodcaller(call, *args)
        try:
            val = request(self.srv)
        except api.PermissionError:
            whoami = self.srv.get_whoami()
            print("You don't have sufficient permissions to access the user"
                  " listing. Login info: %s" % repr(whoami))
            return
        except (ValueError, IOError, http.HTTPError) as out:
            print(repr(type(out)), out)
        except Exception as out:
            print(repr(type(out)), out)
        else:
            return val

    def do_list_users(self, line):
        """
        This is the docstring for do_list_users2. A call to do_help should
        spit this out in the absence of a help_list_users2 method.
        """
        users = self.request('get_users')
        for user in users:
            u = "Name: {name}\nAdmin: {administrator}\n".format(**user)
            print u

    def do_list_vhosts(self, name):
        vhosts = self.request('get_all_vhosts')
        for vname in [i['name'] for i in vhosts]:
            print vname

    @parse_keyval_args
    def do_create_queue(self, vhost, qname):
        res = self.request('create_queue', qname, vhost)
        print res

    def help_create_queue(self):
        print("\n".join([
                    "\tcreate_queue vhost=<vhost> qname=<qname>",
                    "\tCreate a queue named <qname> in vhost <vhost>",
                    "\tBind to a specific exchange with 'create_binding'."]))

    @parse_keyval_args
    def do_purge_queue(self, vhost, qname):
        msgcount = self.request('purge_queue', vhost, qname)
        print("Purged messages: %s\n" % msgcount)

    def help_purge_queue(self):
        print("\n".join(["\tpurge_queue vhost=<vhost> qname=<qname>",
                         "\tPurges a queue of all content."]))

    def do_qlist(self, s):
        print("\n")
        out_fmt = "{0:<20}|{1:<20}|{2:<20}|{3:<20}"
        cell_line = ('-'*20+'+')*4
        hdr_fields = ["Vhost", "Queue", "Consumers", "Idle Since"]
        hdr = out_fmt.format(*hdr_fields)
        print(hdr)
        print(cell_line)
        for vhost in self.srv.get_all_vhosts():
            vname = vhost['name']
            queues = self.srv.get_queues(vname)
            if not queues:
                print("\tVhost %s has no queues!" % vname)
                print(cell_line)
            else:
                for queue in queues:
                    idle_since = queue['idle_since']
                    consumers = queue['consumers']
                    print(out_fmt.format(vname, queue['name'],
                                     consumers, idle_since))
                    print(cell_line)

    def do_queue_detail(self, args):
        pass

    @parse_keyval_args
    def do_delete_queue(self, vhost, qname):
        self.request('delete_queue', vhost, qname)

    def help_delete_queue(self):
        print("\n".join(["\tdelete_queue vhost=<vhost> qname=<qname>",
                         "\tDeletes the named queue."]))

    @parse_keyval_args
    def do_create_exchange(self, name, vhost='/', type='direct'):
        self.request('create_exchange', vhost, name, type)

    def help_create_exchange(self):
        lines =["\tcreate_exchange name=<name> [vhost=<vhost>] [type=<type>]",
                "\tCreate exchange named <name> in vhost <vhost>.",
                "\tType is 'direct' by default. Vhost is '/' by default."]
        print("\n".join(lines))

    def do_xlist(self, s):
        print("\n")
        for vhost in self.srv.get_all_vhosts():
            vname = vhost['name']
            print("Vhost: %s" % vname)
            exchanges = self.srv.get_exchanges(vname)
            if not exchanges:
                print("\t-- no exchanges! --\n")
            else:
                for exchange in exchanges:
                    print("\t'%s'" % exchange['name'])
                print("\n")
        print('\n')

    @parse_keyval_args
    def do_delete_exchange(self, vhost, name):
        self.request('delete_exchange', vhost, name)

    def help_delete_exchange(self):
        print("\n".join(["\tdelete_exchange vhost=<vhost> name=<exchange>",
                         "\tDeletes the named exchange."]))

    @parse_keyval_args
    def do_create_binding(self, vhost, qname, exchange):
        self.request('create_binding', vhost, qname, exchange)

    def help_create_binding(self):
        lines =["\tcreate_binding vhost=<vhost> exchange=<exch> qname=<qname>",
                "\tBinds given queue to named exchange"]
        print("\n".join(lines))

    @parse_keyval_args
    def do_list_queue_bindings(self, qname, vhost):
        """
        Get a listing of all bindings for a named queue.

        :param str qname: Name of the queue to list bindings for
        :param str vhost: Vhost the qname lives in.

        """
        bindings = self.request('get_queue_bindings', vhost, qname)
        if bindings:
            out_fmt = "{0:<20}|{1:<20}|{2:<20}|{3:<20}|{4:<20}"
            cell_line = ('-'*20+'+')*5
            hdrs = ["Vhost", "Source Exch", "Dest Queue",
                    "Routing Key", "Arguments"]
            hdr = out_fmt.format(*hdrs)
            print(hdr)
            print(cell_line)
            for binding in bindings:
                src_exch = binding['source'] or 'AMQP Default'
                rt_key = binding['routing_key']
                arguments = binding['arguments']
                out_vhost = '/' if vhost is '%2F' else vhost
                line = out_fmt.format(out_vhost, src_exch, qname,
                                       rt_key, arguments)
                print(line)

    def help_list_queue_bindings(self):
        print("\n".join(["\tlist_queue_bindings queue=<queue> vhost=<vhost>",
                         "\tList binding details for the named queue"]))

    @parse_keyval_args
    def do_send_message(self, vhost, exchange, rt_key, msg):
        self.request('publish', vhost, exchange, rt_key, msg)

    def help_send_message(self):
        lines = ["\tsend_message vhost=<vhost> exchange=<exchange>",
                 " rt_key=<rt_key> msg=<msg>",
                 "\tSends message <msg> to <exchange> using <rt_key>"]
        print("\n".join(lines))

    @parse_keyval_args
    def do_dump_message(self, vhost, qname):
        """This only does a basic_get right now. You can't specify a particular message."""
        msg = self.request('get_messages', vhost, qname)
        if msg is not None:
            print(msg.body)
        else:
            print("No messages in that queue")

    def help_dump_message(self):
        print("\n".join(["\tdump_message <queue>",
                         "\tPops a message off the queue and dumps the body to output."]))

    @parse_keyval_args
    def do_get_status(self, vhost, qname):
        q_properties = self.request('get_queue', vhost, qname)
        print q_properties

    def help_get_status(self):
        print("\n".join(["\tget_status <queue>",
                         "\tReports number of messages and consumers for a queue"]))

    def emptyline(self):
        pass

    def do_EOF(self, line):
        print("\n")
        return True

    def do_exit(self):
        return True

    def parseargs(self, args):
        d = dict(arg.split('=') for arg in args.split())
        return d


if __name__ == '__main__':
    shell = Bunny()
    if len(sys.argv) > 1:
        shell.onecmd(' '.join(sys.argv[1:]))
    else:
        shell.cmdloop()
