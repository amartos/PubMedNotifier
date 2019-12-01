.PHONY: install upgrade reset

install:
	@pip3 install --user -r requirements.txt
	@mkdir -p ~/.cache/pubmednotifier
	@mkdir -p ~/.config/pubmednotifier
	@mkdir -p ~/.local/share/pubmednotifier
	@cp -n config_example ~/.config/pubmednotifier/config

upgrade: install
	@git pull
	@pip3 install --upgrade --user -r requirements.txt

reset:
	@rm ~/.local/share/pubmednotifier/history
