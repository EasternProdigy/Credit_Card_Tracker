"""v1 bring-up card: single source of truth for the schematic and PCB generators.

Every IC pin number comes from design/pinmaps/<part>.md (datasheet + page cited there).
Values come from docs/03_schematic_spec.md and the Nordic QFN48 config-1 reference
(datasheet v1.0 Fig. 180 / Table 87). Dev-board additions (jumpers, PPK2 breaks,
test pads, DNP trims) are marked dev=True.

Net naming: names from design/netlist.yaml are kept. Dev-board splits add:
  V5_CHG   charger input after the Qi->charger 0R (V5_RX is the Qi side)
  VCHG     charger output before the charger->cell 0R (VCELL is the cell side)
  VBAT     LDO input after the PPK2 battery break (VCELL is the cell side)
  VDD_NRF  nRF supply after the PPK2 3.3 V break (VDD_3V3 is the LDO side)
  nCHG_MCU, VBAT_SENSE_MCU: MCU side of the signal 0R links
PGND == GND (netlist note). PACK_NEG == GND (system ground after the FETs).
"""

PROJECT = 'card_v1'

SHEETS = [  # (file stem, title)
    ('qi_rx', 'A: Qi receiver (BQ51003)'),
    ('charger', 'B: Charger (BQ25101)'),
    ('battery_protect', 'C: Cell, protection, PPK2 battery break'),
    ('power_sense', 'D: LDO, battery sense, PPK2 3.3 V break'),
    ('mcu', 'E: nRF54L15 QFN48 (Nordic config 1)'),
    ('rf_antenna', 'F: Nordic 50 ohm match + IFA L-match'),
    ('debug_nfc', 'G: SWD, test pads, NFC (DNP)'),
]

