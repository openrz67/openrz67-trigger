# Motlesing 2026-09-10: adversariell verifikasjon av review-2026-09-10.md

Metode: 6 motleser-agenter + verifikasjonsrunde på hver av dem (den runden originalen mistet på tokenkvote).
Hver rad i originalens seksjon 2 er regnet ut på nytt fra `pcb/kicad/openrz67.kicad_pcb`, `openrz67.kicad_sch`,
`openrz67.kicad_pro`, `openrz67.kicad_dru`, `openrz67.pretty/`, `openrz67.kicad_sym`, `out/gerber/`, arkivpakkene
og databladene — ikke lest ut av originalen. Verktøy: `kicad-cli` 10.0.6 (`/opt/homebrew/bin/kicad-cli`, samme binær
som `/Applications/KiCad/`) og KiCads egen `pcbnew`-Python for eksakte polygonbooleans. Datablad: ESP32-C3 DS v2.4,
ESP Hardware Design Guidelines (master, esp32c3), ESP32-C3-MINI-1 DS v2.2, TPS63031 SLVS696D, BQ25185 SLUSF65B,
TLP172AM Rev.11.0.A (Toshiba, 2026-04-07), JST ePH.pdf.

**Read-only:** ingen designfil er endret. Alle "hva skjer hvis"-tester (flyttet spor, innlagte vias, nye DRU-regler,
fjernede no-connect-flagg) er kjørt på kopier utenfor repoet. `git status` er uendret.

Denne fila **erstatter ikke** originalen; den sier hvilke rader som står, hvilke som faller, og hva som ble målt feil.
Der originalen og denne fila er uenige, gjelder denne — hvert tall her er reprodusert to ganger uavhengig.

## 1. Sammendrag

- **Ingen rad i seksjon 2 faller helt.** Alle sju identifiserer en reell egenskap ved brettet.
- **Tre fiksforslag er feil og må ikke gjennomføres som skrevet:** X2-deleren på VSYS (feil node, bryter
  strømbudsjettet i originalens §5), L-01s to GND-vias (måler 0,2610 mm hals før *og* etter — nullverdi), og
  L-01s 0,3 mm sørflytting av VCC (fysisk umulig, maks 0,170 mm).
- **Fire delpåstander er REFUTED:** «C24 er eneste 10 µF på VOUT» (C15 er også 10 µF på samme nett),
  «bare U3 er under maskedam-grensen» (USB1 pads 3–10 er på nøyaktig samme 0,098 mm, og brettets minste dam
  er 0,0655 mm ved U2/C25), «NTC-selvoppvarming kan nå knappetrykk-terskelen og felle brettet i factory mode»
  (HOT-trippen kutter varmekilden 8 K før), og originalens bevisledd for U1-04 («tabell 5-4 VOH 0,8×VDD
  spesifisert med PAD_DRIVER = 3» — tabellen har ingen slik betingelse; fotnoten sier høyimpedant last).
- **Ett nytt funn av samme klasse som seksjon 2:** J1s GPIO6-spor på F.Cu står **0,170 mm** fra AGND-pouren i to
  segmenter, altså trangere enn alt annet på brettet unntatt AGND↔GND selv — og `pcb/kicad/README.md:170-171`
  påstår eksplisitt at J1 ikke rører kameraisolasjonen. En AGND-regel skrevet som «AGND mot GND» lar den stå.
- **Originalen motsier seg selv ett sted:** linje 289 sier at arkivpakken «was not unpacked and diffed», mens
  DELTA-01s bevislinje (311) sier «diff of unzipped archive gerbers vs out/gerber». Konklusjonen holder uansett —
  diffen er nå faktisk kjørt.
- **DRC/ERC er kjørt friskt** og er bit-for-bit identisk med `out/drc.rpt` og `out/erc.rpt`. Sonefyllet i fila er
  ferskt (`--refill-zones --save-board` gir byte-identisk `.kicad_pcb`).
- **Minnenotatet om at 2026-09-08-fiksene er «uncommitted» er utdatert.** `24bc07f`, `64ef2b8`, `4550987` og
  arkiveringen `5f30622` er alle i `main`; det eneste usporede er selve review-fila.

## 2. Verdikt per rad i originalens seksjon 2

| Id | Verdikt | Hva står | Hva faller / må korrigeres |
|---|---|---|---|
| U1-01 / FE-1 | **CONFIRMED** | GPIO8 er eksplisitt no-connect i sch og har `unconnected-(U1-GPIO8-Pad14)` uten kobber i pcb. Fiks og del er riktig. | Bevis-kolonnen bør bytte kilde: HDG *anbefaler* ikke pull-up på GPIO8 spesifikt; grunnlaget er DS tabell 3-3 + HDG §1.3.10 + esptool-doket. «esptool tvinger download uavhengig» er for absolutt (HDG §1.5). Fiksen krever *to* schematic-endringer: motstand **og** fjerning av no-connect. |
| U1-02 / FE-2 | **CONFIRMED, styrket** | Pinne 18 er no-connect (`power_out`) og har ikke kobber. HDG §1.3.2 ordrett; Espressifs egen MINI-1 med samme FH4-brikke har C11 = 1 µF på pinne 18 (figur 8-1, s. 32). | «RSPI-fall 150–190 mV» er et statisk IR-fall en kondensator ikke fjerner — feil mekanisme, funnet er dekopling. C15849 er **0603**, ikke 0402. Plassen ved pad 18 er verre enn originalen tror (se §3.2). |
| U1-03 / FE-3 / PWR-02 | **Delt: «X2 ubrukt» CONFIRMED · fiksen REFUTED som skrevet** | X2/C30/C31 er ubestykket brukt: begge Arduino-pakkene på disk (3.20014 og 3.20017) har `RTC_CLK_SRC_INT_RC=y` og `PM_ENABLE` av. GPIO0/1 er de eneste frie ADC1-pinnene og er ikke strapping. | **VSYS er feil node** (oppstrøms S3 → 2,1 µA døgnet rundt, +35 % på originalens eget ≤ 6 µA-budsjett). VSYS er dessuten låst til 4,5 V med USB i. Boot-loop-en er *ikke* argumentet for en ADC. C30/C31 = 18 pF er **riktig** matchet mot X2. |
| DELTA-01 | **CONFIRMED** | Alle **fem** 2026-09-08-endringene mangler i arkivpakken, hver verifisert i `.kicad_pcb`. 4 `starved_thermal` bekreftet. BOM byte-identisk, CPL skiller i én linje (C23). | F_Cu er 2953 diff-linjer (ikke 2949); PTH.drl 19 uten tidsstempel (23 med). Av de fem via-koordinatene originalen tilskriver GPIO21 er to på nett GND, og en femte GPIO21-via er utelatt. Drill-deltaet er 10 nye / 5 fjernet / 2 flyttet. |
| L-01 | **CONFIRMED · begge fikser REFUTED** | Halsen er **0,2610 mm** konstant over 6,3 mm (x 25,75–32,06, y 0,3005–0,5615), reprodusert med to uavhengige metoder. 12 GND-vias binder østblokken; DRC 0 unconnected. | Fiks 1 (0,3 mm sør) gir **to** `shorting_items` mot S3 pad 1/2 + 2× `solder_mask_bridge`; maks lovlig flytt er **0,170 mm** → hals 0,427 mm. Fiks 2 (to GND-vias) endrer **ingenting**: hals og sonearealer identiske etter refill. |
| TPS-01 / TPS-02 | **Avstand CONFIRMED · «eneste 10 µF» REFUTED · konsekvens nedgradert** | 6,521 mm kobber U2.1 → C24.2, ingen parallell vei; nærmeste GND-via til C24s GND-pad er 2,866 mm; 0,16 mm-halsene finnes. SLVS696D §11.1 sier «must be placed as close as possible». | «6,5 mm» er *sporlengde*, ikke avstand (senter 5,064, kant 4,278). C15 er også 10 µF på VCC. `VCC` er netklasse `3v` (0,20 mm), ikke `5v`. IR-fall/varme er neglisjerbart — det som står igjen er induktans/EMI, som ikke kan lukkes uten skop. **Fiks 1 er ikke gjennomførbar**: (15,4, 6,3) er okkupert av BAT+-via og -løp. |
| L-02 | **Geometri CONFIRMED · «bare U3» REFUTED · alvorlighet nedgradert** | 0,400 − 0,200 = 0,200 kobbergap, − 2×0,051 = **0,0980 mm**, målt direkte i `out/gerber/openrz67-F_Mask.gts` (aperture D47, ti separate flash). Fiksen (margin 0,04 → dam 0,120) er aritmetisk riktig og innenfor TIs «0.05 MAX ALL AROUND». | Brettets minste dam er **0,0655 mm** (U2 pad 6 ↔ C25 pad 2, begge `SW_SYS`), og USB1 pads 3–10 ligger på samme 0,098 som U3. Det fabrikerte rev 1-settet hadde 0,0198 mm damer på samme USB1-rad og ett par sammensmeltede åpninger — JLCPCB bygde det. Risikoen er **loddebro på 0,4 mm pitch under montering**, ikke at fabben avviser fila. |

