#!/bin/bash
echo "Building site-scanner.deb..."

# Создаём структуру пакета
mkdir -p site-scanner/DEBIAN
mkdir -p site-scanner/opt/site-scanner
mkdir -p site-scanner/usr/local/bin

# Копируем файлы
cp scanner.py site-scanner/opt/site-scanner/
cp wordlist.txt site-scanner/opt/site-scanner/
cp requirements.txt site-scanner/opt/site-scanner/

# Создаём исполняемый файл
cat > site-scanner/usr/local/bin/site-scanner << 'EOF'
#!/bin/bash
cd /opt/site-scanner
python3 scanner.py "$@"
EOF
chmod +x site-scanner/usr/local/bin/site-scanner

# Создаём control файл
cat > site-scanner/DEBIAN/control << EOF
Package: site-scanner
Version: 0.2-1
Section: net
Priority: optional
Architecture: all
Depends: python3, python3-pip
Maintainer: Your Name <your@email.com>
Description: Fast console network scanner
 A Python-based tool for quick network diagnostics
 including ping checks, port scanning, and HTTP
 header analysis.

EOF

# Собираем пакет
dpkg-deb --build site-scanner
echo "Done: site-scanner.deb"
