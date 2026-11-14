# U4: TI TPS7A0233 (v1 DQN X2SON-4 / v2 YCH DSBGA-4)
Source: TI SBVS277C (Sep 2022), Table 5-1 "Pin Functions: DQN, DBV" (p.3), Table 5-2 "Pin Functions: YCH" (p.4), Recommended Operating Conditions (CIN 1 uF, COUT 1-22 uF), package drawings DQN0004A and YCH0004 (0.4 mm max height).

| Functional name | DQN pin (v1) | YCH ball (v2) |
|---|---|---|
| OUT | 1 | A2 |
| GND | 2 + thermal pad | B2 |
| EN | 3 | B1 |
| IN | 4 | A1 |

- EN has an internal pull-down; tying EN to IN is correct.
- Height: 0.4 mm max for both packages. Orderable: TPS7A0233PDQNR, TPS7A0233PYCHR.
- Layout note (p.~24): no thermal via directly under the DQN thermal pad.