# ---------------------------------------------------------------- custom symbols
# pin: (number, name, electrical type, side L/R/T/B)
CUSTOM_SYMBOLS = {
    'BQ51003YFP': dict(ref='U', fp='Package_BGA:Texas_DSBGA-28_1.9x3mm_Layout4x7_P0.4mm',
        ds='https://www.ti.com/lit/ds/symlink/bq51003.pdf', pins=[
        ('B3', 'AC1', 'passive', 'L'), ('B4', 'AC1', 'passive', 'L'),
        ('B1', 'AC2', 'passive', 'L'), ('B2', 'AC2', 'passive', 'L'),
        ('C4', 'BOOT1', 'passive', 'L'), ('C1', 'BOOT2', 'passive', 'L'),
        ('E4', 'COMM1', 'open_collector', 'L'), ('E1', 'COMM2', 'open_collector', 'L'),
        ('E3', 'CLAMP1', 'open_collector', 'L'), ('E2', 'CLAMP2', 'open_collector', 'L'),
        ('G1', 'ILIM', 'passive', 'L'), ('F2', 'FOD', 'input', 'L'),
        ('C2', 'RECT', 'power_out', 'R'), ('C3', 'RECT', 'passive', 'R'),
        ('D1', 'OUT', 'power_out', 'R'), ('D2', 'OUT', 'passive', 'R'),
        ('D3', 'OUT', 'passive', 'R'), ('D4', 'OUT', 'passive', 'R'),
        ('F4', 'CHG', 'open_collector', 'R'), ('F1', 'TS-CTRL', 'input', 'R'),
        ('G4', 'AD', 'input', 'R'), ('F3', 'AD-EN', 'output', 'R'),
        ('G3', 'EN1', 'input', 'R'), ('G2', 'EN2', 'input', 'R'),
        ('A1', 'PGND', 'power_in', 'B'), ('A2', 'PGND', 'power_in', 'B'),
        ('A3', 'PGND', 'power_in', 'B'), ('A4', 'PGND', 'power_in', 'B')]),
    'BQ25101YFP': dict(ref='U', fp='Package_BGA:Texas_DSBGA-6_0.95x1.488mm_Layout2x3_P0.4mm',
        ds='https://www.ti.com/lit/ds/symlink/bq25101.pdf', pins=[
        ('A2', 'IN', 'power_in', 'L'), ('B2', 'ISET', 'passive', 'L'), ('B1', 'TS', 'input', 'L'),
        ('A1', 'OUT', 'power_out', 'R'), ('C1', '~{CHG}', 'open_collector', 'R'),
        ('C2', 'VSS', 'power_in', 'B')]),
    'S-82N1BAA': dict(ref='U', fp='wallet_tracker:ABLIC_SNT-6A',
        ds='https://www.ablic.com/en/doc/datasheet/battery_protection/S82N1B_E.pdf', pins=[
        ('5', 'VDD', 'power_in', 'L'), ('1', 'PS', 'input', 'L'), ('6', 'VM', 'input', 'L'),
        ('3', 'DO', 'output', 'R'), ('2', 'CO', 'output', 'R'), ('4', 'VSS', 'power_in', 'B')]),
    'TPS7A0233PDQN': dict(ref='U', fp='Package_SON:Texas_X2SON-4_1x1mm_P0.65mm',
        ds='https://www.ti.com/lit/ds/symlink/tps7a02.pdf', pins=[
        ('4', 'IN', 'power_in', 'L'), ('3', 'EN', 'input', 'L'),
        ('1', 'OUT', 'power_out', 'R'), ('2', 'GND', 'power_in', 'B'), ('5', 'EP', 'passive', 'B')]),
    'EFC4615R': dict(ref='Q', fp='wallet_tracker:onsemi_EFCP-4_1.46x1.46mm_P0.65mm',
        ds='https://www.onsemi.com/download/data-sheet/pdf/efc4615r-d.pdf', pins=[
        ('1', 'S1', 'passive', 'L'), ('2', 'G1', 'input', 'L'),
        ('4', 'S2', 'passive', 'R'), ('3', 'G2', 'input', 'R')]),
    'nRF54L15-QFAA': dict(ref='U', fp='Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm',
        ds='nRF54L15 datasheet v1.0 (4503_018) Table 4 / Fig. 180', pins=[
        ('10', 'VDD', 'power_in', 'L'), ('22', 'VDD', 'power_in', 'L'), ('36', 'VDD', 'power_in', 'L'),
        ('47', 'VDD', 'power_in', 'L'), ('48', 'VDD', 'power_in', 'L'),
        ('46', 'DCC', 'passive', 'L'), ('45', 'DECD', 'passive', 'L'), ('43', 'DECA', 'passive', 'L'),
        ('33', 'DECRF', 'passive', 'L'),
        ('34', 'XC1', 'passive', 'L'), ('35', 'XC2', 'passive', 'L'),
        ('31', 'ANT', 'passive', 'L'), ('32', 'VSS_PA', 'passive', 'L'),
        ('25', 'SWDIO', 'bidirectional', 'L'), ('26', 'SWDCLK', 'input', 'L'), ('30', '~{RESET}', 'input', 'L'),
        ('44', 'VSS', 'power_in', 'B'), ('49', 'VSS_EP', 'power_in', 'B'),
        ('1', 'P1.00/XL1', 'bidirectional', 'R'), ('2', 'P1.01/XL2', 'bidirectional', 'R'),
        ('3', 'P1.02/NFC1', 'bidirectional', 'R'), ('4', 'P1.03/NFC2', 'bidirectional', 'R'),
        ('5', 'P1.04/AIN0', 'bidirectional', 'R'), ('6', 'P1.05/AIN1', 'bidirectional', 'R'),
        ('7', 'P1.06/AIN2', 'bidirectional', 'R'), ('8', 'P1.07/AIN3', 'bidirectional', 'R'),
        ('9', 'P1.08/EXTREF', 'bidirectional', 'R'), ('37', 'P1.09', 'bidirectional', 'R'),
        ('38', 'P1.10', 'bidirectional', 'R'), ('39', 'P1.11/AIN4', 'bidirectional', 'R'),
        ('40', 'P1.12/AIN5', 'bidirectional', 'R'), ('41', 'P1.13/AIN6', 'bidirectional', 'R'),
        ('42', 'P1.14/AIN7', 'bidirectional', 'R'),
        ('11', 'P2.00', 'bidirectional', 'R'), ('12', 'P2.01', 'bidirectional', 'R'),
        ('13', 'P2.02', 'bidirectional', 'R'), ('14', 'P2.03', 'bidirectional', 'R'),
        ('15', 'P2.04', 'bidirectional', 'R'), ('16', 'P2.05', 'bidirectional', 'R'),
        ('17', 'P2.06', 'bidirectional', 'R'), ('18', 'P2.07/SWO', 'bidirectional', 'R'),
        ('19', 'P2.08', 'bidirectional', 'R'), ('20', 'P2.09', 'bidirectional', 'R'),
        ('21', 'P2.10', 'bidirectional', 'R'),
        ('23', 'P0.00', 'bidirectional', 'R'), ('24', 'P0.01', 'bidirectional', 'R'),
        ('27', 'P0.02', 'bidirectional', 'R'), ('28', 'P0.03', 'bidirectional', 'R'),
        ('29', 'P0.04', 'bidirectional', 'R')]),
    'Wurth_760308101309': dict(ref='L', fp='wallet_tracker:Wurth_760308101309_Lands',
        ds='https://www.we-online.com/en/components/products/WE-WPCC-RECEIVER', pins=[
        ('1', '1', 'passive', 'L'), ('2', '2', 'passive', 'R')]),
    'IFA_Printed': dict(ref='AE', fp='wallet_tracker:IFA_2G4_arm20_h6', ds='sims/antenna_floorplan.py',
        pins=[('1', 'FEED', 'passive', 'L'), ('2', 'SHORT', 'passive', 'R')]),
}

