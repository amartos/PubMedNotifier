.PHONY: install upgrade reset

define check_config_dir
	if [ -z $${XDG_CONFIG_HOME+x} ]; then $(1) ; else $(2) ; fi
endef

install:
	@pip3 install --user -r requirements.txt
	@$(call check_config_dir, mkdir -p ~/.config/pubmednotifier, mkdir -p '$$XDG_CONFIG_HOME'/pubmednotifier)
	@$(call check_config_dir, cp -n config_example ~/.config/pubmednotifier/config, cp -n config_example '$$XDG_CONFIG_HOME'/pubmednotifier/config)
	@echo "Installation complete."
	@echo "Now please fill configure the script with your e-mail and queries. See README for details."

upgrade: install
	@git pull
	@pip3 install --upgrade --user -r requirements.txt

reset:
	@rm ~/.local/share/pubmednotifier/history
