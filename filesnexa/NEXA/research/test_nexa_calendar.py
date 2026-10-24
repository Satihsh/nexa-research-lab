"""Tests for nexa_calendar on a constructed export (not real calendar data)."""
from __future__ import annotations

import pandas as pd
import pytest

import nexa_calendar as cal


def write_export(d, values_rows, prov_server="Pepperstone-Demo", prov_values=None,
                 export_srv="2026.09.27 18:36:14", export_gmt="2026.09.27 15:36:14"):
    (d / "NEXA_Cal_countries.csv").write_text(
        'id,name,code,currency,currency_symbol,url_name\n840,"United States",US,USD,"$",united-states\n')
    (d / "NEXA_Cal_events.csv").write_text(
        "id,type,sector,frequency,time_mode,country_id,unit,importance,multiplier,digits,event_code,name,source_url\n"
        '1,1,4,2,0,840,0,3,3,1,"nonfarm-payrolls","Nonfarm Payrolls","x"\n'
        '2,1,4,2,1,840,0,1,0,1,"holiday","Holiday","x"\n')
    header = "id,event_id,time_server,time_server_int,period,revision,actual,prev,revised_prev,forecast,impact_type\n"
    (d / "NEXA_Cal_values.csv").write_text(header + "".join(values_rows))
    n = len(values_rows) if prov_values is None else prov_values
    (d / "NEXA_Cal_provenance.txt").write_text(
        f"server={prov_server}\naccount_login=61603218\ncountries=1\nevents=2\nvalues={n}\n"
        f"export_time_trade_server={export_srv}\nexport_time_gmt={export_gmt}\n")


# Stamped as MT5 does: with the server offset AT EXPORT (+3 for a summer export), so the
# winter release (08:30 EST = 13:30 UTC) reads 16:30 and the summer one (12:30 UTC) 15:30.
NFP_WINTER = "10,1,2024.02.02 16:30:00,0,2024.01.01,0,353.000000,333.000000,,185.000000,0\n"
NFP_SUMMER = "11,1,2024.07.05 15:30:00,0,2024.06.01,0,206.000000,272.000000,218.000000,190.000000,0\n"
HOLIDAY = "12,2,2024.07.04 00:00:00,0,2024.07.04,0,,,,,0\n"


def test_load_join_and_utc_conversion(tmp_path):
    write_export(tmp_path, [NFP_WINTER, NFP_SUMMER, HOLIDAY])
    t, man = cal.load_export(str(tmp_path))
    nfp = t[t["event_code"].str.strip('"') == "nonfarm-payrolls"]
    assert nfp["time_utc"].dt.strftime("%H:%M").tolist() == ["13:30", "12:30"]   # 08:30 New York both
    assert set(man["sha256"]) == set(cal.FILES)


def test_missing_values_stay_missing_and_date_only_is_not_exact(tmp_path):
    write_export(tmp_path, [NFP_WINTER, HOLIDAY])
    t, _ = cal.load_export(str(tmp_path))
    hol = t[t["event_id"] == 2].iloc[0]
    assert pd.isna(hol["actual"]) and pd.isna(hol["forecast"])
    assert not hol["timestamp_exact"]
    assert t[t["event_id"] == 1].iloc[0]["timestamp_exact"]


def test_nfp_clock_check_constant_across_dst(tmp_path):
    write_export(tmp_path, [NFP_WINTER, NFP_SUMMER])
    t, man = cal.load_export(str(tmp_path))
    chk = cal.release_clock_check(t, "nonfarm-payrolls", "USD")
    assert chk["new_york_clock"] == {"08:30": 2}
    # bar-clock server time (NY+7) is 15:30 in both seasons once converted correctly
    assert chk["server_clock_by_us_dst"] == {"True": {"15:30": 1}, "False": {"15:30": 1}}
    assert man["calendar_time_basis"].startswith("FIXED_EXPORT_OFFSET 0 days 03:00")


def test_winter_export_offset_changes_the_stamp_not_the_instant(tmp_path):
    summer_in_winter_export = "11,1,2024.07.05 14:30:00,0,2024.06.01,0,206,272,218,190,0\n"
    write_export(tmp_path, [summer_in_winter_export], export_srv="2027.01.10 12:00:00", export_gmt="2027.01.10 10:00:00")
    t, _ = cal.load_export(str(tmp_path))
    assert t["time_utc"].dt.strftime("%H:%M").tolist() == ["12:30"]
    assert pd.to_datetime(t["time_utc"]).dt.tz_convert("America/New_York").dt.strftime("%H:%M").tolist() == ["08:30"]