# ---------------------------------------------------------------- footprints
FP = {
    'R0201': 'Resistor_SMD:R_0201_0603Metric', 'R0402': 'Resistor_SMD:R_0402_1005Metric',
    'R0603': 'Resistor_SMD:R_0603_1608Metric',
    'C0201': 'Capacitor_SMD:C_0201_0603Metric', 'C0402': 'Capacitor_SMD:C_0402_1005Metric',
    'C0603': 'Capacitor_SMD:C_0603_1608Metric',
    'L0201': 'Inductor_SMD:L_0201_0603Metric', 'L0603': 'Inductor_SMD:L_0603_1608Metric',
    'TP': 'TestPoint:TestPoint_Pad_D1.0mm', 'TPRF': 'wallet_tracker:TestPoint_Pad_D0.6mm',
    'HDR2': 'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',
    'SWD': 'Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD',
    'JST2': 'Connector_JST:JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal',
    'TABS': 'wallet_tracker:Battery_Tabs_2x3mm',
    'NETTIE': 'NetTie:NetTie-2_SMD_Pad0.5mm',
    'X2016': 'Crystal:Crystal_SMD_2016-4Pin_2.0x1.6mm', 'X2012': 'Crystal:Crystal_SMD_2012-2Pin_2.0x1.2mm',
}

# ---------------------------------------------------------------- components
# dict(ref, sheet, sym, value, fp, pins{pin:net}, dnp, mpn, src, dev)
# sym: 'Device:R' etc. or 'custom:<name>'
C = []
def add(ref, sheet, sym, value, fp, pins, dnp=False, mpn='', src='', dev=False):
    if fp is None: fp = CUSTOM_SYMBOLS[sym.split(':')[1]]['fp']
    C.append(dict(ref=ref, sheet=sheet, sym=sym, value=value, fp=FP.get(fp, fp), pins=pins,
                  dnp=dnp, mpn=mpn, src=src, dev=dev))

def R(ref, sh, v, a, b, fp='R0402', **k): add(ref, sh, 'Device:R', v, fp, {'1': a, '2': b}, **k)
def Cap(ref, sh, v, a, b, fp='C0402', **k): add(ref, sh, 'Device:C', v, fp, {'1': a, '2': b}, **k)
def Ind(ref, sh, v, a, b, fp='L0201', **k): add(ref, sh, 'Device:L', v, fp, {'1': a, '2': b}, **k)
def TP(ref, sh, net, fp='TP'): add(ref, sh, 'Connector:TestPoint', net, fp, {'1': net}, dev=True,
                                   src='v1 dev board: test pad')
SPEC = 'docs/03_schematic_spec.md'
TIQI = 'TI SLUSBC8C Fig.32 / sec 9.2'
NORD = 'Nordic nRF54L15 DS v1.0 Fig.180/Table 87'

# ---- A: Qi receiver ------------------------------------------------------
S = 'qi_rx'
add('L1', S, 'custom:Wurth_760308101309', '10uH Qi RX coil', 'wallet_tracker:Wurth_760308101309_Lands',
    {'1': 'COIL1', '2': 'AC2'}, mpn='Wurth 760308101309', src=SPEC)
