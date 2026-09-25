# openrz67-trigger

## PCB

- After any change to `pcb/kicad/*.kicad_pcb` or `*.kicad_sch`, run `pcb/kicad/tools/regen.sh`
  and commit everything it writes under `pcb/kicad/out/` (gerber/, gerber zip, BOM, pos, DRC/ERC, renders).
  The zip is tracked so the fab-ready file is always in the repo.
