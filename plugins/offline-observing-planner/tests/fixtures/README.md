# Independent numerical reference fixtures

These are small, selected numerical facts used only by offline regression tests. They are not runtime ephemerides and are not included in the plugin payload or ZIP. Tests never call a service. This selection is not a claim that every possible observer/time has been verified.

## Sources and retained evidence

- NASA/JPL Solar System Dynamics Group, [Horizons](https://ssd.jpl.nasa.gov/horizons/), retrieved 2026-10-30. [API definitions](https://ssd-api.jpl.nasa.gov/doc/horizons.html) and [coordinate/time definitions](https://ssd.jpl.nasa.gov/horizons/manual.html).
- U.S. Naval Observatory Astronomical Applications Department, [Complete Sun and Moon Data for One Day](https://aa.usno.navy.mil/data/RS_OneDay), retrieved 2026-10-30; [API documentation](https://aa.usno.navy.mil/data/api).

Each JSON fixture records the exact request parameters or URL, version returned by the API, and SHA-256 of the original response. The raw responses remain locally in the ignored `.research/astronomy-engine-reference-evidence-20261030/` evidence directory. Raw JPL explanatory reports, website text, the upstream issue's PDF, logos and images are deliberately excluded from deliverables. The maintained fixture is an independently selected set of numerical observations and our own metadata, not a copy of a third-party narrative document or data catalog.

JPL public accessibility alone is not asserted to be a license. Its [FAQ](https://ssd.jpl.nasa.gov/faq.html) and [copyright notice](https://www.jpl.nasa.gov/caltechjpl-privacy-policies-and-important-notices/) say reproduction of site documents may require permission. No blanket MIT/CC0/public-domain claim is made for JPL materials. No provider contact, branding or endorsement is involved. USNO explicitly documents returning JSON for use in applications; only six event times are retained here. No third-party astronomy data is distributed as runtime input.

JPL requests were serial, finite, cached, and identified by product/version plus the repository contact URL in User-Agent. Two rejected initial request/parsing attempts were corrected using documented JD lists and fractional-second output, not repeatedly retried unchanged. Python's local TLS trust store failed; system curl with TLS validation succeeded, without disabling verification. Actual API response says version **1.2**, while current documentation identifies **1.3**; the returned header/table format was inspected and parsed rather than assuming version equality.

## Frames, units and tolerances

Horizons uses Earth geodetic coordinates, east-positive longitude and altitude **kilometers**; the wrapper uses meters. Quantity 4 with `APPARENT=AIRLESS` is apparent topocentric target-center azimuth/elevation, including light-time, aberration, precession/nutation and JPL's deflection model. Azimuth increases clockwise from north; elevation is relative to the local zenith plane. The wrapper uses Astronomy Engine `Equator(ofdate=True, aberration=True)` followed by `Horizon(Refraction.Airless)`. UT in these post-1962 Horizons requests is UTC. No refracted/below-horizon values are compared to airless coordinates.

The test compares great-circle separation rather than raw azimuth alone, which becomes ill-conditioned close to zenith/nadir. There are **38 observations**: all seven supported bodies at Singapore at 2000-01-01, 2026-10-30 twice six hours apart, and 2100-12-30; Mercury/Mars at the issue-383 sample; and Sun/Moon at latitude +80 degrees at summer/winter times. Thirty-seven observations use a **1 arcminute** regression budget. The one far-future Moon case uses an explicit **2 arcminute** budget for the documented time-scale difference below. This is a finite test budget, not a universal accuracy guarantee.

On the captured references, the maximum separation excluding the far-future Moon was **0.313304 arcminute** (Venus, 2026-10-30T12:00Z). The far-future Moon difference was **1.395233 arcminutes**. These limits are not hidden by rounding the display.

USNO times have minute precision. Sea-level Sun/Moon rise/set uses upper-limb/standard-refraction conventions; civil twilight uses the solar center at -6 degrees. The six UTC events use a **60-second** budget (minute rounding plus model/convention differences); observed maximum discrepancy was **28.365 seconds**. No mountain horizon/weather prediction is implied. Nautical/astronomical twilight are functionally exercised elsewhere but are not independently validated by this particular USNO fixture.

## Known far-future time-scale difference

At 2100-12-30T12:00Z, Horizons quantity 30 returned TDB−UTC **69.183860 seconds**. Its manual documents holding the latest predicted TAI−UTC constant for distant future times. Astronomy Engine's default Espenak/Meeus model gives TT−UT approximately **204.998066 seconds**. This is a model/convention difference; future leap seconds and Earth rotation are not currently known.

A diagnostic using the public `Time(ut, tt)` constructor with the JPL offset reduces the lunar separation from 1.395233 to approximately **0.01553 arcminute**. The diagnostic is confined to the test: it does not modify the vendored engine, monkey-patch host dependencies, replace production UTC behavior, or claim TDB and TT are precisely identical (their millisecond periodic difference is negligible for this test). The regression explicitly checks the unmodified production result still has the known greater-than-one-arcminute discrepancy, and that the diagnostic substantially reduces it. Far-future predictions must carry the limitation in user-facing documentation; the year range is not silently reduced.

## Upstream issue 383

The [issue](https://github.com/cosinekitty/astronomy/issues/383) attachment says the sample was approximately 18:30 GMT on 2025-03-10, latitude 37.20, longitude -121.84. Observer elevation is unspecified; this test uses sea level. Independent JPL positions agree with the approved pinned Python engine to **0.03424 arcminute for Mercury** and **0.01436 arcminute for Mars** at those inputs. The large reported discrepancy was not reproduced. This does not prove every issue reporter's input, environment or unreported code path is correct, nor is it labeled an upstream fix.
