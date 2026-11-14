"""Build the GameCube controller feature for one region from src/gc_sample.s and src/pointer.s."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_common as g
from layout import GC_BASE, GC_END
from ops import Blob, Feature

JUMP = '    lis     12, LOOP_END@ha\n    addi    12, 12, LOOP_END@l\n    mtctr   12\n    bctr\n'


def build(region, dol):
    at, w = g.sites(region, dol)
    cfg = g.REGION_SITES[region]
    consts = dict(g.WM, **g.PAD)
    consts['SMP_REG'] = cfg['smp_reg']
    consts['CHAN_REG'] = cfg['chan_reg']
    consts['INDEX_REG'] = cfg['index_reg']
    if os.environ.get('MP_DEBUG'):
        consts['DEBUG'] = 1
    si = g.si_syms(region, dol)
    ops, cur = [], GC_BASE
    h, size = g.hook(at['addi'], w['addi'], cur, g.read('gc_sample.s'), si, consts,
                     'KPAD sampling callback: GameCube pad -> Wii Remote + Nunchuk sample')
    ops.append(h)
    cur += size
    target = g.decode_branch(w['b'], at['b'])
    h, size = g.hook(at['b'], w['b'], cur, g.pointer_source(2, '', JUMP), {'LOOP_END': target}, consts,
                     'KPAD read loop: pointer from the sticks')
    ops.append(h)
    cur += size
    ex, ew = g.gc_extra_sites(region, dol)
    ring_src = cfg.get('ring_src', 'gc_synth.s')
    h, size = g.hook(ex['ring'], ew['ring'], cur, g.read(ring_src), si, consts,
                     'KPAD read: no Wii Remote, so make the sample from the GameCube pad')
    ops.append(h)
    cur += size
    h, size = g.hook(ex['probe'], ew['probe'], cur, g.read('gc_probe.s'), dict(si, PROBE_BODY=ex['probe'] + 4), consts,
                     'WPADProbe: keep SI polling port 1; a GameCube pad counts as a connected controller')
    ops.append(h)
    cur += size
    fsite, forig = g.frame_site(region, dol)
    wsyms, wconsts = g.wpad(region, dol)
    h, size = g.hook(fsite, forig, cur, g.read('gc_frame.s'), dict(si, **wsyms),
                     dict(consts, DISPLACED=forig, **wconsts),
                     'game input update: poll SI port 1 every frame; a GameCube pad connects channel 0')
    ops.append(h)
    cur += size
    isite, iorig = g.wpad_get_info(region, dol)
    h, size = g.hook(isite, iorig, cur, g.read('gc_info.s'), dict(si, **wsyms),
                     dict(consts, DISPLACED=iorig, **wconsts),
                     'WPADGetInfoAsync: a full battery for the GameCube pad')
    ops.append(h)
    cur += size
    if cur > g.PSTATE:
        raise SystemExit('gc code runs into the poller state: 0x%X > 0x%X' % (cur, g.PSTATE))
    ops.append(Blob(g.PSTATE, bytes(g.PSTATE_SIZE), 'SI poller state'))
    if cur > GC_END:
        raise SystemExit('gc code overflows its window: 0x%X > 0x%X' % (cur, GC_END))
    return Feature('gc', 'GameCube controller', region, ops)
