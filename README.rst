=================
What is Bunny?
=================


Bunny aims to be a RabbitMQ administration and testing/development swiss
army knife. It allows you to do a large (and growing) number of tasks that are
supported by RabbitMQ's RESTful HTTP Management API. To get a list of current
tasks that are supported, run '?' from within the shell. Here's the output
at time of writing (Feb. 2012):

::

  guest@localhost: ?

  Documented commands (type help <topic>):
  ========================================
  create_binding   delete_exchange  get_status           list_vhosts   xlist
  create_exchange  delete_queue     list_queue_bindings  purge_queue
  create_queue     dump_message     list_users           send_message

  Undocumented commands:
  ======================
  EOF  connect  exit  help  qlist

Here's a sample run:

::

  (bunny)newhotness:bunny bjones$ ./bunny.py -c config-sample.yaml -r localhost -u guest -a guest
  Connecting to localhost as guest
  Success!
  Admin privileges: True
  guest@localhost: list_users
  Name: guest
  Admin: True

  Name: luser
  Admin: False

  guest@localhost: list_vhosts
  /
  diabolica
  testvhost
  guest@localhost: qlist


  Vhost               |Queue               |Consumers           |Depth               |Idle Since
  --------------------+--------------------+--------------------+--------------------+--------------------+
  /                   |aliveness-test      |0                   |0                   |2012-2-16 13:29:57
  --------------------+--------------------+--------------------+--------------------+--------------------+
  /                   |fuuuuuuuuuuuu       |0                   |0                   |2012-2-15 22:55:38
  --------------------+--------------------+--------------------+--------------------+--------------------+
  /                   |testq               |0                   |0                   |2012-1-25 14:1:19
  --------------------+--------------------+--------------------+--------------------+--------------------+
  /                   |whateverdude        |0                   |0                   |2012-2-19 11:47:42
  --------------------+--------------------+--------------------+--------------------+--------------------+
  diabolica           |dbqueue             |0                   |0                   |2012-2-19 22:56:9
  --------------------+--------------------+--------------------+--------------------+--------------------+
  diabolica           |dqueue              |0                   |0                   |2012-2-19 22:55:2
  --------------------+--------------------+--------------------+--------------------+--------------------+
  testvhost           |test123             |0                   |0                   |2012-1-25 14:1:19
  --------------------+--------------------+--------------------+--------------------+--------------------+
  testvhost           |testcreation        |0                   |0                   |2012-2-19 22:54:41
  --------------------+--------------------+--------------------+--------------------+--------------------+
  guest@localhost: list_queue_bindings qname=dbqueue vhost=diabolica
  Vhost               |Source Exch         |Dest Queue          |Routing Key         |Arguments
  --------------------+--------------------+--------------------+--------------------+--------------------+
  diabolica           |foo                 |dbqueue             |None                |{}
  diabolica           |AMQP Default        |dbqueue             |dbqueue             |{}

  guest@localhost: send_message vhost=diabolica exchange=foo rt_key=foobar msg=barfoo
  guest@localhost: qlist


  Vhost               |Queue               |Consumers           |Depth               |Idle Since
  --------------------+--------------------+--------------------+--------------------+--------------------+
  /                   |aliveness-test      |0                   |0                   |2012-2-16 13:29:57
  --------------------+--------------------+--------------------+--------------------+--------------------+
  /                   |fuuuuuuuuuuuu       |0                   |0                   |2012-2-15 22:55:38
  --------------------+--------------------+--------------------+--------------------+--------------------+
  /                   |testq               |0                   |0                   |2012-1-25 14:1:19
  --------------------+--------------------+--------------------+--------------------+--------------------+
  /                   |whateverdude        |0                   |0                   |2012-2-19 11:47:42
  --------------------+--------------------+--------------------+--------------------+--------------------+
  diabolica           |dbqueue             |1                   |0                   |2012-2-19 23:12:7
  --------------------+--------------------+--------------------+--------------------+--------------------+
  diabolica           |dqueue              |0                   |0                   |2012-2-19 22:55:2
  --------------------+--------------------+--------------------+--------------------+--------------------+
  testvhost           |test123             |0                   |0                   |2012-1-25 14:1:19
  --------------------+--------------------+--------------------+--------------------+--------------------+
  testvhost           |testcreation        |0                   |0                   |2012-2-19 22:54:41
  --------------------+--------------------+--------------------+--------------------+--------------------+
  guest@localhost: dump_message vhost=diabolica qname=dbqueue
  barfoo
  guest@localhost: qlist


  Vhost               |Queue               |Consumers           |Depth               |Idle Since
  --------------------+--------------------+--------------------+--------------------+--------------------+
  /                   |aliveness-test      |0                   |0                   |2012-2-16 13:29:57
  --------------------+--------------------+--------------------+--------------------+--------------------+
  /                   |fuuuuuuuuuuuu       |0                   |0                   |2012-2-15 22:55:38
  --------------------+--------------------+--------------------+--------------------+--------------------+
  /                   |testq               |0                   |0                   |2012-1-25 14:1:19
  --------------------+--------------------+--------------------+--------------------+--------------------+
  /                   |whateverdude        |0                   |0                   |2012-2-19 11:47:42
  --------------------+--------------------+--------------------+--------------------+--------------------+
  diabolica           |dbqueue             |0                   |0                   |2012-2-19 23:16:13
  --------------------+--------------------+--------------------+--------------------+--------------------+
  diabolica           |dqueue              |0                   |0                   |2012-2-19 22:55:2
  --------------------+--------------------+--------------------+--------------------+--------------------+
  testvhost           |test123             |0                   |0                   |2012-1-25 14:1:19
  --------------------+--------------------+--------------------+--------------------+--------------------+
  testvhost           |testcreation        |0                   |0                   |2012-2-19 22:54:41
  --------------------+--------------------+--------------------+--------------------+--------------------+

Features
-------------

 - It's easy to use and works on any RabbitMQ server running the HTTP
   Management API.
 - Provides an interactive shell to issue commands to the server.
 - Optional 'one-shot' mode: you don't *have* to launch a full-blown shell if
   you just want to send one command to a host.
 - Optional config file makes it easy to deal with managing a lot of servers
   without getting carpal tunnel syndrome.
 - Really easy to extend to add new commands.
 - If readline is available, command history and completion should
   work. On my test machine (a mac running Lion), history and
   completion both work.

Requirements
----------------

 - argparse (unless you're using Python >=2.7. Get a backported argparse for
         Python <=2.6 at http://pypi.python.org/pypi/argparse)
 - pyrabbit (I wrote this too: http://pypi.python.org/pypi/pyrabbit)
 - PyYaml (http://pypi.python.org/pypi/PyYAML)