Cap('C1a', S, '100nF 50V X7R', 'COIL1', 'AC1', 'C0603', src=SPEC + ' (v1: 0603, Dwayne)')
Cap('C1b', S, '100nF 50V X7R', 'COIL1', 'AC1', 'C0603', src=SPEC + ' (v1: 0603)')
Cap('C1c', S, '33nF 50V X7R', 'COIL1', 'AC1', 'C0603', src=SPEC + ' bench trim')
Cap('C1d', S, 'DNP 50V X7R', 'COIL1', 'AC1', 'C0603', dnp=True, dev=True, src='v1 trim footprint')
Cap('C2a', S, '2.2nF 50V C0G', 'AC1', 'AC2', 'C0603', src=SPEC)
Cap('C2b', S, '330pF 50V C0G', 'AC1', 'AC2', 'C0603', src=SPEC)
Cap('C2c', S, 'DNP 50V C0G', 'AC1', 'AC2', 'C0603', dnp=True, dev=True, src='v1 trim footprint')
add('U1', S, 'custom:BQ51003YFP', 'BQ51003YFPR', None, {
    'B3': 'AC1', 'B4': 'AC1', 'B1': 'AC2', 'B2': 'AC2', 'C4': 'BOOT1', 'C1': 'BOOT2',
    'E4': 'COMM1', 'E1': 'COMM2', 'E3': 'CLAMP1', 'E2': 'CLAMP2', 'G1': 'ILIM', 'F2': 'FOD',
    'C2': 'VRECT', 'C3': 'VRECT', 'D1': 'V5_RX', 'D2': 'V5_RX', 'D3': 'V5_RX', 'D4': 'V5_RX',
    'F4': 'RXCHG', 'F1': 'TS_RX', 'G4': 'GND', 'F3': None, 'G3': 'GND', 'G2': 'GND',
    'A1': 'GND', 'A2': 'GND', 'A3': 'GND', 'A4': 'GND'}, mpn='TI BQ51003YFPR', src='design/pinmaps/BQ51003.md')
Cap('C3', S, '10nF 25V X7R', 'BOOT1', 'AC1', src=TIQI)
Cap('C4', S, '10nF 25V X7R', 'BOOT2', 'AC2', src=TIQI)
Cap('C5', S, '22nF 25V X7R', 'COMM1', 'AC1', src=SPEC)
Cap('C6', S, '22nF 25V X7R', 'COMM2', 'AC2', src=SPEC)
Cap('C7', S, '470nF 25V X5R', 'CLAMP1', 'AC1', src=TIQI + ' p.5 (0.47uF)')
Cap('C8', S, '470nF 25V X5R', 'CLAMP2', 'AC2', src=TIQI + ' p.5 (0.47uF)')
for r in ('C9a', 'C9b', 'C9c'):
    Cap(r, S, '2.2uF 16V X5R', 'VRECT', 'GND', src=SPEC)
Cap('C10', S, '100nF 25V X7R', 'VRECT', 'GND', src=SPEC)
Cap('C11', S, '4.7uF 10V X5R', 'V5_RX', 'GND', src=SPEC)
Cap('C11b', S, '100nF 25V X7R', 'V5_RX', 'GND', src=SPEC + ' (+100 nF on OUT)')
R('R1', S, '1.5k 1%', 'ILIM', 'FOD', src='SLUSBC8C p.28: R1+RFOD=1.70k -> IMAX 154 mA (1.55k is not E96; rev 0.6)')
R('RFOD', S, '200R 1%', 'FOD', 'GND', src='SLUSBC8C p.28 (TI 196R), calibrate')
R('RFOD2', S, 'DNP', 'FOD', 'GND', dnp=True, src='SLUSBC8C p.28: 2 RFOD footprints')
R('ROS1', S, '20k 1%', 'VRECT', 'FOD', src='SLUSBC8C p.28 default')
R('ROS2', S, 'DNP', 'V5_RX', 'FOD', dnp=True, src='SLUSBC8C p.28 (open)')
R('R_TS', S, '10k 1%', 'TS_RX', 'GND', src='SLUSBC8C p.5: no NTC -> 10k')
R('JP1', S, '0R', 'V5_RX', 'V5_CHG', 'R0603', dev=True, src='v1: Qi->charger section link')
for r, n in (('TP1', 'VRECT'), ('TP2', 'V5_RX'), ('TP3', 'AC1'), ('TP4', 'AC2'), ('TP5', 'RXCHG')):
    TP(r, S, n)

# ---- B: charger ----------------------------------------------------------
S = 'charger'
add('U2', S, 'custom:BQ25101YFP', 'BQ25101YFPR', None,
    {'A2': 'V5_CHG', 'B2': 'ISET', 'B1': 'NTC', 'A1': 'VCHG', 'C1': 'nCHG', 'C2': 'GND'},
    mpn='TI BQ25101YFPR', src='design/pinmaps/BQ25101.md')
