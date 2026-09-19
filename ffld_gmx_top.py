#!/usr/bin/env python3
import sys
import re
import os


def parse_atomtypes(lines):
    atomtypes = []
    name2idx = {}
    started = False
    header_re = re.compile(r'^\s*atom\s+type\s+vdw\s+symbol\s+charge')
    for ln in lines:
        if header_re.match(ln):
            started = True
            continue
        if started:
            if ln.strip() == '' or ln.startswith('---') or ln.startswith(' Stretch'):
                if atomtypes:
                    break
                else:
                    continue
            parts = ln.split()
            if len(parts) < 8:
                continue
            atom_name = parts[0]
            type_num = parts[1]
            vdw = parts[2]
            symbol = parts[3]
            try:
                charge = float(parts[4])
                sigma = float(parts[5])
                epsilon = float(parts[6])
            except ValueError:
                continue
            idx = len(atomtypes) + 1
            name2idx[atom_name] = idx
            atomtypes.append(dict(atom_name=atom_name, type_num=type_num,
                                  vdw=vdw, symbol=symbol, charge=charge,
                                  sigma=sigma, epsilon=epsilon, index=idx))
    return atomtypes, name2idx


def parse_stretch(lines):
    result = []
    started = False
    header_re = re.compile(r'^\s*Stretch\s+k\s+r0')
    for ln in lines:
        if header_re.match(ln):
            started = True
            continue
        if started:
            if ln.strip() == '' or ln.startswith(' Bending'):
                if result:
                    break
                else:
                    continue
            parts = ln.split()
            if len(parts) < 4:
                continue
            a1, a2 = parts[0], parts[1]
            try:
                k = float(parts[2])
                r0 = float(parts[3])
            except ValueError:
                continue
            result.append(dict(a1=a1, a2=a2, k=k, r0=r0))
    return result


def parse_bending(lines):
    result = []
    started = False
    header_re = re.compile(r'^\s*Bending\s+k\s+theta0')
    for ln in lines:
        if header_re.match(ln):
            started = True
            continue
        if started:
            if ln.strip() == '' or ln.startswith(' proper Torsion'):
                if result:
                    break
                else:
                    continue
            parts = ln.split()
            if len(parts) < 5:
                continue
            a1, a2, a3 = parts[0], parts[1], parts[2]
            try:
                k = float(parts[3])
                theta = float(parts[4])
            except ValueError:
                continue
            result.append(dict(a1=a1, a2=a2, a3=a3, k=k, theta=theta))
    return result


def parse_proper_torsion(lines):
    result = []
    started = False
    header_re = re.compile(r'^\s*proper Torsion\s+V1\s+V2\s+V3\s+V4')
    for ln in lines:
        if header_re.match(ln):
            started = True
            continue
        if started:
            if ln.strip() == '' or ln.startswith(' improper Torsion'):
                if result:
                    break
                else:
                    continue
            parts = ln.split()
            if len(parts) < 8:
                continue
            a1, a2, a3, a4 = parts[0], parts[1], parts[2], parts[3]
            try:
                v1 = float(parts[4])
                v2 = float(parts[5])
                v3 = float(parts[6])
                v4 = float(parts[7])
            except ValueError:
                continue
            result.append(dict(a1=a1, a2=a2, a3=a3, a4=a4,
                               v1=v1, v2=v2, v3=v3, v4=v4))
    return result


def parse_improper_torsion(lines):
    result = []
    started = False
    header_re = re.compile(r'^\s*improper Torsion\s+V2\s+quality')
    for ln in lines:
        if header_re.match(ln):
            started = True
            continue
        if started:
            if ln.strip() == '':
                continue
            parts = ln.split()
            if len(parts) < 5:
                continue
            a1, a2, a3, a4 = parts[0], parts[1], parts[2], parts[3]
            try:
                v2 = float(parts[4])
            except ValueError:
                continue
            result.append(dict(a1=a1, a2=a2, a3=a3, a4=a4, v2=v2))
    return result


