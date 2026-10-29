# Third-party software and source availability

The application code is MIT licensed. Bundled libraries retain their own licenses.

- Python 3.12.14: PSF and associated notices; https://www.python.org/downloads/release/python-31214/
- Qt / PySide6 Essentials / Shiboken 6.10.0: we use the LGPL v3 option for dynamically loaded Qt Core, Gui, Widgets and Svg. License texts accompany the release in THIRD_PARTY_LICENSES. No Qt WebEngine, QML or commercial-only modules are used.
- NumPy 2.2.6, lxml 5.4.0, openpyxl 3.1.5, et_xmlfile 2.0.0 and Pillow 11.3.0: their distribution license/notice files accompany the release.
- PyInstaller 6.16.0: GPL v2-or-later with the bootloader distribution exception. This does not change the application's MIT license.

Qt/PySide6 source corresponding to this release:

- https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.10.0-src/
- https://download.qt.io/archive/qt/6.10/6.10.0/submodules/
- https://code.qt.io/cgit/qt/qtbase.git/tree/?h=v6.10.0
- https://code.qt.io/cgit/qt/qtsvg.git/tree/?h=v6.10.0
- https://code.qt.io/cgit/pyside/pyside-setup.git/tree/?h=v6.10.0
- Qt third-party attribution information: https://doc.qt.io/qt-6.10/licenses-used-in-qt.html

Qt is dynamically loaded from the release's _internal/PySide6 directory. Recipients may replace these shared libraries with compatible modified versions and rebuild the application from the supplied source. Reverse engineering for debugging modifications to LGPL-covered components is not prohibited. The build specification and instructions are included in the public repository. Do not delete the bundled license directory when redistributing the program.

The icon SVG is original project artwork, supplied under the project MIT license. The application is not affiliated with Haag-Streit, LENSTAR or The Qt Company. It does not include EyeSuite software, human/animal research records, or a bundled research dataset.
