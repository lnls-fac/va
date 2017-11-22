develop:
	cd vaca-beamcharge; sudo ./setup.py develop; cd systemd; sudo make install-services
	cd vaca-ps; sudo ./setup.py develop; cd systemd; sudo make install-services
	sudo systemctl daemon-reload

install:
	cd vaca-beamcharge; sudo ./setup.py install; cd systemd; sudo make install-services
	cd vaca-ps; sudo ./setup.py install; cd systemd; sudo make install-services
	sudo systemctl daemon-reload
