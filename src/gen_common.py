"""Shared pieces of the Classic Controller and GameCube controller builders for Metroid Prime series."""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
import asm
from ops import Hook

REGION_SITES = {
    'R3IJ01': dict(
        sigettype=0x8049B3F8,
        stb=0x804886CC,
        addi=0x804886D0,
        bl=0x804882F8,
        b=0x804882FC,
        probe=0x804A6F30,
        ring=0x80487D44,
        smp_reg=30,
        chan_reg=29,
        index_reg=28,
        stb_op=0x987E0036,
        addi_op=0x381C0001,
        bl_op=0x4BFFEF19,
        b_op=0x48000008,
    ),
    'R32J01': dict(
        sigettype=0x8049B280,
        stb=0x80488554,
        addi=0x80488558,
        bl=0x80488180,
        b=0x80488184,
        probe=0x804A6DB8,
        ring=0x80487BCC,
        smp_reg=30,
        chan_reg=29,
        index_reg=28,
        stb_op=0x987E0036,
        addi_op=0x381C0001,
        bl_op=0x4BFFEF19,
        b_op=0x48000008,
    ),
    'RM3E01': dict(
        sigettype=0x804EADD0,
        stb=0x804D9C1C,
        addi=0x804D9C20,
        bl=0x804D97F0,
        b=0x804D97F4,
        probe=0x804F66B8,
        ring=0x804D923C,
        smp_reg=28,
        chan_reg=30,
        index_reg=29,
        stb_op=0x987C0036,
        addi_op=0x381D0001,
        bl_op=0x4BFFEF2D,
        b_op=0x48000008,
    ),
    'RM3P01': dict(
        sigettype=0x804ECADC,
        stb=0x804DB928,
        addi=0x804DB92C,
        bl=0x804DB4FC,
        b=0x804DB500,
        probe=0x804F83C4,
        ring=0x804DAF48,
        smp_reg=28,
        chan_reg=30,
        index_reg=29,
        stb_op=0x987C0036,
        addi_op=0x381D0001,
        bl_op=0x4BFFEF2D,
        b_op=0x48000008,
    ),
    # Metroid Prime Trilogy (USA) - Main & Games
    'R3ME01': dict(
        sigettype=0x8049AB8C,
        stb=0x80487E60,
        addi=0x80487E64,
        bl=0x80487A54,
        b=0x80487A58,
        probe=0x804A6718,
        ring=0x804874A0,
        smp_reg=30,
        chan_reg=29,
        index_reg=28,
        stb_op=0x987E0036,
        addi_op=0x381C0001,
        bl_op=0x4BFFEF19,
        b_op=0x48000008,
    ),
    'R3ME01_mp1': dict(
        sigettype=0x803CC288,
        stb=0x803BD850,
        addi=0x803BD854,
        bl=0x803BD444,
        b=0x803BD448,
        probe=0x803D7E0C,
        ring=0x803BCE90,
        smp_reg=30,
        chan_reg=29,
        index_reg=28,
        stb_op=0x987E0036,
        addi_op=0x381C0001,
        bl_op=0x4BFFEF19,
        b_op=0x48000008,
    ),
    'R3ME01_mp2': dict(
        sigettype=0x803FEFA0,
        stb=0x803F0638,
        addi=0x803F063C,
        bl=0x803F022C,
        b=0x803F0230,
        probe=0x8040AB24,
        ring=0x803EFC78,
        smp_reg=30,
        chan_reg=29,
        index_reg=28,
        stb_op=0x987E0036,
        addi_op=0x381C0001,
        bl_op=0x4BFFEF19,
        b_op=0x48000008,
    ),
    'R3ME01_mp3': dict(
        sigettype=0x804ECBE0,
        stb=0x804D9EB4,
        addi=0x804D9EB8,
        bl=0x804D9AA8,
        b=0x804D9AAC,
        probe=0x804F8764,
        ring=0x804D94F4,
        smp_reg=30,
        chan_reg=29,
        index_reg=28,
        stb_op=0x987E0036,
        addi_op=0x381C0001,
        bl_op=0x4BFFEF19,
        b_op=0x48000008,
    ),
    # Metroid Prime Trilogy (Europe) - Main & Games
    'R3MP01': dict(
        sigettype=0x8049BCF8,
        stb=0x80488924,
        addi=0x80488928,
        bl=0x80487F2C,
        b=0x80487F30,
        probe=0x804A779C,
        ring=0x804879F0,
        smp_reg=30,
        chan_reg=29,
        index_reg=28,
        stb_op=0x987E0036,
        addi_op=0x381C0001,
        bl_op=0x4BFFE9B9,
        b_op=0x48000010,
        ring_op=0x881A013B,
        ring_src='gc_synth_pal_mpt.s',
    ),
    'R3MP01_mp1': dict(
        sigettype=0x803CD84C,
        stb=0x803BE76C,
        addi=0x803BE770,
        bl=0x803BDD74,
        b=0x803BDD78,
        probe=0x803D92E8,
        ring=0x803BD838,
        smp_reg=30,
        chan_reg=29,
        index_reg=28,
        stb_op=0x987E0036,
        addi_op=0x381C0001,
        bl_op=0x4BFFE9B9,
        b_op=0x48000010,
        ring_op=0x881A013B,
        ring_src='gc_synth_pal_mpt.s',
    ),
    'R3MP01_mp2': dict(
        sigettype=0x8040312C,
        stb=0x803F411C,
        addi=0x803F4120,
        bl=0x803F3724,
        b=0x803F3728,
        probe=0x8040EBC8,
        ring=0x803F31E8,
        smp_reg=30,
        chan_reg=29,
        index_reg=28,
        stb_op=0x987E0036,
        addi_op=0x381C0001,
        bl_op=0x4BFFE9B9,
        b_op=0x48000010,
        ring_op=0x881A013B,
        ring_src='gc_synth_pal_mpt.s',
    ),
    'R3MP01_mp3': dict(
        sigettype=0x804ED81C,
        stb=0x804DA448,
        addi=0x804DA44C,
        bl=0x804D9A50,
        b=0x804D9A54,
        probe=0x804F92B8,
        ring=0x804D9514,
        smp_reg=30,
        chan_reg=29,
        index_reg=28,
        stb_op=0x987E0036,
        addi_op=0x381C0001,
        bl_op=0x4BFFE9B9,
        b_op=0x48000010,
        ring_op=0x881A013B,
        ring_src='gc_synth_pal_mpt.s',
    ),
}