Cap('C12', S, '1uF 10V X5R', 'V5_CHG', 'GND', src=SPEC)
Cap('C13', S, '1uF 10V X5R', 'VCHG', 'GND', src=SPEC + ' (10 V part, spec min 6.3 V)')
R('R2', S, '2.05k 1%', 'ISET', 'GND', src='KISET 135/2.05k = 66 mA')
add('TH1', S, 'Device:Thermistor_NTC', '10k B3380 NTC', 'R0402', {'1': 'NTC', '2': 'GND'},
    mpn='Murata NCP15XH103F03RC', src=SPEC + ' (v1: on-board 0402; v2: thin film on cell)')
R('R_TSD', S, 'DNP 10k', 'NTC', 'GND', dnp=True, dev=True, src='BQ25101 p.3: 10k to VSS disables NTC')
R('JP2', S, '0R', 'VCHG', 'VCELL', 'R0603', dev=True, src='v1: charger->cell section link')
for r, n in (('TP6', 'V5_CHG'), ('TP7', 'VCHG'), ('TP8', 'nCHG'), ('TP9', 'NTC')):
    TP(r, S, n)

# ---- C: cell + protection ------------------------------------------------
S = 'battery_protect'
add('J1', S, 'Connector_Generic:Conn_01x02', 'Cell (JST SH)', 'JST2', {'1': 'VCELL', '2': 'BT_NEG'},
    dev=True, mpn='JST SM02B-SRSS-TB', src='v1: optional battery connector')
add('BT1', S, 'Connector_Generic:Conn_01x02', 'Cell tabs', 'TABS', {'1': 'VCELL', '2': 'BT_NEG'},
    dev=True, src='Grepow GRP0849049 tab lands')
add('U3', S, 'custom:S-82N1BAA', 'S-82N1BAA-I6T1U7', None,
    {'5': 'PROT_VDD', '1': 'PS_PIN', '6': 'PROT_VM', '3': 'DO_GATE', '2': 'CO_GATE', '4': 'BT_NEG'},
    mpn='ABLIC S-82N1BAA-I6T1U7', src='design/pinmaps/S-82N1B.md')
R('R5', S, '330R', 'VCELL', 'PROT_VDD', src=SPEC)
Cap('C29', S, '100nF 10V X7R', 'PROT_VDD', 'BT_NEG', src=SPEC)
R('R6', S, '2k', 'PROT_VM', 'GND', src=SPEC + ' (PACK_NEG = GND)')
R('R_PS', S, '0R', 'PS_PIN', 'BT_NEG', dev=True, src='S-82N1B.md: PS active high, tie to VSS')
add('Q1', S, 'custom:EFC4615R', 'EFC4615R-TR', None,
    {'1': 'BT_NEG', '2': 'DO_GATE', '3': 'CO_GATE', '4': 'GND'},
    mpn='onsemi EFC4615R-TR', src='design/pinmaps/EFC4615R.md')
R('JP3', S, '0R', 'VCELL', 'VBAT', 'R0603', dev=True, src='v1: PPK2 battery break (remove to measure)')
add('J2', S, 'Connector_Generic:Conn_01x02', 'PPK2 BAT', 'HDR2', {'1': 'VCELL', '2': 'VBAT'}, dnp=True,
    dev=True, src='PPK2 ammeter: VIN=pin1, VOUT=pin2, with JP3 removed')
for r, n in (('TP10', 'VCELL'), ('TP11', 'BT_NEG'), ('TP12', 'VBAT'), ('TP13', 'PS_PIN'),
             ('TP14', 'DO_GATE'), ('TP15', 'CO_GATE')):
    TP(r, S, n)

# ---- D: supply + sense ---------------------------------------------------
S = 'power_sense'
add('U4', S, 'custom:TPS7A0233PDQN', 'TPS7A0233PDQNR', None,
    {'4': 'VBAT', '3': 'VBAT', '1': 'VDD_3V3', '2': 'GND', '5': 'GND'},
    mpn='TI TPS7A0233PDQNR', src='design/pinmaps/TPS7A02.md')
