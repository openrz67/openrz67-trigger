# openrz67-trigger

## PCB

- After any change to `pcb/kicad/*.kicad_pcb` or `*.kicad_sch`, run `pcb/kicad/tools/regen.sh`
  and commit everything it writes under `pcb/kicad/out/` (gerber/, gerber zip, BOM, pos, DRC/ERC, renders).
  The zip is tracked so the fab-ready file is always in the repo.

## Docs

- READMEs describe things as they are, for humans: what, how to build, how to use. No dates,
  no "was X until Y", no rejected alternatives.
- History and reasoning go in `pcb/kicad/notes/revisions.md` and `case/notes/design-history.md`.
  When a change has a "why", write it there, not in the README.
