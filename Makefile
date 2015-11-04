VERSION = "1.8.14"
TOOLS = django.py inkscape.py favicon.py
TOOLS_WAF = "$(PWD)/django.py,$(PWD)/inkscape.py,$(PWD)/favicon.py"

.PHONY = all

all: waf

waf-src:
	wget "https://waf.io/waf-$(VERSION).tar.bz2" -nc -O "waf-$(VERSION).tar.bz2"
	tar -xf "waf-$(VERSION).tar.bz2"
	mv "waf-$(VERSION)" waf-src
	rm "waf-$(VERSION).tar.bz2"

waf: waf-src $(TOOLS)
	(cd waf-src; ./waf-light --tools=$(TOOLS_WAF))
	cp waf-src/waf ./

clean:
	rm -rf waf waf-src