## 3. Detaljert motlesing

### 3.1 U1-01 / FE-1 — GPIO8

| Felt | Innhold |
|---|---|
| Verdikt | **CONFIRMED** |
| Schematic | `openrz67.kicad_sch:3200` `(no_connect (at 158.75 207.01) …)`. U1-instans `:5545` `(at 154.94 180.34)` rot 0 + symbolpinne 14 `GPIO8` `(at 3.81 -26.67)` = nøyaktig (158,75, 207,01). Strengen finnes én gang i fila — pinnen er **eksplisitt** NC-merket, derfor er ERC ren og vil aldri minne om funnet. |
| PCB | `openrz67.kicad_pcb:14489` pad `"14"` `(at 2.55 -0.75)`, footprint `(at 141.257 104.4195)` → brettkoordinat **(23,807, 13,669)**, net `unconnected-(U1-GPIO8-Pad14)`, netnavnet forekommer 1 gang i fila → ingen kobber. |
| Datablad | DS v2.4 tabell 3-1 «GPIO8 · Floating»; tabell 2-1 pinne 14 «At Reset: **IE**» (mot GPIO9 «IE, WPU»); tabell 3-3 «Joint download boot: GPIO2 1, GPIO8 **1**, GPIO9 0»; tabell 3-4 med `EFUSE_UART_PRINT_CONTROL = 0`: GPIO8 «Ignored». HDG tabell 5 «GPIO8 nr. 14 Reset 1», legende «1 – input enabled, in high impedance state». HDG **§1.3.10 GPIO**: «For unused pins in the high-impedance state without an internal pull-up or pull-down, it is recommended to add a pull-up or pull-down resistor …» — den dekker GPIO8 og er den HDG-hjemmelen originalen mangler. esptool-doket: «The strapping combination of GPIO8 = 0 and GPIO9 = 0 is invalid and will trigger unexpected behavior.» |
| Korreksjon til originalen | (a) «esptool via USB-Serial-JTAG tvinger download uavhengig» er for absolutt: HDG §1.5 sier «If the flash is empty, set the chip or module to Joint Download Boot mode», og at auto-download faller bort når applikasjonen slår av USB PHY — nøyaktig scenariet READMEs BOOT+EN-prosedyre skal berge, og som light sleep utløser. (b) Feilmodus er verre enn «kommer ikke inn i download»: låser pinnen lavt mens S1 holdes, er GPIO8 = 0 / GPIO9 = 0, som esptool kaller «invalid». (c) Fiksen krever at `no_connect`-flagget på `:3200` fjernes samtidig, ellers ERC-feil. |
| Kontekst | R6/R7/R8 = 10 kΩ (C25744, 0402) sitter allerede på GPIO9, CHIP_EN og GPIO2. GPIO8 er **den eneste** strapping-pinnen uten. Firmware rører ikke GPIO8 (`grep -rn "GPIO8\|GPIO_NUM_8" src/ README.md` → 0 treff), så en pull-up koster ingenting i drift. Ukoblet også i rev 1: `["PAD_NET","e579","14","","e95",0]` i `.epcb`. |
| Fiks-feasibilitet | Ikke kartlagt godt nok til å love. Originalens «pinne 17 / C29-området er ved siden av» og motlesningens første forslag «rut til pad 11» er **begge** tvilsomme: pad 11 (VDD3P3_RTC) ligger 1,50 mm unna i samme 0,5 mm-pitch-kolonne, med pad 12 og 13 imellom — et spor langs kolonnen er umulig. Nærmeste VCC-kobber er B.Cu-sporet (18,847, 12,293)→(23,727, 12,293), 1,378 mm fra pad 14. Avgjør med et faktisk layoutforsøk + DRC, ikke på papiret. |

### 3.2 U1-02 / FE-2 — VDD_SPI

| Felt | Innhold |
|---|---|
| Verdikt | **CONFIRMED, og styrket av Espressifs eget referansedesign** |
| Schematic | `openrz67.kicad_sch:3191` `(no_connect (at 176.53 186.69) …)`; symbolpinne 18 `VDD_SPI` er type **`power_out`** (`openrz67.kicad_sym:724-727`), derfor måtte flagget settes for å holde ERC ren. |
| PCB | `openrz67.kicad_pcb:14517` pad `"18"` `(at 1.25 -2.55)` → **(22,507, 11,870)**, net `unconnected-(U1-VDD_SPI-Pad18)`, 1 forekomst → ingen kobber. Pinnene 19–24 (SPIHD/SPIWP/SPICS0/SPICLK/SPID/SPIQ) er alle NC — **korrekt** for in-package flash og identisk med MINI-1-skjemaet. Bør stå i «Verifisert OK», ellers ser seks NC-flagg på rad ut som en glipp. |
| Datablad | HDG §1.3.2 *Power Supply → Digital Power Supply*, ordrett: «When the VDD_SPI outputs 3.3 V, it is recommended that users add a 1 μF capacitor close to VDD_SPI.» + Attention: «When using VDD_SPI as the power supply pin for the in-package flash …, the supply voltage should be 3.0 V or above». DS tabell 2-9: pinne 18 «Output: In-package and off-package flash»; tabell 5-3 R_SPI 7,5 Ω typ. **Referansedesign:** ESP32-C3-MINI-1 DS v2.2, figur 8-1 (s. 32), modulen bygget på ESP32-C3FH4: pinne 18 → **C11 1 µF → GND**, pinne 17 → C10 0,1 µF → GND. |
| Korreksjon til originalen | (a) «FH4 driver intern flash via RSPI 7,5 Ω» brukt som begrunnelse er feil mekanisme. 20–25 mA × 7,5 Ω = 150–188 mV er et **statisk** IR-fall som en kondensator på pinne 18 ikke fjerner; marginen er dessuten grei (3,3 − 0,19 = 3,11 V > DS-kravet 3,0 V). Funnet er dekopling/robusthet. Bytt bevis-kolonnen til HDG-setningen + MINI-1 figur 8-1 — det er langt sterkere. (b) C15849 er **0603** (`out/openrz67-bom.csv:7`, gruppen C14/C26/C29), ikke 0402. |
| Fiks-feasibilitet | **Trangere enn originalen antar.** Kobber rundt pad 18: F.Cu VCC-stubben fra pad 17 løper (23,058, 11,993)→…→(19,895, 11,049) w 0,2285 og passerer **0,82 mm** fra padden; på B.Cu ligger et 0,635 mm bredt VCC-spor (18,847, 12,293)→(23,727, 12,293) **0,42 mm** unna. GPIO9-sporet på y = 10,320 er altså ikke den nærmeste hindringen. Et 0603 (~2,6 × 0,95 mm landmønster) er tvilsomt her; et 0402 1 µF er tryggere, men blir en **ny** BOM-linje. Kravet om egen GND-via står (brettet har GND-soner på begge lag, men ikke inn i denne lommen). |

### 3.3 U1-03 / FE-3 / PWR-02 — X2, GPIO0 og VSYS-deleren

