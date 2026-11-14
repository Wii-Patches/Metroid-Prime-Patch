#!/usr/bin/env python3
"""Emit the Riivolution XML from the prebuilt features.

    python3 tools/build.py            # writes riivolution/<ID>.xml

Only for the single-DOL discs: Riivolution patches memory once at boot, so it
cannot reach the game DOLs Metroid Prime Trilogy's front end loads later.  There
are no Gecko codes: the patch lives in the same low memory (0x80001800-0x80003000)
as a Gecko code handler.  The patched-DOL path (tools/patcher.py, the GUI) uses
the very same ops.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import features
from regions import REGIONS

ROOT = os.path.join(HERE, '..')


def riivolution_xml(region):
    r = REGIONS[region]
    out = ['<!-- %s: patches by quatric -->' % r['label'],
           '<wiidisc version="1" root="/">',
           '  <id game="%s" version="%d" />' % (region, r['version']),
           '  <options>',
           '    <section name="%s">' % r['label']]
    for name in features.FEATURES:
        if features.available(name, region):
            out.append('      <option name="%s" default="1">' % features.TITLES[name])
            out.append('        <choice name="Enabled"><patch id="%s" /></choice>' % name)
            out.append('      </option>')
    out += ['    </section>', '  </options>']
    for name in features.FEATURES:
        if not features.available(name, region):
            continue
        f = features.load(name, region)
        out.append('  <patch id="%s">' % name)
        out += ['    ' + e for e in f.memory_elements()]
        out.append('  </patch>')
    out.append('</wiidisc>')
    return '\n'.join(out) + '\n'


def main():
    out = os.path.join(ROOT, 'riivolution')
    os.makedirs(out, exist_ok=True)
    for region in REGIONS:
        path = os.path.join(out, region + '.xml')
        if '_' in region or region.startswith('R3M'):
            if os.path.exists(path):
                os.remove(path)                 # Trilogy: see the module docstring
            continue
        with open(path, 'w') as fh:
            fh.write(riivolution_xml(region))
        print(region, REGIONS[region]['label'])


if __name__ == '__main__':
    main()
