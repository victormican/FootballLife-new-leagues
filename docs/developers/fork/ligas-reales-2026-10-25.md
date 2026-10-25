# Ligas reales (2026-10-25)

Regla: una liga de nuestro world se convierte en la liga real de un pais. Sus clubes son los
**reales del juego de ese pais** (team id < 71.578) y, si no llega, se completan con **nuestros
genericos** (71.578+) hasta el numero de equipos. Nada se crea: solo se renombra y se reasigna.
Formato del nombre: `<liga real> (<pais>) <n equipos>`.

Herramienta: `tools/real_league.py --country <Country.bin> --name "<nombre>" --teams 10 --reg <reg>`.
`--reg` es la liga del world que se convierte (si se omite, elige la que mas clubes de ese pais
tenga; ojo: hoy solo es fiable con `--reg`).

## Hechas

| liga | reg | cid | clubes | reales | genericos |
|---|---|---|---|---|---|
| HNL (Croacia) 10 | 11 | 130 | 10 | 2 | 8 |
| Premijer Liga (Bosnia y Herzegovina) 10 | 49 | 131 | 10 | 0 | 10 |
| Premier League (Egipto) 10 | 60 | 132 | 10 | 1 | 9 |
| LigaPro (Ecuador) 10 | 61 | 134 | 10 | 4 | 6 |
| ISL (India) 10 | 62 | 133 | 10 | 1 | 9 |
| Liga Profesional (Argentina) 10 | 76 | 135 | 10 | 10 | 0 |
| Liga 1 (Peru) 10 | 93 | 142 | 10 | 3 | 7 |
| J1 League (Japon) 10 | 94 | 136 | 10 | 10 | 0 |
| Liga BetPlay (Colombia) 10 | 384 | 161 | 10 | 10 | 0 |

## Arreglado de paso

- **Oceania** (reg 196, cid 91): volvio a sus **11 selecciones OFC** (mi primer intento de
  `real_league.py` la dejo en 8; el fallo era elegir liga sin `--reg`, y se corrigio reponiendo
  las entradas desde `nations.py`).

## Pendiente

- Resto de paises con clubes reales (Brasil, Inglaterra, Espana, Italia, Francia ya tienen liga del
  juego: **no se tocan**) y los de 2-9 clubes reales.
- Segundas divisiones con los reales que sobren.
- Slots libres: 250 - 133 - 23 = **94** ligas mas.
