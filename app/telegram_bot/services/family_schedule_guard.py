"""Family schedule guard.

Checks whether a proposed calendar event overlaps with protected family
time windows so the handler can ask for explicit confirmation before
creating the event.

Protected windows per weekday (0 = Monday, 6 = Sunday):
  - Mon-Fri: school-morning logistics + per-day pickups + evening routine + night transition
  - Sat-Sun:                                                 evening routine + night transition
"""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

_TZ = ZoneInfo("Europe/Madrid")

# (window_start, window_end, human-readable reason)
_FAMILY_WINDOWS: dict[int, list[tuple[time, time, str]]] = {
    0: [  # Monday
        (
            time(7, 30), time(9, 15),
            "franja de mañana para preparar y llevar a los niños; entran a las 9:00",
        ),
        (
            time(16, 45), time(18, 0),
            "recogida del lunes: pequeño a las 17:00 y mayor a las 17:30",
        ),
        (
            time(19, 0), time(20, 30),
            "rutina familiar de baños, cena y dormir",
        ),
        (
            time(20, 30), time(21, 0),
            "transición posterior a dormir a los niños",
        ),
    ],
    1: [  # Tuesday
        (
            time(7, 30), time(9, 15),
            "franja de mañana para preparar y llevar a los niños; entran a las 9:00",
        ),
        (
            time(16, 45), time(18, 0),
            "recogida del martes: pequeño a las 17:00 y mayor a las 17:30",
        ),
        (
            time(19, 0), time(20, 30),
            "rutina familiar de baños, cena y dormir",
        ),
        (
            time(20, 30), time(21, 0),
            "transición posterior a dormir a los niños",
        ),
    ],
    2: [  # Wednesday
        (
            time(7, 30), time(9, 15),
            "franja de mañana para preparar y llevar a los niños; entran a las 9:00",
        ),
        (
            time(16, 15), time(17, 30),
            "recogida del miércoles: mayor a las 16:30 y pequeño a las 17:00",
        ),
        (
            time(19, 0), time(20, 30),
            "rutina familiar de baños, cena y dormir",
        ),
        (
            time(20, 30), time(21, 0),
            "transición posterior a dormir a los niños",
        ),
    ],
    3: [  # Thursday
        (
            time(7, 30), time(9, 15),
            "franja de mañana para preparar y llevar a los niños; entran a las 9:00",
        ),
        (
            time(16, 45), time(18, 0),
            "recogida del jueves: pequeño a las 17:00 y mayor a las 17:30",
        ),
        (
            time(19, 0), time(20, 30),
            "rutina familiar de baños, cena y dormir",
        ),
        (
            time(20, 30), time(21, 0),
            "transición posterior a dormir a los niños",
        ),
    ],
    4: [  # Friday
        (
            time(7, 30), time(9, 15),
            "franja de mañana para preparar y llevar a los niños; entran a las 9:00",
        ),
        (
            time(16, 15), time(17, 30),
            "recogida del viernes: mayor a las 16:30 y pequeño a las 17:00",
        ),
        (
            time(19, 0), time(20, 30),
            "rutina familiar de baños, cena y dormir",
        ),
        (
            time(20, 30), time(21, 0),
            "transición posterior a dormir a los niños",
        ),
    ],
    5: [  # Saturday — no school / pickup windows
        (
            time(19, 0), time(20, 30),
            "rutina familiar de baños, cena y dormir",
        ),
        (
            time(20, 30), time(21, 0),
            "transición posterior a dormir a los niños",
        ),
    ],
    6: [  # Sunday — no school / pickup windows
        (
            time(19, 0), time(20, 30),
            "rutina familiar de baños, cena y dormir",
        ),
        (
            time(20, 30), time(21, 0),
            "transición posterior a dormir a los niños",
        ),
    ],
}


def check_family_conflicts(
    event_dt: datetime,
    duration_minutes: int = 60,
) -> list[str]:
    """Return reasons for each protected window that the event overlaps.

    The event is modelled as the half-open interval
    [event_dt, event_dt + duration_minutes).
    An empty list means no conflict.
    """
    local_dt = event_dt.astimezone(_TZ)
    weekday = local_dt.weekday()  # 0 = Monday, 6 = Sunday

    base_date: date = local_dt.date()
    event_start: datetime = local_dt
    event_end: datetime = local_dt + timedelta(minutes=duration_minutes)

    conflicts: list[str] = []
    for win_start_t, win_end_t, reason in _FAMILY_WINDOWS.get(weekday, []):
        win_start = datetime.combine(base_date, win_start_t, tzinfo=_TZ)
        win_end = datetime.combine(base_date, win_end_t, tzinfo=_TZ)
        # Overlap: event starts before window ends AND event ends after window starts
        if event_start < win_end and event_end > win_start:
            conflicts.append(reason)

    return conflicts