def test_local_clock_flags_rows_off_the_events_mode(tmp_path):
    rows = [f"{100+i},1,2024.0{m}.05 {'15' if m in (4,5,6) else '16'}:30:00,0,2024.01.01,0,1,1,,1,0\n"
            for i, m in enumerate([1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6])]
    rows.append("200,1,2024.09.06 14:30:00,0,2024.08.01,0,1,1,,1,0\n")          # one hour early vs mode
    write_export(tmp_path, rows)
    t, _ = cal.load_export(str(tmp_path))
    assert int(t["local_clock_off_mode"].sum()) == 1
    assert t.loc[t["local_clock_off_mode"], "time_server_text"].tolist() == ["2024.09.06 14:30:00"]


@pytest.mark.parametrize("kind", ["server", "count", "dup", "orphan"])
def test_provenance_and_integrity_failures(tmp_path, kind):
    rows = [NFP_WINTER]
    if kind == "server":
        write_export(tmp_path, rows, prov_server="ICMarketsInternational-Demo")
    elif kind == "count":
        write_export(tmp_path, rows, prov_values=5)
    elif kind == "dup":
        write_export(tmp_path, [NFP_WINTER, NFP_WINTER])
    else:
        write_export(tmp_path, ["13,99,2024.02.02 15:30:00,0,2024.01.01,0,1,1,,1,0\n"])
    with pytest.raises(cal.CalendarError):
        cal.load_export(str(tmp_path))


def test_incomplete_export_rejected(tmp_path):
    write_export(tmp_path, [NFP_WINTER])
    (tmp_path / "NEXA_Cal_provenance.txt").unlink()
    with pytest.raises(cal.CalendarError):
        cal.load_export(str(tmp_path))


# ---------------------------------------------------------------- V2 provenance / causality

def _series(n=16, revise_at=None, anomaly_at=None):
    rows = []
    for i in range(n):
        y, m = 2020 + i // 12, i % 12 + 1
        hour = "15" if 4 <= m <= 10 else "16"                    # 08:30 New York under a summer export
        if anomaly_at == i:
            hour = "14"
        actual = 100 + i
        prev = 100 + i - 1
        rev = "" if revise_at != i else f"{actual + 50}"
        rows.append(f"{1000+i},1,{y}.{m:02d}.05 {hour}:30:00,0,{y}.{m:02d}.01,0,{actual},{prev},{rev},{actual - 1},0\n")
    return rows


def test_first_print_status(tmp_path):
    rows = _series(14)
    # make release 5 carry the value the NEXT release reports as revised
    parts = rows[5].split(",")
    parts[6] = "999"
    rows[5] = ",".join(parts)
    p6 = rows[6].split(",")
    p6[8] = "999"
    rows[6] = ",".join(p6)
    write_export(tmp_path, rows)
    t, _ = cal.load_export(str(tmp_path))
    fp = cal.first_print_status(t)
    t = t.assign(fp=fp).sort_values("time_utc")
    assert t["fp"].iloc[0] == "CONFIRMED"
    assert t["fp"].iloc[5] == "REVISED_VALUE"
    assert t["fp"].iloc[-1] == "UNDETERMINED"                     # latest release: no successor


def test_prior_only_baselines_are_causal(tmp_path):
    write_export(tmp_path, _series(16))
    t, _ = cal.load_export(str(tmp_path))
    a = cal.prior_only_baselines(t).sort_values("time_utc").reset_index(drop=True)
    rows = _series(16)
    last = rows[-1].split(",")
    last[6] = "5000"                                               # change ONLY the final release
    rows[-1] = ",".join(last)
    write_export(tmp_path, rows)
    t2, _ = cal.load_export(str(tmp_path))
    b = cal.prior_only_baselines(t2).sort_values("time_utc").reset_index(drop=True)
    cols = ["prior_n", "prior_modal_clock", "prior_surprise_sd", "local_clock_off_prior"]
    pd.testing.assert_frame_equal(a.loc[:14, cols], b.loc[:14, cols])   # the past never sees the change
    assert a.loc[0, "prior_n"] == 0 and a["prior_modal_clock"].iloc[:12].isna().all()


def test_prior_mode_flags_anomaly_without_future_information(tmp_path):
    write_export(tmp_path, _series(16, anomaly_at=14))
    t, _ = cal.load_export(str(tmp_path))
    b = cal.prior_only_baselines(t).sort_values("time_utc").reset_index(drop=True)
    assert bool(b.loc[14, "local_clock_off_prior"]) and not b.loc[:13, "local_clock_off_prior"].any()
    elig = cal.f1_eligible(b)
    assert not elig.loc[14]
