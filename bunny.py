#!/usr/bin/env python
from amqplib import client_0_8 as amqp
import cmd
import readline
import getpass
from pyrabbit import api

# prefer 'input' in 2.7 (req'd in 3.2). Fall back to raw_input for 2.6.
input = getattr(__builtins__, 'input', None) or raw_input

class Bunny(cmd.Cmd):
    """Represents a session between a client and a RabbitMQ server, so you can
     pass commands using syntax like "bunny.connect(), bunny.delete_queue" etc.

     """

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "--> "
        self.qlist = {"/": []}
        self.host = None
        self.user = None
        self.password = None
        self.vhost = '/'

    def do_connect(self, line):
        if not self.host:
            self.host = raw_input("Host: ")
            self.user = raw_input("Username: ")
            self.password = getpass.getpass()

        try:
            print("Connecting to %s as %s" % (self.host, self.user))
            self.srv = api.Server(self.host, self.user, self.password)
            print("Success!")
            #connection/channel creation success, change prompt
            self.prompt = "%s.%s: " % (self.host, self.vhost)
        except Exception as out:
            print("Connection or channel creation failed")
            print("Error was: ", out)

    def do_list_users(self, name):
        users = self.srv.get_users()
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
                self.srv.queue_declare(name)
                self.qlist["/"].append(name)
        except ValueError as out:
            print(out)
            self.help_create_queue()
        except IOError as out:
            print(out)
        except Exception as out:
            print(out)
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
                msgcount = self.srv.queue_purge(name, nowait=False)
                print("Purged %i messages\n" % msgcount)
        except Exception as out:
            print(out)
            self.help_purge_queue()

    def help_purge_queue(self):
        print("\n".join(["\tpurge_queue <qname>",
                         "\tPurges a queue of all content."]))

    def do_qlist(self, s):
        print("\n")
        for exch, queues in self.qlist.iteritems():
            print("Exchange: %s" % exch)
            for q in queues:
                print("\t%s" % q)
        print("\n")

    def do_delete_queue(self, name):
        try:
            self.srv.queue_delete(name)
            for k, v in self.qlist.iteritems():
                if name in v:
                    v.remove(name)
        except IOError as out:
            print(out)
        except Exception as out:
            print(out)
            self.help_delete_queue()

    def help_delete_queue(self):
        print("\n".join(["\tdelete_queue <qname>",
                         "\tDeletes the named queue."]))

    def do_create_exchange(self, args):
        name = None
        d = self.parseargs(args)
        type = d.get('type') or 'direct'
        print("TYPE: %s" % type)

        if 'name' not in d:
            print("You must provide a name!")
            self.help_create_exchange()
        else:
            name = d['name']

        try:
            self.srv.exchange_declare(name, type)
            self.qlist[name] = []
        except IOError as out:
            print(out)
        except Exception as out:
            print(out)
            print("Invalid input. Here's some help: ")
            self.help_create_exchange()

    def help_create_exchange(self):
        print("\n".join(["\tcreate_exchange name=<name> [type=<type>]",
                         "\tCreate an exchange with given name. Type is 'direct' by default."]))

    def do_delete_exchange(self, name):
        try:
            self.srv.exchange_delete(name)
            if self.qlist.has_key(name):
                for q in self.qlist[name]:
                    self.qlist["/"].append(q)
                del self.qlist[name]
        except IOError as out:
            print(out)
        except Exception as out:
            print(out)
            self.help_delete_exchange()

    def help_delete_exchange(self):
        print("\n".join(["\tdelete_exchange <exchange>",
                         "\tDeletes the named exchange."]))

    def do_create_binding(self, bstring):
        try:
            d = self.parseargs(bstring)
            queue = d['queue']
            exchange = d['exchange']
            self.srv.queue_bind(queue, exchange)
        except Exception as out:
            print("Invalid input. Here's some help: ")
            self.help_create_binding()
            print("Error was: ", out)

    def help_create_binding(self):
        print("\n".join(["\tcreate_binding exchange=<exch> queue=<queue>",
                         "\tBinds given queue to named exchange"]))

    def do_send_message(self, args):
        try:
            exchange, message_txt = args.split(':')
            message = amqp.Message(message_txt)
            self.srv.basic_publish(message, exchange)
        except Exception as out:
            print(out)
            self.help_send_message()

    def help_send_message(self):
        print("\n".join(["\tsend_message <exchange>:<msg>",
                         "\tSends message to the given exchange."]))


    def do_dump_message(self, qname):
        """This only does a basic_get right now. You can't specify a particular message."""
        try:
            msg = self.srv.basic_get(qname, no_ack=True)
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
            q, msgcount, consumers = self.srv.queue_declare(queue=qname,
                                                             passive=True)
            print("%s: %d messages, %d consumers" % (q, msgcount, consumers))

        except Exception as out:
            print(out)
            print(self.help_get_status())

    def help_get_status(self):
        print("\n".join(["\tget_status <queue>",
                         "\tReports number of messages and consumers for a queue"]))

    def emptyline(self):
        pass

    def do_EOF(self, line):
        return True

    def do_exit(self):
        return True

    def parseargs(self, args):
        d = dict(arg.split('=') for arg in args.split())
        return d


shell = Bunny()
shell.cmdloop()