| Felt | Innhold |
|---|---|
| Verdikt | **«X2 ubrukt»: CONFIRMED · «blokkerer eneste frie ADC1-pinner»: CONFIRMED · foreslått fiks: REFUTED som skrevet** |
| PCB | X2 `XKXGI-SUA-32.768K` CL 12,5 pF (C5213671), `openrz67.kicad_pcb:100` (144,5595, 110,4765) rot 180; pad 1 → `32K_N`, pad 2 → `32K_P`. U1 pad 4 → `32K_P`, pad 5 → `32K_N` = **GPIO0 / GPIO1**. C30/C31 = 18 pF ±1 % mot GND. ADC1-status: GPIO2 (CH2) opptatt av strapping-pullup R8, GPIO3 (CH3) = S2_DRV, GPIO4 (CH4) = S1_DRV, GPIO5 = ADC2 (ikke fabrikkkalibrert, JTAG). GPIO0/1 er de eneste frie ADC1-pinnene. |
| Framework | `framework-arduinoespressif32@3.20014.231204/tools/sdk/esp32c3/sdkconfig:832` `CONFIG_ESP32C3_RTC_CLK_SRC_INT_RC=y`, `:833` EXT_CRYS not set, `:983` `# CONFIG_PM_ENABLE is not set`; samme i den forkompilerte `qout_qspi/include/sdkconfig.h:269-270`. **Også** den nyere pakken på disk (3.20017.241212) har `:846 INT_RC=y` og `:1002 PM_ENABLE` av. `.pio/build/rev1/idedata.json` bekrefter at det er 3.20014 som bygges. Dette **lukker** originalens åpne post «the prebuilt sdkconfig was not inspected on disk». |
| Firmware | Ingen ADC-kode, ingen treff på GPIO0/GPIO1/32768/`esp_sleep`/`analogRead`. `src/main.cpp:294-316` `configurePowerManagement()` ber faktisk om light sleep (`:300 .light_sleep_enable = !ARDUINO_USB_CDC_ON_BOOT`, `:308 esp_pm_configure()`), men kallet er inert fordi `CONFIG_PM_ENABLE` er av. Originalens brødtekst (linje 542) har dette riktig; den komprimerte raden i seksjon 2 («main.cpp har ingen sleep/RTC-kode») er upresis. |
| Datablad | DS tabell 2-6: GPIO0 = ADC1_CH0, GPIO1 = ADC1_CH1. GPIO0/1 er **ikke** strapping (kun GPIO2/8/9) og står ikke i tabell 2-2 «Power-Up Glitches» — premisset i oppgaven holder. Tabell 5-6: ATTEN2 0–1300 mV ±10 mV, ATTEN3 0–2500 mV **±35 mV**. Tabell 5-5: ADC-karakteristikken er målt «with an external 100 nF capacitor» — 100 nF-delen av fiksen er godt underbygd. BQ25185: `VSYS_REG` 4,5 V ±2 % når `VBATREG ≤ 4,3 V` (R13 = 18 k → 4,2 V), SYS_OVP 104–106 %, BUVLO 3,0 V typ med 90/150/210 mV hysterese **ved VIN = 0**. |
| Hvorfor fiksen er feil | (a) **Node.** `U3.1 SYS → VSYS → S3.1`; S3 er *nedstrøms*. 2 MΩ på VSYS trekker 4,2 V / 2 MΩ = **2,1 µA døgnet rundt, også med S3 av** — +35 % på originalens eget ≤ 6 µA av-budsjett i §5 (~4 år → ~3,5 år). Originalen bruker i §5 «No resistor divider across BAT+ or VSYS» som et *pluss* og foreslår i §2 nettopp en slik deler, uten å oppdatere budsjettet. Riktig node er **SW_SYS** (etter S3). (b) **Med USB i er VSYS låst til 4,5 V**, uavhengig av cellen; deleren blir da en «USB tilstede»-flagg, ikke en ladeindikator. (c) **Delingsforholdet.** 1 M/1 M lander SYS_OVP 4,77 V på 2,385 V, altså i ATTEN3 med ±35 mV = **±70 mV referert** (±5,8 % av 3,0–4,2 V-spennet). ATTEN2 er dobbelt så nøyaktig; men merk at 2,2 M/820 k med ±1 % kan gi 1,314 V i OVP-transienten, marginalt utenfor ATTEN2s 1300 mV — velg forholdet med toleranse-marginen regnet inn, eller aksepter ATTEN3. (d) **Begrunnelsen.** `U2.6 (EN)` er hardkoblet til `SW_SYS` og S3 er mekanisk, så en ADC kan ikke i seg selv hindre BUVLO-syklingen. Men den *muliggjør* mitigeringen: `esp_deep_sleep_start()` kutter ~40 mA til titalls µA, og GPIO0/1 ligger i `VDD3P3_RTC`-domenet, altså blant de få deep-sleep-wakeup-pinnene på C3 — nok et argument for å frigjøre dem. Formuler funnet som «varsling + muliggjør deep-sleep-mitigering», ikke «hindrer boot-loop». |
| Korrigert fiks | «Fjern X2/C30/C31 (alle tre — ellers henger 18 pF mot GND på ADC-noden). Legg motstandsdeler fra **SW_SYS** til GND med midtpunkt på GPIO0 og 100 nF fra GPIO0 til GND; velg forhold slik at SYS_OVP 4,77 V med ±1 % motstandstoleranse holder seg innenfor valgt ATTEN. Vent ~5τ etter oppvåkning før første lesning (τ = 50–60 ms). Formål: lavbatterivarsling og deep-sleep-mitigering.» |
| Strøket fra motlesningen | Påstanden om at C30/C31 = 18 pF er feilmatchet mot X2 holder ikke: C_L = 18·18/36 + C_stray = 9 + ~3,5 ≈ **12,5 pF**, altså krystallens CL. 18 pF er lærebokverdien (2×(12,5 − 3) = 19). Ingen parallell til originalens X1-funn (U1-07), som gjelder en reell undermatch. |
| Nyansering | «Arduino tillater ikke EXT_CRYS» er for sterkt. Ingen **prebuilt** Arduino-pakke aktiverer det; en egen ESP-IDF-/lib-builder-bygging kan, og originalen foreslår selv en custom sdkconfig (linje 543). Riktig formulering: X2 er død i alle bygg som bruker de forkompilerte pakkene. Boot-loop-en er dessuten **treg**: gjeninnkobling krever +90–210 mV på cellen med VIN = 0, altså OCV-relaksasjon over minutter — periodisk gjenoppstart, ikke en krasjløkke. |

### 3.4 DELTA-01 — arkiv mot out/

Proveniensen er sterkere enn README hevder: arkivets 13 gerber-/drill-filer skiller seg fra `git show 0e1376e:pcb/kicad/out/gerber/*` bare i to headerlinjer hver (`%TF.CreationDate` 2026-09-07T20:10:15 mot 20:25:08), `openrz67-job.gbrjob` i én linje, og `pcb/archive/2026-09-07-rev2/drc.rpt` er **byte-identisk** med `0e1376e`s. `top.png`, `bottom.png` og `schematic.pdf` er også byte-identiske. `out/openrz67-gerber.zip` er byte-identisk med det sporede `out/gerber/`.

| Endring (2026-09-08) | I arkiv? | Bevis |
|---|---|---|
| C23 flyttet til U2 VIN (`4550987`) | **Mangler** | `0e1376e`: C23 (136,5, 101,4) rot 0, pad 2 (`SW_SYS`) 3,572 mm fra U2 pad 5. HEAD: (135,15, 100,5) rot 180, pad 2 1,120 mm unna. Ny GND-via aux (15,85, 11,2) bare i `out/`. |
| U2/U3 EP-vias (`64ef2b8`+`4550987`) | **Mangler** | `0e1376e`: 0 vias i U2 EP (1,2×2,0) og 0 i U3 EP (0,9×1,5). HEAD: 4 + 2, på de oppgitte koordinatene. Totalt vias 140 → 145. |
| GPIO21 som ett B.Cu-løp | **Mangler** | `0e1376e`: 9 segmenter / 4 vias, F.Cu 18,083 mm + B.Cu 8,742. HEAD: 5 segmenter / 2 vias, 15,417 + 10,851. |
| GND-halsen under U1 åpnet | **Mangler** | B.Cu VCC (141,285, 110,117)→(140,32, 109,1515) erstattet av to segmenter via (141,047, 110,117); VCC-via aux (20,32, 19,151)→(20,33, 19,4); CHIP_EN-via (22,924, 17,94)→(22,924, 17,78). Sone: 15 → 14 fyllpolygoner. |
| Pin-1-prikker U1/U3 (`24bc07f`) | **Mangler** | `0e1376e`: U1 har ingen F.SilkS-sirkel, U3 kun r = 0,03 / w = 0,06. HEAD: fylt r = 0,2 begge, tegnet i `F_Silkscreen.gto` linje 713/721 og 789/797 med D14. |

| Felt | Innhold |
|---|---|
| Verdikt | **CONFIRMED.** Originalen teller fire fikser; det er **fem** endringer (pin-1-prikkene er en egen commit og er nevnt i påstandsteksten, men ikke i seksjon 2-raden). |
| Talltilfeller | F_Cu **2953** reelle diff-linjer (originalen: 2949). B_Cu 1260, F_Silkscreen 249, F_Mask 6, F_Paste 4 stemmer eksakt. PTH.drl **19** uten tidsstempel — originalens 23 er tallet *med*, altså inkonsistent med de øvrige. PTH-hull 158 → 163 (T1: 140 → 145): **10 lagt til, 5 fjernet, 2 flyttet**. `PTH-drl_map.gbr` 146 linjer, ikke nevnt. `erc.rpt` skiller bare i tidsstempelet. |
| Via-tilskrivelse | Originalen lister fem koordinater for GPIO21s «4 vias». To av dem — (18,186, 18,490) og (18,553, 17,320) — er på nett **GND**, ikke GPIO21, og (25,15, 19,00) er utelatt. GPIO21 hadde: (17,65, 16,55), (17,90, 14,25), (18,80, 18,00), (25,15, 19,00). |
| DRC-delta | Arkiv 14 brudd mot 10 i `out/`; differansen er nøyaktig 4 × `starved_thermal` (sone `[GND]` F.Cu prio 498, min spoke 2 / actual 1) ved U2 pad 7 (136,56, 98,9), U2 pad 9 (136,56, 97,9), USB1 pad 1 (125,982, 100,059), USB1 pad 12 (125,982, 106,459). |
| Datodiskrepans i kilden | `README.md` og `pcb/archive/README.md` sier «ordered 2026-09-07»; `pcb/kicad/README.md:268` og commit `24bc07f` sier «the 2026-09-08 order». Merk at pin-1-prikkene ble laget som **svar** på JLCPCBs DFM-spørsmål, altså etter opplasting — de er helt sikkert ikke på brettene. Et evt. git-tag bør merkes med commit-hashen, ikke datoen. |

### 3.5 L-01 — GND-halsen på B.Cu

