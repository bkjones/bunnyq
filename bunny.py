#!/usr/bin/env python
from amqplib import client_0_8 as amqp
import cmd
import readline
import string
import getpass

class Bunny(cmd.Cmd):
  """Represents a session between a client and a RabbitMQ server, so you can pass commands
      using syntax like "bunny.connect(), bunny.delete_queue" etc. """

  prompt = "--> "
  qlist = {"/":[]}
  def do_connect(self, line):
    host = raw_input("Host: ")
    user = raw_input("Username: ")
    password = getpass.getpass()
    vhost = '/'

    try:
      print "Trying connect to %s:%s as %s" % (host, vhost, user)
      self.conn = amqp.Connection(userid=user, password=password, host=host, virtual_host=vhost, ssl=False)
      self.chan = self.conn.channel()
      print "Success!"
      """connection/channel creation success, change prompt"""
      self.prompt = "%s.%s: " % (host, vhost)
    except Exception:
      print "Connection or channel creation failed"

  def do_create_queue(self, name):
    try:
      self.check_conn()
      if not name:
        raise ValueError("You need provide a name for the queue")
      else:
        self.chan.queue_declare(name)
        self.qlist["/"].append(name)
    except ValueError as out:
      print out
      self.help_create_queue
    except IOError as out:
      print out
    except Exception as out:
      print out
      self.help_create_queue()

  def help_create_queue(self):
    print "\n".join(["\tcreate_queue <qname>",
                     "\tCreates a queue with a default binding provided by the server.",
                     "\tBind to a specific exchange with 'create_binding'."])

  def do_purge_queue(self, name):
    try:
      self.check_conn()
      if not name or name is None:
        self.help_purge_queue()
      else:
        msgcount = self.chan.queue_purge(name, nowait=False)
        print "Purged %i messages\n" % msgcount
    except Exception as out:
      print out
      self.help_purge_queue()

  def help_purge_queue(self):
    print "\n".join(["\tpurge_queue <qname>",
                     "\tPurges a queue, leaving it with a message count of 0, without interrupting consumers."])


  def do_qlist(self, s):
    print "\n"
    for exch, queues in self.qlist.iteritems():
      print "Exchange: %s" % exch
      for q in queues:
        print "\t%s" % q
    print "\n"

  def do_delete_queue(self, name):
    """amqplib's 'Channel' object has a queue_delete method"""
    try:
      self.check_conn()
      self.chan.queue_delete(name)
      for k,v in self.qlist.iteritems():
        if name in v:
          v.remove(name)
    except IOError as out:
      print out
    except Exception as out:
      print out
      self.help_delete_queue()

  def help_delete_queue(self):
    print "\n".join(["\tdelete_queue <qname>",
                     "\tDeletes the named queue."])

  def check_conn(self):
    if not self.__dict__.has_key('chan'):
      raise IOError("You don't have a valid connection to the server. Run 'connect'")
    else:
      return True

  def do_create_exchange(self, args):
    try:
      self.check_conn()
      d = self.parseargs(args)

      if not d.has_key('type'):
        print "No type - using 'direct'"
        type = 'direct'
      else:
        type = d['type']
        print "TYPE: %s" % type

      if not d.has_key('name'):
        print "You must provide a name!"
      else:
        name = d['name']

      self.chan.exchange_declare(name, type)
      self.qlist[name] = []
    except IOError as out:
      print out
    except Exception as out:
      print out  # uncomment for debugging
      print "Invalid input. Here's some help: "
      self.help_create_exchange()



  def help_create_exchange(self):
    print "\n".join(["\tcreate_exchange name=<name> [type=<type>]",
                     "\tCreate an exchange with given name. Type is 'direct' by default."])

  def do_delete_exchange(self, name):
    try:
      self.check_conn()
      self.chan.exchange_delete(name)
      if self.qlist.has_key(name):
        for q in self.qlist[name]:
          self.qlist["/"].append(q)
        del self.qlist[name]
    except IOError as out:
      print out
    except Exception:
      self.help_delete_exchange()

  def help_delete_exchange(self):
    print "\n".join(["\tdelete_exchange <exchange>",
                     "\tDeletes the named exchange."])

  def do_create_binding(self, bstring):
    try:
      self.check_conn()
      d = parseargs(bstring)
      queue = d['queue']
      exchange = d['exchange']
      self.chan.queue_bind( queue, exchange )

      """Update internal accounting of bindings kept in self.qlist.
      We just created a new binding, so the default binding done by the server
      at time of queue_declare should be updated, and the queue list for the
      exchange used in this method should be updated."""
      if not self.qlist.has_key(exchange):
        self.qlist[exchange] = []
      if queue not in self.qlist[exchange]:
        self.qlist[exchange].append(queue)
      if queue in self.qlist["/"]:
        self.qlist["/"].remove(queue)
    except IOError as out:
      print out
    except Exception:
      print "Invalid input. Here's some help: "
      self.help_create_binding()


  def help_create_binding(self):
    print "\n".join(["\tcreate_binding exchange=<exch> queue=<queue>",
                     "\tBinds given queue to named exchange"])

  def do_send_message(self, args):
    try:
        self.check_conn()
        (exchange, message_txt) = string.split(args, ':')
        message = amqp.Message(message_txt)
        self.chan.basic_publish(message, exchange)
    except Exception as out:
      print out
      self.help_send_message()

  def help_send_message(self):
    print "\n".join(["\tsend_message <exchange>:<msg>",
                      "\tSends message to the given exchange."])


  def do_dump_message(self, qname):
    """This only does a basic_get right now. You can't specify a particular message."""
    try:
      self.check_conn()
      msg = self.chan.basic_get(qname, no_ack=True)
      if msg is not None:
        print msg.body
      else:
        print "No messages in that queue" 
    except Exception as out:
      print out
      self.help_dump_message()

  def help_dump_message(self):
    print "\n".join(["\tdump_message <queue>",
                      "\tPops a message off the queue and dumps the body to output."])


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
