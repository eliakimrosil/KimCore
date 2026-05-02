# Maintainer: Master Kim <eliakimrosil@example.com>
pkgname=kimcore
pkgver=1.0.0
pkgrel=1
pkgdesc="Modern CPU core power manager for Master Kim"
arch=('any')
url="https://github.com/eliakimrosil/KimCore"
license=('MIT')
depends=('python' 'python-customtkinter' 'tk')
makedepends=('git')
source=('main.py' 'run.sh' 'KimCore.desktop')
sha256sums=('SKIP' 'SKIP' 'SKIP')

package() {
    # Install main script
    install -Dm755 main.py "$pkgdir/usr/share/kimcore/main.py"
    
    # Install runner script
    install -Dm755 run.sh "$pkgdir/usr/bin/kimcore"
    
    # Install desktop entry
    install -Dm644 KimCore.desktop "$pkgdir/usr/share/applications/kimcore.desktop"
    
    # Fix the runner script to use system python and correct path
    sed -i 's|.*venv/bin/python.*|/usr/bin/python /usr/share/kimcore/main.py|' "$pkgdir/usr/bin/kimcore"
    
    # Fix desktop entry exec path
    sed -i 's|Exec=.*|Exec=/usr/bin/kimcore|' "$pkgdir/usr/share/applications/kimcore.desktop"
}