| Felt | Innhold |
|---|---|
| Verdikt | **CONFIRMED på tredje desimal · begge foreslåtte fikser REFUTED** |
| Geometri | Zone `(net "GND") (layer "B.Cu")` uuid `c357cabf-…`, prio 499, `min_thickness 0.127`: 4 utlinjer / 642,50 mm², hovedøy 561,22. F.Cu-GND: 7 utlinjer / 506,65, hovedøy 413,61. Vertikale snitt hver 0,25 mm: bånd **y 0,3005–0,5615 = 0,2610 mm**, konstant x 25,75 → 32,06, taper 0,350 (x 32,25) / 0,850 (32,75), sammensmelting x ≈ 33,25. Uavhengig erosjonsbisektering (`SHAPE_POLY_SET::Inflate`): østblokken løsner ved r = 0,13050 → hals 0,2610. Ved r = 0,140/side: 363,3 + 115,4 mm² — originalens «115 + 363» reprodusert eksakt. |
| Hva klemmer | Nord: `Edge.Cuts` + `min_copper_edge_clearance` 0,30 → kobber starter y = 0,3005. Sør: B.Cu-spor på **VCC**, w 0,254, **senterlinje y = 0,816** (kant 0,689; + 0,127 sone-clearance = 0,5615). Originalens «VCC-løpet ved y≈0,7» treffer kanten, ikke senterlinja — og det er nettopp derfor fiksforslaget bommer. Ingen B.Cu-via eller pad i båndet; nærmeste er S3 pad 1/2 (Ø1,6, drill 0,9). |
| Fiks 1 REFUTED | S3 pad 1 (VSYS, (27,714, 2,040)) har overkant y = 1,240; VCC-sporets underkant er 0,943 → 0,297 mm ledig, minus 0,127 clearance = **maks 0,170 mm flytt**. Testet: dy = 0,30 gir **to** `shorting_items` (VSYS/VCC og SW_SYS/VCC mot S3 pad 1 og 2) + 2 × `solder_mask_bridge`. dy = 0,17 er lovlig og gir hals **0,4270 mm**, B.Cu-hovedøy 562,55 mm² (ikke 0,431/562,70 — det er summen 0,261 + 0,170, ikke en måling). Reell forbedring, men ikke de 0,56 mm originalen impliserer. |
| Fiks 2 REFUTED | Begge foreslåtte vias lagt inn (0,45/0,25 GND) + refill: halsen er fortsatt **0,2610 mm**, B.Cu-hovedøy fortsatt 561,22, og **samtlige** sonearealer er uendret (506,65 / 642,50 / 151,64 / 161,37). DRC 0 errors / 0 unconnected / samme 10 warnings. Viaene ligger øst for halsen og dupliserer de 12 som allerede binder østblokken. Nullverdi mot dette funnet. (Punktet (33,5, 17,9) ligger dessuten allerede i F.Cu-GND-fyllet, i sekundærøya på 55,81 mm² — «utenfor fyllet, pouren plukker den opp» stemmer ikke.) |
| Er parallellbanen solid? | Ja, men ikke av grunnen erosjonstesten gir. Erosjon på F.Cu er ikke et brukbart mål her (F.Cu-hovedøya splitter allerede ved r = 0,008 pga. tynne utløpere). Slab-målingen er den holdbare: bredeste sammenhengende F.Cu-GND-streng i et vertikalt snitt er **≥ 1,71 mm for hele x 20–40** (ved x = 29: 5,55 mm), altså langt bredere enn B.Cu-halsen. Bruk det tallet, ikke et erosjonstall. |
| Riktig fiks | Vil man ha halsen bort: flytt VCC 0,170 mm sør **og** flytt S3-paddene sørover, eller rut VCC-spinen forbi S3 på F.Cu. Vil man bare ha redundans: de 12 eksisterende viasene + F.Cu-banen er allerede nok — da er dette en DFM-/kantflis-merknad, ikke et elektrisk funn. |
| Nytt | **Ingen DRC-innstilling fanger dette.** `min_connection` = 0,0. Settes den til 0,3 får man 199 `connection_width`-warnings (alle 0,127/0,16-spor og 45 termiske eiker), men **ikke** halsen: KiCad måler bredden på forbindelser *mellom* elementer, ikke innsnevringer *inne i* et sonefyll. Erosjonstesten er eneste detektor — det bør stå i README, ellers dukker samme klasse feil opp igjen. |

### 3.6 TPS-01 / TPS-02 — C24 og 0,16 mm-halsene

| Felt | Innhold |
|---|---|
| Verdikt | **Avstand CONFIRMED · «eneste 10 µF» REFUTED · «ingen returvia» CONFIRMED bokstavelig · konsekvens REFUTED som strøm-/varmeproblem, UNCERTAIN som rippel-/EMI-problem** |
| Faktisk vei | U2 `(at 135.4 98.4)` rot 0 (VSON-10, EP 1,2×2,0). Pad 1 VOUT = `VCC` (14,240, 7,400); C24 `C0603` (19,300, 6,500) rot −90, pad 2 = `VCC` (19,300, 7,200). Seks F.Cu-segmenter: 0,16/0,700 + 0,40/2,320 + 0,16/0,700 + 0,16/0,640 + 0,30/0,361 + 0,30/1,800 = **6,521 mm**. Ingen parallell DC-vei (via (17,500, 6,700) fører B.Cu-løpet *vekk* fra U2). Senter-til-senter 5,064 mm, kant-til-kant 4,278 mm — kryssjekket mot gerber-aperturen D18. Originalens «6,5 mm unna» er sporlengde; «(19,3, 6,5)» i samme celle er C24s posisjon, så tallene forveksles lett. |
| «Eneste 10 µF» | REFUTED. `out/openrz67-bom.csv`: `10uF,"C15,C20,C21,C22,C23,C24"` — **C15 er også 10 µF på VCC**, 10,89 mm fra U2 pad 1. Riktig påstand: *på VCC-nettet* er C24 den nærmeste kondensatoren av noen verdi, og det finnes ingen 100 nF/1 µF ved pinnen (C29 1 µF 12,97 mm, C4 100 nF 13,91, C6 12,75, C7 14,31, C3 15,00, C26 18,66). Originalens §5-linje «C24 10 µF + C26 1 µF at U2» er feil — C26 står ved U1. |
| Returvia | Nærmeste GND-via til C24 pad 1 (19,300, 5,800) er **2,866 mm** (17,35, 3,70); ingen innenfor 1,5 mm. Men punkt-i-polygon: C24 pad 1, U2 pad 3 og U2 EP ligger alle i **samme** F.Cu-GND-polygon (413,6 mm²) — returen er et plan på samme lag, ikke en manglende forbindelse. Mindre alvorlig enn ordlyden antyder. |
| Konsekvens | IPC-2221 (ytre lag, 35 µm, ΔT 10 °C): 0,16 mm → **0,633 A**, 0,20 → 0,745, 0,254 → 0,886, 0,30 → 0,999. Reell last ~95 mA ut ⇒ halsene på 2–19 % av grensen, ΔT < 0,2 °C. Hele U2.1→C24.2 ≈ 12,7 mΩ → 1,3 mV ved 0,1 A. **IR-fall og varme er ikke problemet.** Det som står igjen: ~4–5 nH i Cout-grenen mot ~5 µF DC-deratert C24 gir egenresonans ≈ 1,1 MHz, altså under fsw 2,4 MHz — grenen er induktiv ved switchefrekvensen (|Z| ≈ 68 mΩ). Kan bare måles. |
| Netklasse | `VCC` ligger i netklasse **`3v` (0,20 mm)**, ikke `5v` — originalens «under 5v-klassens 0,254» er feil klasse for VOUT-halsene (den stemmer for `SW_SYS`-stubben). `track_width` i en netklasse er dessuten KiCads rutebredde-*standard*, ikke en DRC-regel; DRC-grensen er `min_track_width` 0,127. Derfor står det ingenting i `out/drc.rpt`. |
| Fiks 1 REFUTED | (15,4, 6,3) er opptatt: BAT+-via **0,5/0,25** 0,510 mm fra sentrum (inne i 0603-omrisset), BAT+ B.Cu w 0,40 med 0,212 mm klaring, VCC-broen 0,200 mm. Feltet mellom U2s toppads (y 7,4) og U3s toppads (y 4,75) er 2,65 mm og brukt av BAT+/VSYS-krysset. Testet også 0-graders orientering — også konflikt. Å flytte C24 dit er en ombygging av strømhjørnet. |
| Fiks 2 STØTTES | Egen GND-via ved C24 er gjennomførbar i dag: nærmeste lovlige 0,45/0,25-punkt er **0,400 mm** fra C24 pad 1s sentrum, (18,900, 5,800) eller (19,700, 5,800), med **0,395 mm** kobber-til-kobber til `STAT2`. Vias er tentet. Gjør denne uansett. |
| Fiks 3 (ny) | Legg om utgangen i stedet for å flytte delen: fører man 0,30 mm østover fra broen ved y 6,7 og opp til C24 i stedet for å dukke ned i pad 10 (FB), faller veien til **5,83 mm** — 0,69 mm / 11 % gevinst, ikke de ~1,4 mm en rask overslagsregning gir. Kombinert med 0,20 mm-utganger og GND-viaen tar det det meste. |
| Fiks 5 er den mest verdifulle | Via på C23 pad 2 ned på B.Cu `SW_SYS`: bekreftet at pad 2 er `SW_SYS` og at B.Cu-sporet (14,400, 10,300)→(15,100, 10,300) w 0,30 går rett under. Originalen nevner den sist. |
| Nytt (N1) | **Hele U2s inngangsstrøm** går gjennom **1,340 mm** 0,16 mm-spor (0,640 fra pad 5 til (13,600, 9,400) + 0,700 opp til viaen) og én 0,5/0,25-via; C23 har ingen egen via, så det finnes ingen parallell vei. Ved 500 mA ut og tom celle er inngangsstrømmen 0,611 A ≈ 97 % av IPC-grensen for 0,16 mm. Tyngre hals enn de to på VOUT, og originalen slår den sammen med dem. |
| Nytt (N2) | B.Cu-GND-planet er brutt rett under Cout-veien i **x 15,02–17,86 ved y 6,70** (2,84 mm) av B.Cu VCC-løpet (17,300, 6,900)→(15,200, 6,900) — returstrømmen må rundt bruddet der forovervei-en er lengst. |
| Nytt (N3) | C25 (VINA-bypass, 100 nF) har samme mangel som C24: nærmeste GND-via 2,98 mm. Lav alvorlighet (databladet krever ikke nærhet for VINA). |
| Nytt (N4) | Funnet står allerede i `pcb/kicad/README.md:236` («a return via next to C24, 0.16 mm power necks at the U2/U3 pads»). Raden mangler «Kjent i README»-merket som L-02 har. |

