# Select Team: flujo y reintento (2026-11-06)

## Lo observado

1. `Jugar > Liga > Nuevo` abre "Seleccionar la liga a competir" (lista a la izquierda,
   "Información de la Liga" con los equipos a la derecha).
2. **Primera entrada**: la lista del slot se construye antes de que la regulación esté
   disponible; el DLL deja la lista del juego (1 club) y al seleccionarlo el juego se cierra
   (`0x3fd2b2` / `0x161efa600`).
3. **Volver al menú principal y entrar otra vez**: el DLL ya sirve los equipos y la lista sale
   completa.

## Herramienta

`tools/select_team_retry.ps1 <hwnd> <scroll> <captura.png>`: vuelve al menú, Jugar -> Liga ->
Nuevo, se desplaza `scroll` posiciones y hace la captura. El operador mira la lista y, si trae
un solo equipo, repite (atrás -> menú -> entrar).

## Corrección pendiente

Que el DLL conteste bien en la **primera** lectura. Opciones:

1. servir la lista antes de abrir Select Team (precarga al cargar el modo), o
2. forzar un releido tras cargar la regulación (hook de carga -> invalidar la lista), o
3. que `count_hook`, si la regulación aún no está, devuelva la lista cacheada de una lectura
   anterior y marque el slot para reconstruir en la siguiente.

La 3 no ayuda en el primer arranque (no hay caché); la 1/2 son las de verdad.