ELEM_MASS = {
    'H':  1.00800,  'He': 4.00260,
    'Li': 6.94100,  'Be': 9.01218,  'B':  10.81000, 'C':  12.01100,
    'N':  14.00670, 'O':  15.99940, 'F':  18.99840, 'Ne': 20.17970,
    'Na': 22.98977, 'Mg': 24.30500, 'Al': 26.98154, 'Si': 28.08550,
    'P':  30.97376, 'S':  32.06000, 'Cl': 35.45300, 'Ar': 39.94800,
    'K':  39.09830, 'Ca': 40.08000, 'Sc': 44.95590, 'Ti': 47.88000,
    'V':  50.94150, 'Cr': 51.99600, 'Mn': 54.93800, 'Fe': 55.84700,
    'Co': 58.93320, 'Ni': 58.69000, 'Cu': 63.54600, 'Zn': 65.38000,
    'Ga': 69.73500, 'Ge': 72.59000, 'As': 74.92160, 'Se': 78.96000,
    'Br': 79.90400, 'Kr': 83.79800, 'Rb': 85.46780, 'Sr': 87.62000,
    'Y':  88.90590, 'Zr': 91.22000, 'Nb': 92.90640, 'Mo': 95.94000,
    'Tc': 98.00000, 'Ru': 101.0700, 'Rh': 102.9055, 'Pd': 106.4200,
    'Ag': 107.8680, 'Cd': 112.4100, 'In': 114.8200, 'Sn': 118.6900,
    'Sb': 121.7500, 'Te': 127.6000, 'I':  126.9045, 'Xe': 131.2930,
    'Cs': 132.9054, 'Ba': 137.3300, 'La': 138.9100, 'Ce': 140.1200,
    'Pr': 140.9077, 'Nd': 144.2400, 'Pm': 145.0000, 'Sm': 150.3600,
    'Eu': 151.9600, 'Gd': 157.2500, 'Tb': 158.9254, 'Dy': 162.5000,
    'Ho': 164.9304, 'Er': 167.2600, 'Tm': 168.9342, 'Yb': 173.0400,
    'Lu': 174.9670, 'Hf': 178.4900, 'Ta': 180.9479, 'W':  183.8500,
    'Re': 186.2070, 'Os': 190.2000, 'Ir': 192.2200, 'Pt': 195.0800,
    'Au': 196.9665, 'Hg': 200.5900, 'Tl': 204.3700, 'Pb': 207.2000,
    'Bi': 208.9804, 'Po': 209.0000, 'At': 210.0000, 'Rn': 222.0000,
    'Fr': 223.0000, 'Ra': 226.0000, 'Ac': 227.0300, 'Th': 232.0400,
    'Pa': 231.0359, 'U':  238.0300, 'Np': 237.0000, 'Pu': 244.0000,
    'Am': 243.0600, 'Cm': 247.0000, 'Bk': 247.0000, 'Cf': 251.0000,
    'Es': 252.0000, 'Fm': 257.0000, 'Md': 258.0000, 'No': 259.0000,
    'Lr': 266.0000, 'Rf': 267.0000, 'Db': 268.0000, 'Sg': 269.0000,
    'Bh': 270.0000, 'Hs': 277.0000, 'Mt': 278.0000, 'Ds': 281.0000,
    'Rg': 282.0000, 'Cn': 285.0000, 'Nh': 286.0000, 'Fl': 289.0000,
    'Mc': 290.0000, 'Lv': 293.0000, 'Ts': 294.0000, 'Og': 294.0000,
}