### 3.7 L-02 — U3 maskedam

| Felt | Innhold |
|---|---|
| Verdikt | **Geometri CONFIRMED · «bare U3» REFUTED · alvorlighet nedgradert til UNCERTAIN/lav** |
| Geometri | U3 `openrz67:WSON-10_L2.2-W2.0-P0.40-EP0.9x1.5` (17,000, 3,700); pads `(size 0.5 0.2)` rot 90 = **0,200 × 0,500** i brettrammen, pitch 0,400 → kobbergap 0,200 → dam **0,200 − 2×0,051 = 0,0980 mm**. Ingen `solder_mask_margin` på footprint- eller padnivå. `(setup (pad_to_mask_clearance 0.051) (allow_soldermask_bridges_in_footprints no))`, ingen `solder_mask_min_width`. Målt direkte i `out/gerber/openrz67-F_Mask.gts`: aperture D47 = RoundRect 0,051 med hjørner ±0,1/±0,25 → åpning 0,302 × 0,602, **ti separate flash**, åtte naborpar alle på 0,0980. Pad→EP-dam 0,248. |
| «Bare U3» REFUTED | Brettets minste maskedam er **0,0655 mm** mellom U2 pad 6 (`EN`) og C25 pad 2 — begge `SW_SYS`, så en bro er elektrisk uskadelig, men det er den tynneste maskefliken på brettet og den er ikke nevnt noe sted. **USB1 pads 3–10 (åtte pads, sju mellomrom) ligger på nøyaktig samme 0,0980.** USB1s to Ø0,7 NPTH-pinner har 0,0692 mm til to av padene (og 0,1107 til de to andre). U1 og U2 ligger på 0,1180. Originalens §5-linje «only U3 is below» er feil. |
| Alvorlighet | Det fabrikerte rev 1-settet (samme fab, maskeekspansjon 0,09) hadde **0,0198–0,0201 mm** damer på nøyaktig samme USB1-rad, 0,0416/0,0631 på VBUS/GND-padene, og **ett par helt sammensmeltede åpninger** ved (33,04, 20,04)/(31,56, 20,12). JLCPCB bygde og monterte det brettet, og det virker. Fabben avviser altså ikke fila. Den nye risikoen er **loddebro under montering av et 0,4 mm-pitch WSON** — rev 1 hadde ingen 0,4 mm-pitch-del (ikke ettergått uavhengig). Begrunn fiksen med «0,12 er innenfor fabbens oppgitte grense», ikke «0,098 virker ikke». |
| Fiks | `(solder_mask_margin 0.04)` på U3s ti signalpads → åpning 0,280 × 0,580, dam **0,120 mm**. Aritmetikken stemmer. Innenfor TIs land-pattern-note «0.05 MAX ALL AROUND / NON SOLDER MASK DEFINED (PREFERRED)» (4226298/A 10/2020). Ved ±0,05 mm maskeregistrering gir 0,04 verste fall 0,01 mm maske inn på en 0,20 mm pad (~5 %) — akseptabelt. Gå **ikke** til 0,025 (0,075 mm inntrengning = ~37 %). Brettets 0,051 er 0,001 over TIs maksimum for både QFN og WSON, så en **global** endring til 0,04–0,05 er mer datablad-konform enn en lokal padoverstyring. |
| Ikke fiks | U1s hjørnepar er **0,311 mm** fra hverandre i masken, ikke 0,108 eller 0,153: aperturene er obround (`%ADD35O,0.382000X1.002000`), og de avrundede endene skyver hjørnene fra hverandre. Ingen handling. |
| DRC | 0 `solder_mask_bridge`, og sjekken *er* aktiv (error-severitet, slår ut umiddelbart i kontrollprøven der VCC-sporet ble flyttet 0,30 mm). KiCad flagger først ved overlapp (dam ≤ 0), ikke ved 0,098 — den kan ikke fange en fab-grense. |

## 4. Lukkede «Ikke sjekket»-punkter

### 4.1 Fersk DRC og ERC

`kicad-cli` 10.0.6, kjørt på kopi: `pcb drc --severity-all --schematic-parity --all-track-errors --refill-zones --save-board` og `sch erc --severity-all`.

| Sjekk | `out/` (2026-09-08T23:38) | Fersk (2026-09-10) | Avvik |
|---|---|---|---|
| DRC violations | 10 | 10 | ingen |
| — errors / unconnected / footprint / parity | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | ingen |
| — fordeling | 7 `courtyards_overlap`, 1 `silk_overlap`, `text_height`, `text_thickness` | identisk | ingen |
| ERC violations | 15 (`endpoint_off_grid`), 0 errors | 15, 0 errors | ingen |
| Sonefyll | — | `--refill-zones --save-board` gir **byte-identisk** `.kicad_pcb` | fyllet i fila er ferskt |

`diff` av rapportene med tidsstempellinja fjernet er **tom** for både DRC og ERC. `starved_thermal`, `isolated_copper`, `copper_sliver`, `connection_width`: 0 treff hver, alle på warning-severitet og med i `--severity-all` — ekte nuller. Filhoder: pcb `(version 20260206) (generator_version "10.0")`, sch `(version 20260306)` uten `generator_version`; verktøyet er samme minor, nyere patch.

**Viktig:** ERC vil **aldri** flagge U1-01/U1-02. Bevist ved å fjerne alle 15 `no_connect` i en kopi: da får man 30 violations, blant dem `pin_not_connected` på «U1 Pin 14 [GPIO8]» @(158,75, 207,01) og «U1 Pin 18 [VDD_SPI]» @(176,53, 186,69), begge med error-severitet. NC-flaggene er det eneste som holder ERC stille, og de må fjernes samtidig som pinnene får krets.

### 4.2 U5/U6 TLP172AM — pad-til-pinne og R21/R22 mot IFT

