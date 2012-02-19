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
        try:
            d = dict(arg.split('=') for arg in args.split())
        except ValueError:
            # there were probably spaces around the '='
            raise ValueError("Invalid input: try removing spaces from around "
                             "the '=' sign in your argument(s)")
        else:
            try:
                return func(inst, **d)
            except TypeError as out:
                print(out)
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

    def request(self, call, help=self.do_help):
        request = methodcaller(call)
        try:
            val = request(self.srv)
        except api.PermissionError:
            whoami = self.srv.get_whoami()
            print("You don't have sufficient permissions to access the user"
                  " listing. Login info: %s" % repr(whoami))
            return
        except (ValueError, IOError, http.HTTPError) as out:
            print(repr(type(out)), out)
            help()
        except Exception as out:
            print(repr(type(out)), out)
        else:
            return val

    def do_list_users(self, name):
        try:
            users = self.srv.get_users()
        except api.PermissionError:
            whoami = self.srv.get_whoami()
            print("You don't have sufficient permissions to access the user"
                  " listing. Login info: %s" % repr(whoami))
            return
        for user in users:
            u = "Name: {name}\nAdmin: {administrator}\n".format(**user)
            print u

    def do_list_vhosts(self, name):
        vhosts = self.srv.get_all_vhosts()
        for vname in [i['name'] for i in vhosts]:
            print vname

    def do_create_queue(self, name):
        try:
            if not name:
                raise ValueError("You need provide a name for the queue")
            else:
                self.srv.create_queue(name, self.vhost)
        except ValueError as out:
            print(repr(type(out)), out)
            self.help_create_queue()
        except IOError as out:
            print(repr(type(out)), out)
        except http.HTTPError as out:
            print out
            return
        except Exception as out:
            print(repr(type(out)), out)
            self.help_create_queue()

    def help_create_queue(self):
        print("\n".join([
                    "\tcreate_queue <qname>",
                    "\tCreate a queue w/ default binding.",
                    "\tBind to a specific exchange with 'create_binding'."]))

    def do_purge_queue(self, name):
        try:
            if not name or name is None:
                self.help_purge_queue()
            else:
                msgcount = self.srv.purge_queue(self.vhost, name)
                print("Purged %i messages\n" % msgcount)
        except Exception as out:
            print(out)
            self.help_purge_queue()

    def help_purge_queue(self):
        print("\n".join(["\tpurge_queue <qname>",
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

    def do_delete_queue(self, name):
        try:
            self.srv.delete_queue(self.vhost, name)
        except IOError as out:
            print(out)
        except Exception as out:
            print(out)
            self.help_delete_queue()

    def help_delete_queue(self):
        print("\n".join(["\tdelete_queue <qname>",
                         "\tDeletes the named queue."]))

    @parse_keyval_args
    def do_create_exchange(self, name, vhost='/', type='direct'):
        if not name:
            print("You must provide a name!")
            self.help_create_exchange()
        try:
            self.srv.create_exchange(vhost, name, type)
        except IOError as out:
            print(out)
        except Exception as out:
            raise

    def help_create_exchange(self):
        print("\n".join(["\tcreate_exchange name=<name> [type=<type>]",
                         "\tCreate an exchange with given name. Type is 'direct' by default."]))

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

    def do_delete_exchange(self, name):
        try:
            self.srv.delete_exchange(self.vhost, name)
        except IOError as out:
            print(out)
        except Exception as out:
            print(out)
            self.help_delete_exchange()

    def help_delete_exchange(self):
        print("\n".join(["\tdelete_exchange <exchange>",
                         "\tDeletes the named exchange."]))

    @parse_keyval_args
    def do_create_binding(self, queue, exchange):
        try:
            self.srv.create_binding(self.vhost, queue, exchange)
        except Exception as out:
            print("Invalid input. Here's some help: ")
            self.help_create_binding()
            print("Error was: ", out)

    def help_create_binding(self):
        print("\n".join(["\tcreate_binding exchange=<exch> queue=<queue>",
                         "\tBinds given queue to named exchange"]))

    @parse_keyval_args
    def do_list_queue_bindings(self, queue, vhost):
        """
        Get a listing of all bindings for a named queue.

        :param str qname: Name of the queue to list bindings for
        :param str vhost: Vhost the qname lives in.

        """
        vhost = '%2F' if vhost is '/' else vhost
        try:
            bindings = self.srv.get_queue_bindings(vhost, queue)
        except http.HTTPError as out:
            print(out)
            return

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
                line = out_fmt.format(out_vhost, src_exch, queue,
                                       rt_key, arguments)
                print(line)

    def help_list_queue_bindings(self):
        print("\n".join(["\tlist_queue_bindings queue=<queue> vhost=<vhost>",
                        "\tList binding details for the named queue"]))

    def do_send_message(self, args):
        try:
            exchange, message_txt = args.split(':')
            self.srv.publish(self.vhost, exchange, None, message_txt)
        except Exception as out:
            print(out)
            self.help_send_message()

    def help_send_message(self):
        print("\n".join(["\tsend_message <exchange>:<msg>",
                         "\tSends message to the given exchange."]))


    def do_dump_message(self, qname):
        """This only does a basic_get right now. You can't specify a particular message."""
        try:
            msg = self.srv.get_messages(self.vhost, qname)
            if msg is not None:
                print(msg.body)
            else:
                print("No messages in that queue")
        except Exception as out:
            print(out)
            self.help_dump_message()


    def help_dump_message(self):
        print("\n".join(["\tdump_message <queue>",
                         "\tPops a message off the queue and dumps the body to output."]))

    def do_get_status(self, qname):
        try:
            q_properties = self.srv.get_queue(self.vhost, qname)
            print q_properties
        except Exception as out:
            print(out)
            print(self.help_get_status())

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
