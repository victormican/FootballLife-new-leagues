# Nombres corruptos en el world file y la liga belga (2026-11-06)

## 1. El bug: 35 nombres doble-codificados

Síntoma: la liga belga salía como `Bǟ�'�Ń?Tǟ�?s�'��lgica CPL` — y lo mismo otras 34.

Causa: para añadir las líneas `pool` y la de Concacaf usé `Get-Content -Raw` + `WriteAllText` de
PowerShell 5.1. **`Get-Content -Raw` sin `-Encoding` lee el fichero como ANSI**, así que los acentos
UTF-8 se leyeron mal y se volvieron a escribir doble-codificados.

Arreglo: `tools/fix_world_names.py` compara el `name=` de cada línea (`league` y `ccup`) con el
nombre de su regulación en las tablas y **reescribe el de la tabla** si no coincide.

```
lineas corregidas: 35
  league 368  BÃƒÆ’Ã‚Â©lgica CPL  -> Bélgica CPL
  ...
```

Regla para el futuro: **el world file solo se toca con Python** (`io.open(..., encoding="utf-8")`),
nunca con `Get-Content -Raw`.

## 2. La liga belga

Había dos cosas:

- La **Primera real** (cid 111: Anderlecht, Brujas, Amberes…) **no tenía línea**: sus 16 clubes
  estaban en las tablas pero no se listaban.
- La única línea "belga" era la **genérica** `Bélgica CPL` (cid 106, 20 clubes inventados) y con
  `slot=-1`, es decir oculta.

Añadida la línea de la real (es un split: el total es la regulación 115, `type 9`):

```
league 115 cid=111 region=8 country=162 conf=2 slot=248 tier=1 promote=0 demote=0 \
       clubs=16 legs=2 kickoff=99 name=Jupiler Pro League
```

`clubs=16` porque son las entradas reales (la regulación declara 18). `check_world`: 153 ligas,
136 slots, **0 errores**.

## 3. Lo que esto destapó: ligas reales sin listar

Comparando el release con el world file por nombre, hay **510 ligas del release con 10 clubes o
más sin línea** en el mundo. La mayoría son divisiones amateur/regionales (Torneo Federal C 720,
French Regional 435, Regional Amateur 250…), pero hay **competiciones reales**:

| liga | clubes | estado |
|---|---|---|
| **Sky Bet Championship** (2.ª inglesa) | 24 | **falta** (están League One y League Two, no la Championship) |
| **Major League Soccer** | 30 | preparada (cid 40 con 30 entradas) pero sin listar |
| Bolivian Second Division | 42 | falta |
| Peruvian Copa Perú | 38 | falta |
| Turkish Super Amateur League | 32 | falta |
| Libyan Premier League | 27 | falta |
| Uruguayan First Amateur Division | 27 | falta |

(La "Colombian Third Division" y la "Argentine Premier Division" del release sí están, pero con
nuestros nombres: Primera C Colombia y Liga Profesional de Fútbol.)

## 4. Siguiente paso

Revisar una a una las ligas reales que faltan y listarlas con el mismo patrón que Bélgica:
línea `league` con el `reg` de la fase total, `clubs` igual a las entradas y un slot libre.
Empezar por **Sky Bet Championship** (24 clubes) y **MLS** (30, con su formato).