| Felt | Innhold |
|---|---|
| Verdikt | **Pinkart CONFIRMED. LED-strøm CONFIRMED OK — ingen risiko.** Lukker to «Ikke sjekket»-punkter (linje 260 og 278). |
| Pinkart | `openrz67.kicad_sym` `TLP172AM`: pin 1 «A», 2 «K», 3 «D», 4 «D». Footprint `SMD-4_L4.6-W3.7-P2.54-LS7.0-BR`: pad 1 (3,5/1,27), 2 (3,5/−1,27), 3 (−3,5/−1,27), 4 (−3,5/1,27), alle 1,5 × 0,8. Datablad Rev.11.0.A s. 2: «1: Anode / 3: Cathode / 4: Drain / 6: Drain»; s. 10 toppvisning: 6 øverst-venstre, 4 øverst-høyre, 1 nederst-venstre, 3 nederst-høyre. Transformasjonen datablad → footprint er en ren **90° rotasjon mot klokka**, verifisert hjørne for hjørne (samme kiralitet, ingen speiling). Nett: pad 1 ← R21/R22 ← `S1_DRV`/`S2_DRV` (U1 pinne 9/8), pad 2 → `GND`, pad 3 → `AGND`, pad 4 → `S1`/`S2`. Utgangen er to source-koblede MOSFET-er med body-dioder, altså **bidireksjonal** — pad 3/4 har ingen polaritet. |
| LED-strøm | R21/R22 = 150 Ω ±1 % (C25082). Ideell driver: 12,5–14,8 mA (VF 1,1–1,4 V); med VCC-vindu 3,20–3,50 V: 11,9–16,2 mA. Med 10 mA-klassens ekvivalente utgangsmotstand (Rout ≈ 66 Ω, se 5.3): typisk **9,4 mA**, verste hjørne **8,3 mA**. Datablad §11: **IFT typ 1 / maks 3 mA**; RON ≤ 2 Ω spesifisert ved IF = 5 mA; §7 anbefalt IF 5/7,5/25 mA. **Margin 2,8× mot IFT(maks), 1,66× mot RON-testpunktet.** Effekt: LED 18 mW < PD 50 mW; R21 40 mW < 62,5 mW. tON maks 2 ms ≪ de 10 ms firmware venter mellom S1 og S2. |
| Nytt | Anbefalt IF derates −0,3 mA/°C over 25 °C. Beste hjørne (16,2 mA, ideell driver) krysser den deratede abs.maks-grensen ved Ta ≈ 71 °C; med 66 Ω-modellen ved ≈ 88 °C. UL508-tabellen setter uansett maks 19,5 mA ved 60 °C. Verdt en linje ved 150 Ω-regnestykket i README. |
| Nytt | **Premisset «rev 1 brukte samme del og virket» er feil.** Rev 1-BOM rad 12 har `G6K-2F-Y DC3` på K1/K2 (Omron-reléer); «TLP172» finnes ikke noe sted i rev 1-arkivet. U5/U6 har **ingen produsert presedens**. |
| Orientering | CPL i både `out/` og arkivet: `U5,36.500mm,-14.400mm,Top,270` / `U6,…,270` — `ROT_FIX` +90 er faktisk påført, og brettene i posten er bestilt med den vinkelen. Et **90°-avvik er fysisk umulig å lodde** (7,0 mm lead span mot 2,54 mm pitch), så JLCPCBs biblioteksforskyvning kan bare gi et *forhåndsvisnings*-avvik. Eneste reelle risiko er **180°**, og pakkens to toppmerker er diagonalt symmetriske, så det er **ikke visuelt lesbart** på ferdig brett. Lukkes elektrisk: diodetest pad 1 ↔ pad 2 skal vise en LED-overgang, pad 3 ↔ pad 4 brudd begge veier; ved 180° er resultatene byttet. (Et vanlig DMM driver ~0,5–1 mA, så avlest VF blir lavere enn tabellens 1,1–1,4 V ved 10 mA — testen skiller likevel entydig.) |
| Nits | `F.CrtYd` 8,6 × **3,8** mm mot maks kroppsbredde 3,95 → courtyarden klipper 0,075 mm/side (U5–U6-gap er 3,0 mm, utløser ingenting). Hæl-margin 0,25 mm er under IPC-7351 nominal 0,35. F.Fab-rektangelet er 4,6 mm langs lead-span-aksen mot databladets nominal 4,55 (+0,25/−0,15) — innenfor toleranse. |
| Til SH-1 | Pakken garanterer 5,0 mm creepage/clearance (tabell 3.1) og brettet holder 5,5 mm kobbergap mellom katode- og AGND-pads — men AGND-utfyllingen kommer 0,85 mm fra katode-padsene. Det er **brettet, ikke delen**, som setter isolasjonen. |

### 4.3 BAT1 JST PH-polaritet (LIB-03)

| Felt | Innhold |
|---|---|
| Verdikt | **LIB-03 står. Originalens «Ikke sjekket»-punkt er delvis REFUTED (feil innrammet):** låsevinduet er ikke det polariteten henger på, og headersiden lar seg faktisk lukke fra JST-katalogen. |
| Brett | `openrz67:CONN-TH_B2B-PH-K-S` (123,275, 94,8105) rot 90. Pad 1 (Ø1,6/0,9) (123,275, 93,811) = aux (3,275, 3,811) → **BAT+**; pad 2 (123,275, 95,811) → GND. Pin 1 vender mot S3-kanten (y = 0). |
| Datablad lukker headeren | `ePH.pdf` s. 1, «PC board layout … Top entry type», sett fra monteringsflaten: hullrekka har **(1.7) mm til den ene omrisskanten** av 4,5, og «No. 1 circuit» er hullet lengst til høyre. Footprinten er en tro kopi: pads på lokal y = 0, omriss y −2,8…+1,7, pad 1 på lokal x = +1,0. Delen har dessuten et støpt «Mark of No. 1 circuit» (s. 3). **Orienteringen er entydig bestemt av 1,7/2,8-asymmetrien (1,1 mm)** — en 180°-rotasjon ville få kroppen til å stikke 1,1 mm utenfor silkomrisset. Originalens «silk differs left/right only by 0.05–0.13 mm» er korrekt målt, men det er ikke den asymmetrien som orienterer delen. |
| Rev 1-paritet | `pcb/archive/2025-09-23-rev1/Drill_PTH_Through.DRL` T04 (Ø0,90002): hull (3,27488, −5,81063) og (3,27488, −3,81064) — identisk med rev 2s BAT1-pads. Kobber og orientering er uendret. Drillfila sier likevel ikke hvilket hull som var BAT+. |
| Det som faktisk står åpent | Hvilken ledning i PHR-2-huset som er krets 1 er en egenskap ved **cellepakken**, ikke ved JST. Rød i krets 1 er ingen standard. Bare målbart med multimeter på den konkrete pakken. |
| Korreksjon | Påstanden «F.SilkS har ingen polaritetsmarkering overhodet / brettet har ingen +-tekst noe sted» holder ikke bokstavelig: `BAT+` finnes som `gr_text` på **B**.SilkS (124,826, 92,997), og det ligger en enslig `-` på **F.SilkS** ved (123,354, 98,9025), størrelse 1,067 — 0,08 mm fra BAT1s padkolonne-akse og 1,09 mm utenfor kontaktkroppen på GND-pad-siden. Å avfeie den som C21s (et 0603 10 µF 3,57 mm unna, der `-` er meningsløst) er ikke underbygd; den leser mer som en fjern, uparet BAT1-negativmarkør. LIB-03 står uansett, fordi `pcb/kicad/README.md:237` selv fører «a `+` mark for BAT1 on F.SilkS» som åpen. Fiksordlyden «`+` ved pad 1 på **F**.SilkS» er fortsatt den riktige. |

## 5. Seksjon 3-minorene med høyest konsekvens

### 5.1 CHG-3 / FE-4 / PWR-03 — R16 NTC

| Felt | Innhold |
|---|---|
| Verdikt | **«R16 måler laderen, ikke cellen»: CONFIRMED, og sterkere enn originalen sier. «>67 °C → factory mode-fall»: REFUTED. «Forveksling med en annen TI-lader»: REFUTED — BQ25185 pinne 6 *er* TS/MR.** |
| Krets | R16 = `NCP18XH103F03RB` (Murata NTC 10 kΩ ±1 %, β25/85 = 3434), R0603, pad 1 → `TS_MR`, pad 2 → GND. Nettet `TS_MR` har **nøyaktig to** pads: R16.1 og U3.6. Ingen bias-/kompensasjonsmotstand — akkurat kretsen databladet ber om. |
| Avstander | U3 (137,0, 93,7) ↔ R16 (138,7, 91,0): senter-til-senter **3,191 mm** (originalens 3,2 stemmer), men **kobber-til-kobber 1,118 mm** (U3 pad 6 = TS_MR mot R16 pad 1) — termisk kobling er verre enn originalen antyder, og de deler GND-planet. R16 ↔ BAT1: **15,889 mm**, og cellen henger i JST-kabel *utenfor* brettet. (Merk: U3-footprinten er WSON-10_**L2.2**-W2.0, ikke 2,0 × 2,0.) |
| Trip-temperaturer | I_TSMR 38 µA × R_NTC, β-formel: V_HOT_ENTRY 0,1150 V → 3026 Ω → **59,5 °C**; V_HOT_EXIT 0,1350 → 3553 Ω → **54,4 °C**; V_COLD_ENTRY 1,0075 → 26 513 Ω → **+1,7 °C**; V_COLD_EXIT 0,8200 → 21 579 Ω → **+6,3 °C**; V_TSMR 90 mV → 2368 Ω → **67,6 °C**. Originalens «~1 °C / ~59 °C / >67 °C» reproduseres eksakt. |
| Factory mode REFUTED | Tre grunner. (a) **Termisk:** ladetapet er ~0,26 W → +18 K ved RθJA 68,3 °C/W, T_J ≈ 62 °C ved 25 °C omgivelse — og i det øyeblikket HOT-trippen slår inn ved 59,5 °C **faller ladetermen bort**; igjen står ~0,07 W → +4,8 K. Systemet kan ikke løfte seg fra 59,5 til 67,6 °C på egen varme. (b) **Sekvens:** §6.3.8 krever `tLPRESS` = 10 s sammenhengende **og** at VIN deretter fjernes («After this duration, **removing VIN** places the device into factory mode»). (c) **V_TSMR-retningen:** at 90 mV bare er en max-spesifikasjon trekker terskelen mot *lavere* spenning = *lavere* NTC-motstand = **høyere** temperatur (63 mV → ~80 °C), altså lenger unna, ikke nærmere. Konsekvensen når det først skjer er alvorlig (BATFET av, SYS ute til USB settes i igjen), men scenariet er ikke troverdig via egenvarme. |
| Det reelle symptomet | HOT-hysteresen 54,4 → 59,5 °C er 5 K. I et lukket, 3D-printet kabinett uten luftstrøm pendler brettet i den sløyfa og **lader intermitterende**, mens D3 slukker og tenner. Ved TS-feil er STAT1 LOW / STAT2 HIGH = «recoverable fault» → **D3 slukker, som README tolker som «ferdigladet»** (samme familie som CHG-1, men et annet tilfelle). Kuldetrippen er den mer sannsynlige plagen: under **+1,7 °C brettemperatur** nektes lading helt, gjenopptak først ved +6,3 °C — realistisk «lader ikke» ute om vinteren. |
| Rekkevidde | Tabell 6-4: «TS Measurement» og «Pushbutton Input» = Yes **kun** i Adapter mode, No i Battery-only og Factory. **Hele feilmodusen eksisterer bare mens USB er tilkoblet.** Originalens §5 har dette riktig; seksjon 3-raden sier det ikke. |
| Fiks | «Fast 10 kΩ» er TIs egen anvisning når TS ikke brukes (§6.3.9.1: «If the TS function is not required, connect a 10kΩ resistor from the TS/MR pin to GND») og fjerner problemet for null BOM-endring. «Flytt R16 mot BAT1» gir **ikke** celletemperatur så lenge cellen er off-board — da måler man bare et annet punkt på kortet. Skal TS gjøre jobben, må NTC-en fysisk på cellen, altså en ledning til fra pakken: produktbeslutning, ikke layoutflytting. |
| Korrigert rad | «R16 (NTC) 1,1 mm kobber-til-kobber fra U3 og 15,9 mm fra BAT1 måler kretskortet, ikke cellen. HOT tripper ved 59,5 °C og gjenopptar ved 54,4 °C → intermitterende lading og en ladelampe som slukker; COLD sperrer under +1,7 °C (gjenopptak +6,3 °C). Knappetrykk-terskelen på 67,6 °C nås ikke ved egenvarme. Gjelder bare med USB tilkoblet (tabell 6-4). Fiks: fast 10 kΩ, eller NTC fysisk på cellen.» |