Cap('C14', S, '1uF 10V X5R', 'VBAT', 'GND', src=SPEC)
Cap('C15', S, '4.7uF 10V X5R', 'VDD_3V3', 'GND', src=SPEC)
R('R3', S, '10M 1%', 'VBAT', 'VBAT_SENSE', src=SPEC)
R('R4', S, '10M 1%', 'VBAT_SENSE', 'GND', src=SPEC)
Cap('C16', S, '100nF 10V X7R', 'VBAT_SENSE', 'GND', src=SPEC)
R('JP4', S, '0R', 'VDD_3V3', 'VDD_NRF', 'R0603', dev=True, src='v1: PPK2 3.3 V break (remove to measure)')
add('J3', S, 'Connector_Generic:Conn_01x02', 'PPK2 3V3', 'HDR2', {'1': 'VDD_3V3', '2': 'VDD_NRF'},
    dnp=True, dev=True, src='PPK2 ammeter: VIN=pin1, VOUT=pin2, with JP4 removed')
R('JP5', S, '0R', 'VBAT_SENSE', 'VBAT_SENSE_MCU', dev=True, src='v1: sense->MCU link')
for r, n in (('TP16', 'VDD_3V3'), ('TP17', 'VDD_NRF'), ('TP18', 'VBAT_SENSE')):
    TP(r, S, n)

# ---- E: nRF54L15 QFN48 config 1 -------------------------------------------
S = 'mcu'
u5 = {'10': 'VDD_NRF', '22': 'VDD_NRF', '36': 'VDD_NRF', '47': 'VDD_NRF', '48': 'VDD_NRF',
      '46': 'DCC', '45': 'DECD', '43': 'DECA', '33': 'DECA', '34': 'XC1', '35': 'XC2',
      '31': 'RF_NRF', '32': 'GND', '25': 'SWDIO', '26': 'SWDCLK', '30': 'nRESET_IC',
      '44': 'GND', '49': 'GND', '1': 'XL1', '2': 'XL2', '3': 'NFC1', '4': 'NFC2',
      '5': 'VBAT_SENSE_MCU', '6': 'nCHG_MCU', '7': 'P1_06', '18': 'SWO', '23': 'P0_00', '24': 'P0_01'}
for p in ('8', '9', '37', '38', '39', '40', '41', '42', '11', '12', '13', '14', '15', '16', '17',
          '19', '20', '21', '27', '28', '29'):
    u5[p] = None
add('U5', S, 'custom:nRF54L15-QFAA', 'nRF54L15-QFAA', None, u5, mpn='Nordic nRF54L15-QFAA-R7',
    src='design/pinmaps/nRF54L15_QFN48.md')
Cap('C17', S, '10uF 6.3V X5R', 'VDD_NRF', 'GND', 'C0402', src=NORD + ' C3')
Cap('C21', S, '100nF X7R', 'VDD_NRF', 'GND', 'C0201', src=NORD + ' C10 (pins 47/48)')
Cap('C20', S, '100nF X7R', 'VDD_NRF', 'GND', 'C0201', src=NORD + ' C4 (pin 10)')
Cap('C22', S, '100nF X7R', 'VDD_NRF', 'GND', 'C0201', src=NORD + ' C7 (pin 22)')
Cap('C23', S, '100nF X7R', 'VDD_NRF', 'GND', 'C0201', src=NORD + ' C8 (pin 36)')
Ind('L2', S, '4.7uH 120mA', 'DCC', 'DECD', 'L0603', src=NORD + ' L1 (v1 0603, Dwayne)')
Cap('C18', S, '2.2uF X6T', 'DECD', 'GND', 'C0201', src=NORD + ' C1')
add('FB1', S, 'Device:FerriteBead_Small', '120R@100MHz', 'L0201', {'1': 'DECD', '2': 'DECA'},
    src=NORD + ' FB1')
Cap('C19', S, '2.2uF X6T', 'DECA', 'GND', 'C0201', src=NORD + ' C2')
Cap('C24', S, '10nF X7R', 'DECA', 'GND', 'C0201', src=NORD + ' C12')
Cap('C30', S, '2.2nF X7R', 'DECA', 'GND', 'C0201', src=NORD + ' C5')
add('Y1', S, 'Device:Crystal_GND24', '32MHz CL8pF', 'X2016', {'1': 'XC1', '3': 'XC2', '2': 'GND', '4': 'GND'},
    src=NORD + ' X2 (2016, CL 8 pF, +/-40 ppm)')
add('Y2', S, 'Device:Crystal', '32.768kHz CL9pF', 'X2012', {'1': 'XL1', '2': 'XL2'},
    src=NORD + ' X1 (2012, CL 9 pF, +/-20 ppm)')
