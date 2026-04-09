"""数据层测试。"""

from tests.conftest import DT


def test_get_game(repo):
    game = repo.get_game("10001")
    assert game is not None
    assert game.name == "星际征途"


def test_get_game_not_found(repo):
    assert repo.get_game("99999") is None


def test_resolve_game(repo):
    games = repo.resolve_game("星际")
    assert len(games) == 1
    assert games[0].game_id == "10001"


def test_list_games(repo):
    games = repo.list_games()
    assert len(games) == 3


def test_get_review_servers(repo):
    servers = repo.get_review_servers("10001")
    assert len(servers) == 1
    assert servers[0].channel == "appstore"


def test_get_player_records_normal(repo):
    records = repo.get_player_records("review-10001-appstore-01", DT)
    assert len(records) == 5
    assert all(r.total_pay == 0 for r in records)


def test_get_player_records_leaked(repo):
    records = repo.get_player_records("review-10003-appstore-01", DT)
    assert len(records) == 55


def test_get_formal_crosscheck(repo):
    uids = [f"u2_{i:03d}" for i in range(1, 16)]
    result = repo.get_formal_crosscheck_uids("10002", uids)
    assert len(result) == 4


def test_get_account_creations(repo):
    records = repo.get_account_creations("review-10002-appstore-01", DT)
    # 场景 2 中前 5 个玩家是当日注册
    assert len(records) == 5


def test_get_daily_stats(repo):
    stats = repo.get_daily_stats("review-10003-appstore-01", "2026-03-01", "2026-03-07")
    assert len(stats) == 7
    assert stats[-1].leak_level == "leaked"


def test_get_formal_crosscheck_empty(repo):
    result = repo.get_formal_crosscheck_uids("10001", [])
    assert result == []


def test_get_player_records_page(repo):
    records, total = repo.get_player_records_page("review-10003-appstore-01", DT, offset=0, limit=10)
    assert total == 55
    assert len(records) == 10


def test_get_player_records_page_offset(repo):
    records, total = repo.get_player_records_page("review-10003-appstore-01", DT, offset=50, limit=10)
    assert total == 55
    assert len(records) == 5
