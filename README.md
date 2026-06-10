# Wind Power Simulation App

En applikation för simulering och analys av vindkraftverk (fysik, hållfasthet och ekonomi). Systemet är byggt med uppdelning av beräkningslogik, datamodeller och användargränssnitt (GUI).

## Arkitektur & Dataflöde

* **Sandbox Mode:** Miljön (`SiteEnvironment`) genereras dynamiskt via personnummer (`SSNGenerator`).
* **Challenge Mode:** Förutbestämda uppdrag (`Mission`) laddas med låsta miljöer.
* **Beräkning:** `SimulationEngine` tar emot en turbin och en miljö, utför fysik-/ekonomiberäkningar, och returnerar ett oföränderligt `SimulationResult` till gränssnittet.

---

## Status: Vad som är gjort

* [x] **Domänmodeller:** Grundläggande struktur för `WindTurbine`, `SiteEnvironment` och `SimulationResult` (`frozen=True`).
* [x] **Fabriker:** `SSNGenerator` som parsar personnummer och mappar till miljöparametrar.
* [x] **Beräkningsmotor:** `SimulationEngine` med formler för vind, krafter/tjocklek och ekonomi.
* [x] **Uppdragssystem:** `Mission`-klassen med stöd för utvärdering av resultat (t.ex. "The Arctic Gale").
* [x] **Huvudkontroller:** `UnifiedSimulatorApp` (`app.py`) som koordinerar flödet.

---

## Att göra: Nästa steg

### 1. Fixa klartberäkningsprogrammet

* [ ] Flytta över och uppdatera beräkningar som krävs till applikationen
* [ ] Koppla ihop med nya dataklasser och deras gränssnitt

### 2. GUI & Visualisering (AnalyticsPanel)

* [ ] Koppla ihop reglage (sliders) med `WindTurbine`-objektets parametrar.
* [ ] Implementera grafer för Weibull-fördelning och effektkurva i högerpanelen baserat på `SimulationResult`.
* [ ] Visa score och framgångs-/felmeddelanden vid körning av `Mission`.
* [ ] Lägg till så man kan exportera sina tester med diagram

### 3. Validering & Robusthet

* [ ] Lägg till domänregler/validering direkt i `WindTurbine` (t.ex. kasta exceptions vid ogiltiga dimensioner).
* [ ] Hantera felmeddelanden i GUI om `SimulationEngine` stöter på mekaniska misslyckanden (t.ex. `is_unsafe == True`).

### 4. Distribution & Testning

* [ ] Skriva tester för `SimulationEngine`
* [ ] Skriv checkar för använderinput