R('R7', S, '1k 1%', 'nRESET_IC', 'nRESET', 'R0201', src=NORD + ' R1')
Cap('C31', S, '3.9pF C0G', 'nRESET_IC', 'GND', 'C0201', src=NORD + ' C13')
# NT1 removed (rev 0.6): pin 32 (VSS_PA) is GND in the netlist; the Fig. 180 topology (C25 -> pin 32 only on top,
# pin 32 -> pin 49 only under the IC) is enforced in the PCB by copper keepouts + a scripted trace (gen_pcb.py).
R('JP6', S, '0R', 'nCHG', 'nCHG_MCU', dev=True, src='v1: charger status link')

# ---- F: RF ---------------------------------------------------------------
S = 'rf_antenna'
Ind('L3', S, '2.7nH', 'RF_NRF', 'RF_A', mpn='Murata LQP03HQ2N7B02', src=NORD + ' L2')
Cap('C25', S, '1.5pF', 'RF_A', 'GND', 'C0201', mpn='Murata GJM0335C1E1R5WB01', src=NORD + ' C6')
Ind('L4', S, '3.5nH', 'RF_A', 'RF_B', mpn='Murata LQP03TN3N5B02', src=NORD + ' L3')
Cap('C26', S, '2.0pF', 'RF_B', 'GND', 'C0201', mpn='Murata GJM0335C1E2R0WB01', src=NORD + ' C9')
Ind('L5', S, '3.5nH', 'RF_B', 'RF_MATCHED', mpn='Murata LQP03TN3N5B02', src=NORD + ' L4')
Cap('C27', S, '0.3pF C0G', 'RF_MATCHED', 'GND', 'C0201', src=NORD + ' C11')
Cap('C32', S, 'DNP', 'RF_MATCHED', 'GND', 'C0201', dnp=True, src='antenna pi, first shunt (Dwayne)')
Ind('L6', S, '2.2nH', 'RF_MATCHED', 'ANT_FEED', src='sims/antenna_match.py L-match')
Cap('C28', S, '0.2pF C0G', 'ANT_FEED', 'GND', 'C0201', src='sims/antenna_match.py L-match')
add('AE1', S, 'custom:IFA_Printed', 'IFA arm 20 mm', 'wallet_tracker:IFA_2G4_arm20_h6',
    {'1': 'ANT_FEED', '2': 'GND'}, src='sims/antenna_floorplan.py (feed 6, short 3, h 6, arm 20)')
TP('TP19', S, 'ANT_FEED', 'TPRF')

# ---- G: debug + NFC ------------------------------------------------------
S = 'debug_nfc'
add('J4', S, 'Connector_Generic:Conn_02x05_Odd_Even', 'SWD 10p 1.27', 'SWD',
    {'1': 'VDD_NRF', '2': 'SWDIO', '3': 'GND', '4': 'SWDCLK', '5': 'GND', '6': 'SWO', '7': None,
     '8': None, '9': 'GND', '10': 'nRESET'}, dev=True, mpn='Cortex Debug 10-pin',
    src='ARM Cortex 10-pin debug pinout')
for r, n in (('TP20', 'SWDIO'), ('TP21', 'SWDCLK'), ('TP22', 'nRESET'), ('TP23', 'GND'), ('TP24', 'GND'),
             ('TP25', 'GND'), ('TP26', 'P0_00'), ('TP27', 'P0_01'), ('TP28', 'P1_06'), ('TP29', 'SWO')):
    TP(r, S, n)
add('J5', S, 'Connector_Generic:Conn_01x02', 'NFC ant', 'HDR2', {'1': 'NFC1', '2': 'NFC2'}, dnp=True,
    dev=True, src='NFC loop antenna pads (DNP until v2.1)')
Cap('C33', S, 'DNP', 'NFC1', 'GND', 'C0402', dnp=True, dev=True, src='NFC tuning cap, tune on bench')
Cap('C34', S, 'DNP', 'NFC2', 'GND', 'C0402', dnp=True, dev=True, src='NFC tuning cap, tune on bench')

# power flags (ERC: nets driven only through passives / connectors)
PWR_FLAGS = {'battery_protect': ['PROT_VDD', 'BT_NEG', 'GND'], 'power_sense': ['VBAT', 'VDD_NRF'],
             'charger': ['V5_CHG']}