ELEM_ZNUM = {
    'H':  1,   'He': 2,
    'Li': 3,   'Be': 4,   'B':  5,   'C':  6,
    'N':  7,   'O':  8,   'F':  9,   'Ne': 10,
    'Na': 11,  'Mg': 12,  'Al': 13,  'Si': 14,
    'P':  15,  'S':  16,  'Cl': 17,  'Ar': 18,
    'K':  19,  'Ca': 20,  'Sc': 21,  'Ti': 22,
    'V':  23,  'Cr': 24,  'Mn': 25,  'Fe': 26,
    'Co': 27,  'Ni': 28,  'Cu': 29,  'Zn': 30,
    'Ga': 31,  'Ge': 32,  'As': 33,  'Se': 34,
    'Br': 35,  'Kr': 36,  'Rb': 37,  'Sr': 38,
    'Y':  39,  'Zr': 40,  'Nb': 41,  'Mo': 42,
    'Tc': 43,  'Ru': 44,  'Rh': 45,  'Pd': 46,
    'Ag': 47,  'Cd': 48,  'In': 49,  'Sn': 50,
    'Sb': 51,  'Te': 52,  'I':  53,  'Xe': 54,
    'Cs': 55,  'Ba': 56,  'La': 57,  'Ce': 58,
    'Pr': 59,  'Nd': 60,  'Pm': 61,  'Sm': 62,
    'Eu': 63,  'Gd': 64,  'Tb': 65,  'Dy': 66,
    'Ho': 67,  'Er': 68,  'Tm': 69,  'Yb': 70,
    'Lu': 71,  'Hf': 72,  'Ta': 73,  'W':  74,
    'Re': 75,  'Os': 76,  'Ir': 77,  'Pt': 78,
    'Au': 79,  'Hg': 80,  'Tl': 81,  'Pb': 82,
    'Bi': 83,  'Po': 84,  'At': 85,  'Rn': 86,
    'Fr': 87,  'Ra': 88,  'Ac': 89,  'Th': 90,
    'Pa': 91,  'U':  92,  'Np': 93,  'Pu': 94,
    'Am': 95,  'Cm': 96,  'Bk': 97,  'Cf': 98,
    'Es': 99,  'Fm': 100, 'Md': 101, 'No': 102,
    'Lr': 103, 'Rf': 104, 'Db': 105, 'Sg': 106,
    'Bh': 107, 'Hs': 108, 'Mt': 109, 'Ds': 110,
    'Rg': 111, 'Cn': 112, 'Nh': 113, 'Fl': 114,
    'Mc': 115, 'Lv': 116, 'Ts': 117, 'Og': 118,
}