### 5.2 SH-1 — AGND/GND-gapet

| Felt | Innhold |
|---|---|
| Verdikt | **CONFIRMED.** Gapet er brettets egen minimumsklaring, og det finnes ingen AGND-regel. Fiksen er gjennomførbar og billig — men regelen må skopes, og den bommer på den trangeste kryssingen. |
| Måling | AGND-soner prio 500 (over GND 499/498), én utlinje hver, 151,64 (F.Cu) / 161,37 mm² (B.Cu), bbox x 34,60–47,70. Minsteavstand AGND↔GND: **0,1274 mm** på begge lag (hjørnene ved (34,50, 4,40) og (34,52, 17,74)); KiCads egen DRC-probe rapporterer 0,1325 mm langs kanten. Snittprofil: **konstant 0,1325 over ~8 mm (F.Cu) og ~13 mm (B.Cu)** — en lang slisse, ikke et punkt. Nærmeste faste AGND-*element* til GND-*element* (spor/pad/via, sonefyll utelatt) er **1,032 mm**, så hele det trange gapet er ren fyllgeometri. |
| Regelgrunnlag | `openrz67.kicad_pro` `netclass_patterns` dekker GND, VCC, +5V, VDDA, VBUS, BAT+, VSYS, SW_SYS, SW1, SW2 — **AGND står ikke i noen**, så den arver `Default` 0,127; `min_clearance` er også 0,127. `openrz67.kicad_dru` (13 linjer) har kun de to USB1-pinnereglene. Originalens premiss er riktig: isolasjonen er ikke skrevet ned noe sted. JLCPCBs min gap er 0,10, så det er ikke fabben som begrenser. |
| Fiks testet | `(rule "AGND to GND 0.5mm" (condition "A.NetName == 'AGND' && B.NetName == 'GND'") (constraint clearance (min 0.5mm)))` + `--refill-zones`: **0 errors, 0 unconnected, samme 10 warnings**. Kostnad: GND-fyll F.Cu 506,65 → 493,87 og B.Cu 642,50 → 627,54 (−2,4 % GND-kobber); AGND nesten uendret; antall øyer uendret, ingen ny isolert kobber. |
| Naiv variant funker ikke | `A.NetName == 'AGND' && B.NetName != 'AGND'` gir 2 clearance-feil: AGND-via ↔ `S2`-spor 0,2775 mm (falsk positiv — S2 er på samme isolerte side) og AGND-via ↔ `GPIO6`-spor 0,2955 mm (ekte). |
| **Nytt funn (seksjon 2-klasse)** | **Den trangeste kryssingen av isolasjonsbarrieren er ikke AGND↔GND, men AGND↔GPIO6.** Probe mot alt utenfor {AGND, S1, S2}: J1-headerens **GPIO6-spor på F.Cu står 0,170 mm fra AGND-pouren** i to segmenter — @(150,550, 99,300) l = 5,269 mm og @(154,350, 102,950) l = 4,850 mm (brettramme 30,55/9,30 og 34,35/12,95), sporbredde 0,16, kant 34,43 mot pourens 34,60. Det er 0,043 mm over brettets minimum og trangere enn alt annet unntatt AGND↔GND selv. `pcb/kicad/README.md:170-171` skriver at «the header sits below the AGND island (y > 17.7) in the GND domain, so camera isolation is untouched» — det gjelder **ikke** GPIO6-løpet, som følger øyas vestkant hele veien opp. En regel som bare nevner GND lar den stå. **Skriv regelen som «isolert side ({AGND, S1, S2}) mot resten», ikke «AGND mot GND», og rett README-setningen.** |
| Nytt | U4 pad 1 (kamera 6 V, uten nett) står 0,1274 mm fra AGND-pouren på begge lag. Uten nett faller den ikke inn under noen barriere-regel skrevet på nettnavn. |

### 5.3 U1-04 / SH-3 — GPIO-drivstyrke

| Felt | Innhold |
|---|---|
| Verdikt | **NEDGRADERT. Faktapåstandene CONFIRMED, ett bevisledd REFUTED, konsekvensen overdrevet. Hører hjemme som en README-linje, ikke i «bør vurderes».** |
| Bekreftet | DS v2.4 tabell 2-1 fotnote 4, ordrett: «The default drive strength for each pin is as follows: • GPIO2, GPIO3, MTMS, and MTDI: **10 mA** • GPIO18, GPIO19: 40 mA • All other pins: 20 mA». GPIO3 (pinne 8) og MTMS/GPIO4 (pinne 9) er begge i 10 mA-klassen, ingen WPU/WPD. Firmware setter aldri drivstyrke: `pinMode(..., OUTPUT)` → `__pinMode` bygger en `gpio_config_t` som **ikke har noe drivstyrke-felt** (`gpio_types.h:393-399`), så `gpio_config()` kan ikke skrive FUN_DRV; eneste `gpio_set_drive_capability` i hele Arduino-kjernen er `esp32-hal-tinyusb.c:76-77` (USB D+/D−). |
| **REFUTED bevisledd** | Originalen (linje 549) skriver «Table 5-4 VOH 0.8 VDD specified with PAD_DRIVER = 3». **Det stemmer ikke.** Tabell 5-4 fører «VOH² High-level output voltage — min 0,8 × VDD» **uten** PAD_DRIVER-betingelse, og fotnote 2 sier «VOH and VOL are measured using **high-impedance load**». Kun strømlinjene bærer betingelsen (IOH typ 40 mA ved «VOH ≥ 2,64 V, PAD_DRIVER = 3»). Databladet gir **ingen** IOH for PAD_DRIVER 0/1/2 og ingen VOH-mot-IOH-kurve. Konsekvens: READMEs «worst case 8,2 mA» er verken et drivstyrke-tall eller et garantert lastet gulv — det er en konservativ bakvendt regning som *tilfeldigvis* lander nær modellens 8,3 mA. Rett README-setningen. |
| Modell, ikke spesifikasjon | Fra databladets eneste strømpunkt: Rout = (3,30 − 2,64)/0,040 = 16,5 Ω for 40 mA-klassen, lineært skalert til **≈ 66 Ω** for 10 mA-klassen. Iterert sløyfe gir IF ≈ **9,4 mA** typisk, 8,3 verste, 11,2 beste. Med `GPIO_DRIVE_CAP_3` (16,5 Ω): **10,7–14,5 mA, typisk 12,2 mA** — altså ca. **+30 %** over 66 Ω-modellen. **Dette er en lineær ekstrapolasjon av ett publisert punkt, ikke en spesifikasjon.** Nedgraderingen er modellstøttet, ikke bevist. |
| Konsekvens | Selv om VOH skulle sige helt til 2,05 V (usannsynlig fall på 1,25 V) blir IF 4,3 mA — fortsatt 1,4× over IFT(maks) 3 mA; bare 2 Ω-garantien på RON (spesifisert ved IF = 5 mA) faller bort. **Ingen firmware-endring er nødvendig for korrekt drift.** |
| Anbefaling | La firmware stå. Hvis man likevel setter drivstyrke: `GPIO_DRIVE_CAP_2` (20 mA), som SH-3-varianten foreslår, ikke `CAP_3` (40 mA) som U1-04-varianten foreslår. Maskinvarealternativet (100 Ω) er unødvendig. **Mål IF over R21 på prototypen** — ett målepunkt avgjør både U1-04 og README-linja. |
| Boot-tilstand | Ingen risiko: GPIO3 er IE ved reset, MTMS er helt av ved reset og IE etterpå, begge høyimpedante uten pull. Ingen pull-down på anode-siden, men pinnelekkasjen er IIH/IIL maks 50 nA — fire tierpotenser under IFC min 0,1 mA. Verken GPIO3 eller GPIO4 er strapping. Rev 1s problem (S1 på GPIO21/U0TXD) er borte. |
| Felle | `gpio_types.h:412` definerer `GPIO_DRIVE_CAP_DEFAULT = 2 /* medium */`. Det er et **programvarenavn**, ikke maskinvarens reset-verdi; for GPIO2/GPIO3/MTMS/MTDI er reset-klassen 10 mA (≈ CAP_1). Den som leser headeren i stedet for databladet vil tro pinnene starter i 20 mA-klassen. |