# Wii Remote / Nunchuk button bits (WPAD)
WM = dict(WM_LEFT=0x0001, WM_RIGHT=0x0002, WM_DOWN=0x0004, WM_UP=0x0008, WM_PLUS=0x0010,
          WM_2=0x0100, WM_1=0x0200, WM_B=0x0400, WM_A=0x0800, WM_MINUS=0x1000,
          WM_Z=0x2000, WM_C=0x4000, WM_HOME=0x8000)
# Classic Controller button bits (WPAD)
CC = dict(CC_UP=0x0001, CC_LEFT=0x0002, CC_ZR=0x0004, CC_X=0x0008, CC_A=0x0010, CC_Y=0x0020,
          CC_B=0x0040, CC_ZL=0x0080, CC_R=0x0200, CC_PLUS=0x0400, CC_HOME=0x0800,
          CC_MINUS=0x1000, CC_L=0x2000, CC_DOWN=0x4000, CC_RIGHT=0x8000)
# GameCube pad button bits (PAD)
PAD = dict(PAD_LEFT=0x0001, PAD_RIGHT=0x0002, PAD_DOWN=0x0004, PAD_UP=0x0008, PAD_Z=0x0010,
           PAD_R=0x0020, PAD_L=0x0040, PAD_A=0x0100, PAD_B=0x0200, PAD_X=0x0400, PAD_Y=0x0800,
           PAD_START=0x1000)

PTR_X = 0.00065
PTR_Y = -0.00070


def read(name):
    out = []
    for line in open(os.path.join(HERE, name)).read().split('\n'):
        out.append(read(line.split()[1]) if line.startswith('#include ') else line)
    return '\n'.join(out)


def decode_branch(word, at):
    li = word & 0x03FFFFFC
    if li & 0x02000000:
        li -= 0x04000000
    return (at + li) & 0xFFFFFFFF


def sites(region, dol):
    cfg = REGION_SITES[region]
    out = {k: cfg[k] for k in ('stb', 'addi', 'bl', 'b')}
    w = {k: struct.unpack('>I', dol.read(a, 4))[0] for k, a in out.items()}
    if w['stb'] != cfg['stb_op'] or w['addi'] != cfg['addi_op']:
        raise SystemExit('%s: sample hook sites are 0x%08X 0x%08X (expected 0x%08X 0x%08X)' % (
            region, w['stb'], w['addi'], cfg['stb_op'], cfg['addi_op']))
    if (w['bl'] >> 26) != 18 or not (w['bl'] & 1) or (w['b'] >> 26) != 18 or (w['b'] & 1):
        raise SystemExit('%s: pointer hook sites are not bl / b' % region)
    return out, w


def pointer_source(marker, prologue='', epilogue=''):
    return (prologue + read('pointer.s').replace('MARKER', str(marker)).replace('PTR_X', repr(PTR_X)).replace(
        'PTR_Y', repr(PTR_Y)) + epilogue)


