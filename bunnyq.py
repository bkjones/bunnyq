#!/usr/bin/env python
import argparse
import cmd
import functools
import getpass
from operator import methodcaller
from pyrabbit import api, http
import yaml

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
     pass commands using syntax like "bunnyq.connect(), bunnyq.delete_queue" etc.

     """

    def __init__(self, host=None, port=None, user=None, password=None):
        cmd.Cmd.__init__(self)
        self.prompt = "--> "
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.do_connect()

    def do_connect(self):
        if not self.host:
            self.host = raw_input("Host: ")
        if not self.port:
            self.port = raw_input("Port: ")
        if not self.user:
            self.user = raw_input("Username: ")
        if not self.password:
            self.password = getpass.getpass()

        try:
            print("Connecting to %s as %s" % (self.host, self.user))
            self.srv = api.Client('%s:%s' % (self.host, self.port),
                                  self.user,
                                  self.password)
            print("Success!")
            print("Admin privileges: %s" % self.srv.has_admin_rights)
            #connection/channel creation success, change prompt
            self.prompt = "%s@%s: " % (self.user, self.host)
        except Exception as out:
            print("Connection failed")
            print("Error was: ", out)

    def request(self, call, *args):
        request = methodcaller(call, *args)
        try:
            val = request(self.srv)
        except api.PermissionError:
            whoami = self.srv.get_whoami()
            print("You don't have sufficient permissions"
                  " Login info: %s" % repr(whoami))
            return
        except (ValueError, IOError) as out:
            print(repr(type(out)), out)
        except http.HTTPError as out:
            print out
        except Exception as out:
            print(repr(type(out)), out)
        else:
            return val

    def do_list_users(self, line):
        """
        Lists user names and admin priv status.
        """
        users = self.request('get_users')
        if users:
            for user in users:
                u = "Name: {name}\nAdmin: {administrator}\n".format(**user)
                print u

    def do_list_vhosts(self, name):
        """
        Lists names of each RabbitMQ vhost
        """
        vhosts = self.request('get_all_vhosts')
        for vname in [i['name'] for i in vhosts]:
            print vname

    @parse_keyval_args
    def do_create_queue(self, vhost, qname):
        """
        Creates a queue named <qname> in vhost <vhost>
        """
        self.request('create_queue', qname, vhost)

    def help_create_queue(self):
        print("\n".join([
                    "\tcreate_queue vhost=<vhost> qname=<qname>",
                    "\tCreate a queue named <qname> in vhost <vhost>",
                    "\tBind to a specific exchange with 'create_binding'."]))

    @parse_keyval_args
    def do_purge_queue(self, vhost, qname):
        """
        Removes all messages from a named queue.
        """
        msgcount = self.request('purge_queue', vhost, qname)
        print("Purged messages: %s\n" % msgcount)

    def help_purge_queue(self):
        print("\n".join(["\tpurge_queue vhost=<vhost> qname=<qname>",
                         "\tPurges a queue of all content."]))

    def do_qlist(self, s):
        """
        Provides a listing of queues, including number of consumers,
        queue depth, etc.
        """
        print("\n")
        out_fmt = "{0:<20}|{1:<20}|{2:<20}|{3:<20}|{4:<20}"
        cell_line = ('-'*20+'+')*5
        hdr_fields = ["Vhost", "Queue", "Consumers", "Depth", "Idle Since"]
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
                    msgs = queue['messages']
                    print(out_fmt.format(vname, queue['name'], msgs,
                                         consumers, idle_since))
                    print(cell_line)

    @parse_keyval_args
    def do_delete_queue(self, vhost, qname):
        """
        Completely eradicates a queue. It's gone. No going back.
        """
        self.request('delete_queue', vhost, qname)

    def help_delete_queue(self):
        print("\n".join(["\tdelete_queue vhost=<vhost> qname=<qname>",
                         "\tDeletes the named queue."]))

    @parse_keyval_args
    def do_create_exchange(self, name, vhost='/', type='direct'):
        """
        Creates a new exchange named <name>.
        """
        self.request('create_exchange', vhost, name, type)

    def help_create_exchange(self):
        lines =["\tcreate_exchange name=<name> [vhost=<vhost>] [type=<type>]",
                "\tCreate exchange named <name> in vhost <vhost>.",
                "\tType is 'direct' by default. Vhost is '/' by default."]
        print("\n".join(lines))

    def do_xlist(self, s):
        """
        List all of the exchanges, broken down by vhost.
        """
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
        """
        Delete an exchange named <name> in vhost <vhost>.
        """
        self.request('delete_exchange', vhost, name)

    def help_delete_exchange(self):
        print("\n".join(["\tdelete_exchange vhost=<vhost> name=<exchange>",
                         "\tDeletes the named exchange."]))

    @parse_keyval_args
    def do_create_binding(self, vhost, qname, exchange, rt_key):
        """
        Creates a binding between a queue and exchange. Exchange-to-exchange
        bindings are not yet supported.
        """
        self.request('create_binding', vhost, exchange, qname, rt_key)

    def help_create_binding(self):
        lines =["\tcreate_binding vhost=<vhost> exchange=<exch> qname=<qname>"
                " rt_key=<rt_key>",
                "\tBinds given queue to named exchange using given rt_key"]
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
        print("\n".join(["\tlist_queue_bindings qname=<qname> vhost=<vhost>",
                         "\tList binding details for the named queue"]))

    @parse_keyval_args
    def do_send_message(self, vhost, exchange, rt_key, msg):
        """
        This actually uses the HTTP REST Management api to push a message into
        an exchange. It DOES NOT USE THE AMQP PROTOCOL. Therefore, it's a good
        way to test that, say, a routing key works as you expect, but it's not
        a good sanity check against your amqplib code. It's perfectly
        reasonable for this to work while your code is broken. ;-)
        """
        self.request('publish', vhost, exchange, rt_key, msg)

    def help_send_message(self):
        lines = ["\tsend_message vhost=<vhost> exchange=<exchange>",
                 " rt_key=<rt_key> msg=<msg>",
                 "\tSends message <msg> to <exchange> using <rt_key>"]
        print("\n".join(lines))

    @parse_keyval_args
    def do_dump_message(self, vhost, qname):
        """
        This only does a basic_get right now. You can't specify a
        particular message.

        """
        msg = self.request('get_messages', vhost, qname)
        if msg is not None:
            print(msg[0]['payload'])
        else:
            print("No messages in that queue")

    def help_dump_message(self):
        print("\n".join(["\tdump_message vhost=<vhost> qname=<queue>",
                         "\tPops a message off the queue and dumps the body to output."]))

    @parse_keyval_args
    def do_get_status(self, vhost, qname):
        """
        Lists number of messages and consumers for a queue.
        """
        q_properties = self.request('get_queue', vhost, qname)
        print q_properties

    def help_get_status(self):
        print("\n".join(["\tget_status vhost=<vhost> qname=<qname>",
                         "\tReports number of messages and consumers for a queue"]))

    def emptyline(self):
        pass

    def do_EOF(self, line):
        print("\n")
        return True

    def do_exit(self):
        return True

def do_options():
    parser = argparse.ArgumentParser(prog='bunnyq',
                                  description="A CLI for interacting w/ the " \
                                              "RabbitMQ Management API.")
    parser.add_argument('-c', '--config', type=str, default=None,
                        help='Path to configuration file')

    parser.add_argument('-u', '--user', type=str, default=None,
                        help="user to connect to RabbitMQ as.")

    parser.add_argument('-r', '--rabbithost', type=str, default=None,
                        help='The host to connect to. This is the name of' \
                             ' a connection def in the config if -c is ' \
                             'used.')
    parser.add_argument('-p', '--port', type=int, default=None,
                        help="The port to connect to RabbitMQ with.")

    parser.add_argument('-a', '--auth', type=str, default=None,
                        help="password to use to connect to RabbitMQ.")

    parser.add_argument('-x', '--execute', type=str, default=None,
                        help='command string to execute')

    args = parser.parse_args()
    return args

def main():
    args = do_options()

    if args.config:
        # if there's a config arg, there should also be a host arg.
        if not args.rabbithost:
            raise Exception("Specify a '-r' option so bunnyq knows where in "
                            "the config to look for connection parameters.")
        with open(args.config, 'r') as conf:
            config = yaml.load(conf)

        # prefer the config values, filling in values in args as needed.
        config = config[args.rabbithost]
        host = config.get('host', args.rabbithost)
        port = config.get('port', args.port)
        user = config.get('user', args.user)
        password = config.get('password', args.auth)
    else:
        # there's no config option at all: get all from args.
        host = args.rabbithost
        port = args.port
        user = args.user
        password = args.auth

    shell = Bunny(host, port, user, password)
    if args.execute:
        shell.onecmd(args.execute)
    else:
        shell.cmdloop()

if __name__ == '__main__':
    main()
