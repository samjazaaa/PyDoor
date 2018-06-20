#! /bin/bash

case "$1" in
	start)
		echo "Ignoring incoming pings!"
		sudo sysctl -w net.ipv4.icmp_echo_ignore_all=1
		;;
	stop)
		echo "Reactivating pings!"
		sudo sysctl -w net.ipv4.icmp_echo_ignore_all=0
		;;
	*)
		echo "Usage: ./ignoreEcho.sh {start|stop}"
		exit 1
		;;
esac

exit 0
