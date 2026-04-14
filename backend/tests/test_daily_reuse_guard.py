from pathlib import Path


def test_daily_reuse_guard_is_scoped_to_daily_flow():
    source = (Path(__file__).resolve().parents[1] / 'main.py').read_text(encoding='utf-8')
    assert 'if flow_type == "daily_horoscope":' in source
    assert '# Daily consistency (account + anonymous): return same-day result if it exists.' in source
