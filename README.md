# PyDoor
Simple python backdoor

It communicates via **ICMP**, making it pretty stealthy.
It needs admin rights on the target system.


## Preparing the attacking system

Before installing the backdoor on the target system, some precautions must be taken on the attacker's system.
It must be ensured that *ICMP echo requests* are not automatically answered by the operating system.
This can be done either temporarily by running the script `ignoreEcho.sh start` or permanently by inserting 

```
net.ipv4.icmp_echo_ignore_all = 1
```

into `/etc/sysctl.conf`.

For longer use of the backdoor, however, the second method is recommended, because otherwise after a reboot of the attacker system, the echo responses 
are reactivated, resulting in a lifelock of the backdoor. (TODO)


## Installing the backdoor on the target system

First, the file `booty.sh`, which is responsible for the automatic start of the backdoor even after a reboot of the target system must be adjusted.
The path to the `pydoor.py` on the target system must be added at `DIR` and the IP of the attacker system must be added at `ATTACKER`.
Then the files `pydoor.py`, `booty.sh` and `install.sh` can be transferred to the target system.
The backdoor is then activated by executing

```
sudo ./install.sh 
```


## Connecting to the backdoor and executing commands

In order to connect to the active backdoor, run 

```
sudo ./handler.py
```

on the attacker system.

The current working directory on the target system can be changed via `cd`.
All other commands are directly executed.
The connection can be closed by calling `exit`.
