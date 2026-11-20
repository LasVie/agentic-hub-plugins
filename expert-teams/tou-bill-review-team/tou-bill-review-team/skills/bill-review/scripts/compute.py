"""Candidate calculation and independent replay."""
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP, localcontext


def meter_report(case):
    return {
        "stage": "inspect",
        "inputs_sha256": case.hashes,
        "start": case.start.isoformat(timespec="minutes"),
        "end": case.end.isoformat(timespec="minutes"),
        "utc_offset": case.offset,
        "interval_minutes": case.interval_minutes,
        "count": len(case.readings),
        "energy_micro_kwh": sum(row[4] for row in case.readings),
    }


def candidate(case):
    buckets = {}
    for start, end, band in case.windows:
        for minute in range(start, end, case.interval_minutes):
            buckets[minute] = band
    totals = dict.fromkeys(case.rates, 0)
    intervals = []
    for when, _, _, _, quantity in case.readings:
        band = buckets[when.hour * 60 + when.minute]
        totals[band] += quantity
        intervals.append(band)
    rounding = ROUND_HALF_UP if case.rounding == "half_up" else ROUND_HALF_EVEN
    cents = {}
    with localcontext() as context:
        context.prec = 40
        for band, units in totals.items():
            amount = Decimal(units).scaleb(-6) * Decimal(case.rates[band])
            cents[band] = int(amount.quantize(Decimal("0.01"), rounding=rounding) * 100)
    return {"interval_bands": intervals, "energy_micro_kwh": totals, "amount_minor": cents}


def scaled_million(text):
    whole, _, fraction = text.partition(".")
    return int(whole) * 1_000_000 + int(fraction.ljust(6, "0"))


def independent_replay(case):
    # Derive bucket membership from the interval's full span, not the candidate's lookup map.
    # Rates and quantities use integer millionths, so no Decimal rounding is shared here.
    totals = dict.fromkeys(case.rates, 0)
    charges = dict.fromkeys(case.rates, 0)
    rates = {band: scaled_million(rate) for band, rate in case.rates.items()}
    bands = []
    for when, _, raw, unit, _ in case.readings:
        minute = when.hour * 60 + when.minute
        band = next(band for start, end, band in case.windows
                    if start <= minute and minute + case.interval_minutes <= end)
        quantity = scaled_million(raw)
        if unit == "Wh":
            quantity //= 1000
        bands.append(band)
        totals[band] += quantity
        charges[band] += quantity * rates[band]
    minor = {}
    divisor = 10 ** 10
    for band, charge in charges.items():
        cents, remainder = divmod(charge, divisor)
        round_up = remainder * 2 > divisor or (
            remainder * 2 == divisor and (case.rounding == "half_up" or cents % 2 == 1)
        )
        minor[band] = cents + int(round_up)
    return {"interval_bands": bands, "energy_micro_kwh": totals, "amount_minor": minor}