def hook(site, orig, base, source, syms, consts, note):
    words = asm.words(asm.assemble(read('macros.s') + source, base, syms, consts)) + [0]
    return Hook(site, orig, words, base, note=note), (len(words) * 4 + 15) & ~15


def gc_extra_sites(region, dol):
    cfg = REGION_SITES[region]
    out = {k: cfg[k] for k in ('probe', 'ring')}
    w = {k: struct.unpack('>I', dol.read(a, 4))[0] for k, a in out.items()}
    exp_ring = cfg.get('ring_op', 0x881F010F)
    if w['probe'] != 0x9421FFF0 or w['ring'] != exp_ring:
        raise SystemExit('%s: probe / ring sites are 0x%08X 0x%08X (expected 0x%08X 0x%08X)' % (
            region, w['probe'], w['ring'], 0x9421FFF0, exp_ring))
    return out, w



# The poller's own state (zero in the injected section): see gc_poll.s.
PSTATE = 0x80002FE0
PSTATE_SIZE = 0x20

# OSDisableInterrupts / OSEnableInterrupts / OSRestoreInterrupts, back to back in every DOL
OS_INTR = [0x7C6000A6, 0x5464045E, 0x7C800124, 0x54638FFE, 0x4E800020,
           0x7C6000A6, 0x60648000, 0x7C800124, 0x54638FFE, 0x4E800020,
           0x2C030000, 0x7C8000A6, 0x4182000C, 0x60858000, 0x48000008,
           0x5485045E, 0x7CA00124, 0x54838FFE, 0x4E800020]


def _w(dol, a):
    return struct.unpack('>I', dol.read(a, 4))[0]


def si_syms(region, dol):
    """SIGetType, the si state block and the interrupt helpers, read out of SIGetType itself.

    SIGetType opens with `stwu r1,-0x20(r1) ; mflr r0 ; stw r0,0x24(r1)`, calls
    OSDisableInterrupts at +0x18, and loads the address of si's type cache with
    `lis r5,hi` (+0x1C) / `addi r5,r5,lo` (+0x2C).  The type cache is at +0x18 in si's
    state block (+0 busy channel, +4 SIPOLL shadow).
    """
    fn = REGION_SITES[region]['sigettype']
    head = [_w(dol, fn + 4 * i) for i in range(3)]
    if head != [0x9421FFE0, 0x7C0802A6, 0x90010024]:
        raise SystemExit('%s: 0x%08X is not SIGetType' % (region, fn))
    bl, hi, lo = _w(dol, fn + 0x18), _w(dol, fn + 0x1C), _w(dol, fn + 0x2C)
    if (bl >> 26) != 18 or not bl & 1 or (hi >> 16) != 0x3CA0 or (lo >> 16) != 0x38A5:
        raise SystemExit('%s: SIGetType at 0x%08X does not have the expected shape' % (region, fn))
    dis = decode_branch(bl, fn + 0x18)
    if [_w(dol, dis + 4 * i) for i in range(len(OS_INTR))] != OS_INTR:
        raise SystemExit('%s: 0x%08X is not OSDisableInterrupts' % (region, dis))
    imm = lo & 0xFFFF
    types = (((hi & 0xFFFF) << 16) + (imm - 0x10000 if imm & 0x8000 else imm)) & 0xFFFFFFFF
    return {'SIGETTYPE': fn, 'SIBASE': types - 0x18, 'OSDISABLE': dis, 'OSRESTORE': dis + 0x28,
            'PSTATE': PSTATE}



def _kpad_read(region, dol):
    """KPADRead's first instruction (`stwu r1,-N(r1)`), from the ring hook site."""
    a = REGION_SITES[region]['ring']
    while _w(dol, a) >> 16 != 0x9421:
        a -= 4
    return a


