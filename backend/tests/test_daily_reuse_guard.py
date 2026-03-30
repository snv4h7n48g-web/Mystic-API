def test_daily_reuse_guard_is_scoped_to_daily_flow():
    source = open('/home/vmbot2/.openclaw/workspace/Mystic-API/backend/main.py', 'r', encoding='utf-8').read()
    assert 'if flow_type == "daily_horoscope":' in source
    assert '# Daily consistency (account + anonymous): return same-day result if it exists.' in source