## 6. Nye funn, ikke i originalen

| Id | Alvorlighet | Funn |
|---|---|---|
| V-01 | **major** | **GPIO6 (J1) står 0,170 mm fra AGND-pouren på F.Cu** i to segmenter (@(30,55, 9,30) l = 5,269 og @(34,35, 12,95) l = 4,850, brettramme). Trangeste kryssing av isolasjonsbarrieren, og `pcb/kicad/README.md:170-171` påstår det motsatte. Se 5.2. |
| V-02 | minor | **Hele U2s inngangsstrøm** går gjennom 1,340 mm 0,16 mm-spor + én via; ingen parallell vei. Ved 500 mA ut / tom celle: 0,611 A ≈ 97 % av IPC-grensen. Tyngre enn de to VOUT-halsene originalen grupperer den med. Se 3.6 N1. |
| V-03 | minor | **Brettets minste maskedam er 0,0655 mm** (U2 pad 6 ↔ C25 pad 2, begge `SW_SYS`), ikke U3s 0,098. Elektrisk uskadelig, men ikke nevnt noe sted. USB1 pads 3–10 ligger også på 0,098. |
| V-04 | minor | **B.Cu-GND-planet er brutt over 2,84 mm (x 15,02–17,86, y 6,70)** rett under Cout-returveien, av B.Cu VCC-løpet. |
| V-05 | minor | **C25 (VINA-bypass) har nærmeste GND-via 2,98 mm unna** — samme mangel som C24, lavere alvorlighet. |
| V-06 | minor | **Ingen DRC-innstilling kan fange soneflaskehalser** som L-01: `connection_width` måler mellom elementer, ikke inne i et fyll. Erosjonstest er eneste detektor. Bør i README. |
| V-07 | prosess | **ERC kan aldri flagge U1-01/U1-02** fordi begge pinner har eksplisitt `no_connect`. Flaggene må fjernes samtidig med fiksen. |
| V-08 | prosess | **Rev 1 hadde reléer, ikke PhotoMOS.** U5/U6 har ingen produsert presedens; «samme del virket i rev 1» gjelder ikke her. |
| V-09 | prosess | **U5/U6 180°-feil er ikke visuelt lesbar** på ferdig brett (pakkens to toppmerker er diagonalt symmetriske). Diodetest er lukkemekanismen, ikke fabrikkens forhåndsvisning. |
| V-10 | prosess | **Originalen motsier seg selv:** linje 289 «archive … was not unpacked and diffed» mot linje 311 «diff of unzipped archive gerbers vs out/gerber». Nå faktisk kjørt. |
| V-11 | prosess | **Minnenotatet «2026-09-08-fiksene er uncommitted» er utdatert** — `24bc07f`, `64ef2b8`, `4550987`, `5f30622` er i `main`. |
| V-12 | kosmetisk | Brettets 0,051 mm maskeekspansjon er 0,001 over TIs «0.05 MAX ALL AROUND» for både QFN og WSON — argument for en **global** endring til 0,04–0,05 framfor lokal padoverstyring på U3. |

## 7. Fortsatt ikke lukkbart uten maskinvare

- **GPIO8s faktiske reset-nivå på dette kobberet.** Les ROM-loggen på et mottatt rev 2-brett: `boot:0x0C` = GPIO8 høy, `boot:0x08` = GPIO8 lav (esptool «Boot Mode Message», 0x04 = GPIO8, 0x08 = GPIO9). Og om BOOT+EN-prosedyren virker reproduserbart, særlig etter at firmware har slått av USB Serial/JTAG.
- **Droop på VDD_SPI under flash-skriving.** Pinne 18 er en 0,28 × 0,9 mm QFN-pad uten testpunkt.
- **Om et 1 µF får plass ved pad 18 og en 10 kΩ ved pad 14.** Krever layoutforsøk + DRC; ikke gjort (read-only).
- **Om 0,2610 mm-halsen faktisk kutter.** JLCPCBs side-erosjon er ikke publisert; 0,14 mm/side er et valgt scenario. Mikroskop langs nordkanten x 25,75–32,06 på et mottatt brett.
- **VOUT-rippel og switche-spisser ved U2** med Cout 6,5 mm unna og ingen HF-kondensator på pinnen, og om det påvirker BLE-følsomheten. Skop på C24 og på U1s VCC-pinner, i både PWM- og PFM-området.
- **Reell temperaturstigning i 0,16 mm-halsene** ved 500 mA ut. IPC-2221 gjelder en uendelig, ensartet leder; disse er 0,6–1,3 mm stubber mellom en pad og en utstøping.
- **Om 0,098 mm maskedam gir loddebro på U3s 0,4 mm pitch**, og hva JLCPCBs CAM gjør under sin egen grense. Mikroskop på de bestilte brettene.
- **Kobbertykkelsen på de bestilte brettene** (1 oz antatt) — avgjør både IPC-grensene og hvilken JLCPCB-rad som gjelder for maskedammen. Står ikke i repoet; sjekk ordrebekreftelsen.
- **Faktisk temperatur på R16 under lading i det lukkede kabinettet**, og omgivelsestemperaturen der inne. RθJA 68,3 °C/W er JEDEC (2s2p), ikke dette 48×22 mm-kortet. Avgjør om 59,5 °C i det hele tatt nås.
- **Murata NCP18XH103F03RB R–T-tabell er fortsatt ikke lokal.** Trip-temperaturene er β-tilnærminger (±1–2 K over 50 °C). Originalens åpne post er **ikke** lukket.
- **Den faktiske V_TSMR-terskelen** (databladet gir bare max 90 mV).
- **Faktisk IF gjennom R21/R22.** Mål spenningsfallet over R21 (0402 ved (31,35, 13,40)) mens S1 er aktiv; IF = U/150. Forventet 8–13 mA. Lukker både U1-04 og READMEs 8,2 mA-linje.
- **IFT og RON over temperatur** (Fig. 14.1.5/14.1.6 er bildekurver, «not guaranteed by production test»); VF-temperaturkoeffisienten er en typisk GaAs-IRED-verdi, ikke Toshiba-spesifisert.
- **U5/U6 monteringsorientering** (diodetest, se 4.2), og **U1/U3 fysisk orientering** på brettene i posten — de har ingen brukbar pin-1-prikk, så det må leses av kapselmerkingen mot `out/openrz67-top.png` **før** første pålegging av spenning.
- **Cellepakkens ledningsrekkefølge i PHR-2** (multimeter før tilkobling), og hvilken vegg på den leverte B2B-PH-K-S som bærer låsevinduet (JST-katalogen dimensjonerer det ikke; påvirker bare kabelretning, ikke polaritet).
- **Termisk på U2/U3 EP uten vias** og VIN-rippel med C23 i den bestilte posisjonen, på de mottatte brettene.
- **BLE-rekkevidde/RSSI mot rev 1** — eneste målbare konsekvens av 0,12 mm-halsen under U1 og av GPIO21 0,21 mm fra LNA_IN på de bestilte brettene.
- **Om 0,127 mm AGND/GND holder mot det kameraet faktisk gjør** (kamerasidens spenning/impedans er uverifisert, README l. 89). IPC-2221 tabell 6-1 finnes ikke lokalt og ble ikke hentet — ikke bruk 0,13 mm-terskelen som begrunnelse i README før den er slått opp i en ekte kopi.
- **Om JLCPCB monterte U1/U5/U6 riktig** tross biblioteksrotasjonen; bare synlig på brettet.
