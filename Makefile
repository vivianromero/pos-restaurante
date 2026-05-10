PACKAGE_NAME=pos-system
VERSION=1.0.0
ARCH=amd64
BUILD_DIR=debian_pkg
INSTALL_DIR=$(BUILD_DIR)/opt/pos-system

all: deb

prepare:
	rm -rf $(BUILD_DIR)

	mkdir -p $(BUILD_DIR)/DEBIAN
	mkdir -p $(INSTALL_DIR)
	mkdir -p $(BUILD_DIR)/lib/systemd/system
	mkdir -p debian_pkg/etc/nginx/sites-available
	mkdir -p $(BUILD_DIR)/etc/pos-system
	mkdir -p debian_pkg/usr/share/doc/pos-system

    # Copiar ejecutable
	cp -r dist/backend/* $(BUILD_DIR)/opt/pos-system/
	cp pos-system.service \
	   $(BUILD_DIR)/lib/systemd/system/pos-system.service
    
    # Copiar TODO el onedir
	cp -r dist/backend/* $(INSTALL_DIR)/
	cp packaging/pos-system-nginx.conf debian_pkg/etc/nginx/sites-available/pos-system
	cp pos-system.service $(BUILD_DIR)/lib/systemd/system/pos-system.service
	cp packaging/pos-system.env $(BUILD_DIR)/etc/pos-system/pos-system.env

    # Copiar documentación
	cp LEEME.txt debian_pkg/usr/share/doc/pos-system/LEEME.txt
	chmod 644 debian_pkg/usr/share/doc/pos-system/LEEME.txt

    # Permisos ejecutable
	chmod +x $(INSTALL_DIR)/backend
	chmod 644 $(BUILD_DIR)/lib/systemd/system/pos-system.service

    # Service
	cp pos-system.service $(BUILD_DIR)/lib/systemd/system/


    # Scripts Debian
	cp packaging/postinst $(BUILD_DIR)/DEBIAN/
	cp packaging/prerm $(BUILD_DIR)/DEBIAN/
	cp packaging/postrm $(BUILD_DIR)/DEBIAN/
	cp packaging/control $(BUILD_DIR)/DEBIAN/


    # Copiar ficheros de control y scripts
	chmod 755 $(BUILD_DIR)/DEBIAN/postinst
	chmod 755 $(BUILD_DIR)/DEBIAN/prerm
	chmod 755 $(BUILD_DIR)/DEBIAN/postrm

deb: prepare
	dpkg-deb --build $(BUILD_DIR) $(PACKAGE_NAME)_$(VERSION)_$(ARCH).deb

clean:
	rm -rf $(BUILD_DIR)
	rm -f $(PACKAGE_NAME)_$(VERSION)_$(ARCH).deb