def frame_site(region, dol):
    """The per-frame hook site in the game's input update.

    The game calls KPADRead from exactly one function (Trilogy Europe through the
    SDK's `li r6,0 ; li r7,0 ; b KPADReadEx` wrapper).  That function opens with
    `mr rN,r3 ; bl <its event pump>` at +0x30/+0x34 in every DOL; the hook replaces
    the instruction after the call (+0x38), where r0 and r3-r12 are free.
    """
    k = _kpad_read(region, dol)
    if _w(dol, k - 4) == 0x48000004 and _w(dol, k - 8) == 0x38E00000 and _w(dol, k - 12) == 0x38C00000:
        k -= 12
    calls = []
    for off, base, size, idx in dol.secs:
        if idx >= 7:
            continue
        ws = struct.unpack('>%dI' % (size // 4), bytes(dol.data[off:off + size]))
        for i, w in enumerate(ws):
            if w >> 26 == 18 and w & 1 and decode_branch(w, base + 4 * i) == k:
                calls.append(base + 4 * i)
    if len(calls) != 1:
        raise SystemExit('%s: KPADRead (0x%08X) has %d callers' % (region, k, len(calls)))
    f = calls[0]
    while _w(dol, f) >> 16 != 0x9421:
        f -= 4
    mr, bl, site = _w(dol, f + 0x30), _w(dol, f + 0x34), _w(dol, f + 0x38)
    if mr & 0xFFE0FFFF != 0x7C601B78 or bl >> 26 != 18 or not bl & 1 or site >> 26 not in (34, 48):
        raise SystemExit('%s: input update at 0x%08X does not have the expected shape' % (region, f))
    return f + 0x38, site


def _lis_addi(ws, base_reg=None):
    """The first `lis rX,hi ; ... ; addi rY,rX,lo` value in `ws`."""
    vals = _lis_addis(ws, base_reg)
    return vals[0] if vals else None


def _lis_addis(ws, base_reg=None):
    """Every `lis rX,hi ; ... ; addi rY,rX,lo` value in `ws`, in order."""
    out = []
    for i, w in enumerate(ws):
        if w >> 26 != 15:
            continue
        reg = (w >> 21) & 31
        if base_reg is not None and reg != base_reg:
            continue
        for x in ws[i + 1:i + 8]:
            if x >> 26 == 14 and (x >> 16) & 31 == reg:
                imm = x & 0xFFFF
                out.append((((w & 0xFFFF) << 16) + (imm - 0x10000 if imm & 0x8000 else imm)) & 0xFFFFFFFF)
                break
    return out


def wpad(region, dol):
    """WPAD's per-channel control block table, the status offset in a block (-1 = no Wii
    Remote) and the connect callback offset.

    WPADProbe loads the table (`lis/addi`), indexes it by channel and reads the status
    with `lwz rS,off(rB) ; cmpwi rS,-1`.  The connect callback sits 0x18 before the
    status; WPADSetConnectCallback, the one function of the table that swaps a word
    there (`lwz ; stw`), confirms it.  (Trilogy Europe's game registers through
    KPADSetConnectCallback: WPAD's callback is then KPAD's handler, which records the
    connection and calls the game.)
    """
    probe = REGION_SITES[region]['probe']
    ws = [_w(dol, probe + 4 * i) for i in range(24)]
    table = _lis_addi(ws)
    status = None
    for a, b in zip(ws, ws[1:]):
        if a >> 26 == 32 and b & 0xFFE0FFFF == 0x2C00FFFF and (b >> 16) & 31 == (a >> 21) & 31:
            status = a & 0xFFFF
            break
    if table is None or status is None:
        raise SystemExit('%s: WPADProbe at 0x%08X: table %r status %r' % (region, probe, table, status))
    cb = status - 0x18
    setters = []
    for off, base, size, idx in dol.secs:
        if idx >= 7:
            continue
        cw = struct.unpack('>%dI' % (size // 4), bytes(dol.data[off:off + size]))
        for k in range(len(cw) - 40):
            if cw[k] >> 16 != 0x9421 or table not in _lis_addis(cw[k:k + 40]):
                continue
            for a, b in zip(cw[k:k + 40], cw[k + 1:k + 40]):
                if b == 0x4E800020:
                    break
                if a >> 26 == 32 and b >> 26 == 36 and a & 0x001FFFFF == b & 0x001FFFFF and a & 0xFFFF == cb:
                    setters.append(base + 4 * k)
    if len(setters) != 1:
        raise SystemExit('%s: WPADSetConnectCallback (swap at +0x%X) found %d times' % (region, cb, len(setters)))
    return dict(WTBL=table), dict(WSTAT=status, WCB=cb)


def wpad_get_info(region, dol):
    """WPADGetInfoAsync: the one call in the game's input update (besides KPADRead)
    to a function that indexes WPAD's control-block table and reads the status.
    Returns its address and its first instruction (`stwu r1,-N(r1)`)."""
    syms, consts = wpad(region, dol)
    site, _ = frame_site(region, dol)
    f = site - 0x38
    k = _kpad_read(region, dol)
    hits = set()
    for a in range(f, f + 0x400, 4):
        w = _w(dol, a)
        if w == 0x4E800020:
            break
        if w >> 26 != 18 or not w & 1:
            continue
        t = decode_branch(w, a)
        if t == k or _w(dol, t) >> 16 != 0x9421:
            continue
        ws = [_w(dol, t + 4 * i) for i in range(24)]
        if syms['WTBL'] in _lis_addis(ws) and any(x >> 26 == 32 and x & 0xFFFF == consts['WSTAT'] for x in ws):
            hits.add(t)
    if len(hits) != 1:
        raise SystemExit('%s: WPADGetInfoAsync: %d candidates in the input update' % (region, len(hits)))
    t = hits.pop()
    return t, _w(dol, t)