def elem_of(atom_name):
    m = re.match(r'^([A-Za-z]+)', atom_name)
    if not m:
        return None
    return m.group(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_to_itp.py input.txt [output.itp]")
        sys.exit(1)

    in_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(in_path)[0] + '.itp'

    with open(in_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    atomtypes, name2idx = parse_atomtypes(lines)
    if not atomtypes:
        print("Error: atom type section not found.")
        sys.exit(1)

    stretches = parse_stretch(lines)
    bendings = parse_bending(lines)
    propers = parse_proper_torsion(lines)
    impropers = parse_improper_torsion(lines)

    def name2index(name):
        if name in name2idx:
            return name2idx[name]
        m = re.match(r'^([A-Za-z]+)(\d+)$', name)
        if m:
            return int(m.group(2))
        return None

    molecule_name = "UNK"
    type_prefix = "mm_"

    for at in atomtypes:
        elem = elem_of(at['atom_name'])
        if elem is None:
            print("Error: cannot parse element from atom name '%s' (atom index %d)."
                  % (at['atom_name'], at['index']))
            sys.exit(1)
        if elem not in ELEM_MASS or elem not in ELEM_ZNUM:
            print("Error: element '%s' (from atom name '%s', atom index %d) "
                  "is not in the element table."
                  % (elem, at['atom_name'], at['index']))
            sys.exit(1)

    unique_types = {}
    for at in atomtypes:
        tname = "%s%s" % (type_prefix, at['type_num'])
        if tname not in unique_types:
            unique_types[tname] = at

    atomtypes_lines = []
    atomtypes_lines.append("; name        at.num  mass      charge    ptype  sigma(nm)   epsilon(kJ/mol)")
    for tname, at in unique_types.items():
        elem = elem_of(at['atom_name'])
        mass = ELEM_MASS[elem]
        znum = ELEM_ZNUM[elem]
        sigma_nm = at['sigma'] / 10.0
        eps_kj = at['epsilon'] * 4.184
        atomtypes_lines.append("%-11s %6d  %8.5f  %8.4f  A  %10.6f  %12.6f" % (
            tname, znum, mass, at['charge'], sigma_nm, eps_kj))
    atomtypes_section = "\n".join(atomtypes_lines)

    atoms_lines = []
    atoms_lines.append("; nr  type        resnr  residue  atom  cgnr  charge     mass")
    for at in atomtypes:
        idx = at['index']
        tname = "%s%s" % (type_prefix, at['type_num'])
        elem = elem_of(at['atom_name'])
        mass = ELEM_MASS[elem]
        q = at['charge']
        atoms_lines.append("%5d  %-11s %5d  %-7s %-5s %5d  %10.6f  %8.5f" % (
            idx, tname, 1, molecule_name, at['atom_name'], idx, q, mass))
    atoms_section = "\n".join(atoms_lines)

    bonds_lines = []
    bonds_lines.append("; ai  aj  funct  b0(nm)  kb(kJ/mol/nm^2)")
    for b in stretches:
        i = name2index(b['a1'])
        j = name2index(b['a2'])
        if i is None or j is None:
            continue
        kb = b['k'] * 2.0 * 4.184 * 100.0
        b0 = b['r0'] / 10.0
        bonds_lines.append("%5d %5d   1  %10.6f  %12.4f" % (i, j, b0, kb))
    bonds_section = "\n".join(bonds_lines)

    angles_lines = []
    angles_lines.append("; ai  aj  ak  funct  theta0(deg)  ktheta(kJ/mol/rad^2)")
    for b in bendings:
        i = name2index(b['a1'])
        j = name2index(b['a2'])
        k = name2index(b['a3'])
        if None in (i, j, k):
            continue
        ktheta = b['k'] * 2.0 * 4.184
        angles_lines.append("%5d %5d %5d   1  %10.4f  %12.4f" % (
            i, j, k, b['theta'], ktheta))
    angles_section = "\n".join(angles_lines)

    dihedrals_lines = []
    dihedrals_lines.append("; ai  aj  ak  al  funct  C1  C2  C3  C4(kJ/mol)")
    pair_set = set()
    for t in propers:
        i = name2index(t['a1'])
        j = name2index(t['a2'])
        k = name2index(t['a3'])
        l = name2index(t['a4'])
        if None in (i, j, k, l):
            continue
        pair_set.add((min(i, l), max(i, l)))
        c1 = t['v1'] * 4.184
        c2 = t['v2'] * 4.184
        c3 = t['v3'] * 4.184
        c4 = t['v4'] * 4.184
        dihedrals_lines.append("%5d %5d %5d %5d   5  %12.6f  %12.6f  %12.6f  %12.6f" % (
            i, j, k, l, c1, c2, c3, c4))
    dihedrals_section = "\n".join(dihedrals_lines)

    impropers_lines = []
    impropers_lines.append("; Periodic improper dihedrals (type 4)")
    impropers_lines.append("; ai  aj  ak  al  funct  phi0  fc(kJ/mol)  n")
    for t in impropers:
        i = name2index(t['a1'])
        j = name2index(t['a2'])
        k = name2index(t['a3'])
        l = name2index(t['a4'])
        if None in (i, j, k, l):
            continue
        fc = t['v2'] * 4.184 / 2.0
        impropers_lines.append("%5d %5d %5d %5d   4  180.000  %10.6f   2" % (
            i, j, k, l, fc))
    impropers_section = "\n".join(impropers_lines)

    pairs_lines = []
    pairs_lines.append("; ai  aj  funct")
    for (i, j) in sorted(pair_set):
        pairs_lines.append("%5d %5d   1" % (i, j))
    pairs_section = "\n".join(pairs_lines)

    itp_content = """[ atomtypes ]
%s

[ moleculetype ]
; name  nrexcl
%s  3

[ atoms ]
%s

[ bonds ]
%s

[ angles ]
%s

[ dihedrals ]
%s

[ dihedrals ]
%s

[ pairs ]
%s
""" % (atomtypes_section, molecule_name, atoms_section, bonds_section,
       angles_section, dihedrals_section, impropers_section, pairs_section)

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(itp_content)

    top_path = os.path.splitext(out_path)[0] + '.top'
    top_content = """;Generated topology file

[ defaults ]
; nbfunc  comb-rule  gen-pairs  fudgeLJ  fudgeQQ
1         3          yes        0.5      0.5

#include "%s"

[ system ]
SYS

[ molecules ]
%s   1
""" % (os.path.basename(out_path), molecule_name)

    with open(top_path, 'w', encoding='utf-8') as f:
        f.write(top_content)

    print("Generated itp file: %s" % out_path)
    print("Generated top file: %s" % top_path)


if __name__ == '__main__':
    main()
