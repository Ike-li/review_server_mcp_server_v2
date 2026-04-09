"""服务层测试。"""

from tests.conftest import DT


def test_detect_leak_normal(service):
    score = service.detect_leak("10001", "review-10001-appstore-01", DT)
    assert score.level == "normal"


def test_detect_leak_leaked(service):
    score = service.detect_leak("10003", "review-10003-appstore-01", DT)
    assert score.level == "leaked"
    assert score.total > 60


def test_detect_leak_unknown_server(service):
    score = service.detect_leak("10001", "nonexistent-server", DT)
    assert score.level == "normal"
    assert "未找到" in score.summary


def test_classify_player_normal(service):
    result = service.classify_player("10001", "review-10001-appstore-01", "u1_001", DT)
    assert result["classification"] == "normal"


def test_classify_player_high_risk(service):
    # u3_001 在正式服存在且有付费 + 提审服也有付费 + 当日注册
    result = service.classify_player("10003", "review-10003-appstore-01", "u3_001", DT)
    assert result["classification"] == "high_risk"


def test_classify_player_not_found(service):
    result = service.classify_player("10001", "review-10001-appstore-01", "nobody", DT)
    assert result["classification"] == "unknown"


def test_generate_report(service):
    report = service.generate_report("10003", "review-10003-appstore-01", DT)
    assert "# 提审服泄漏检测报告" in report
    assert "末日狂飙" in report
    assert "维度明细" in report


def test_query_status(service):
    status = service.query_status("10001")
    assert status["game"]["name"] == "星际征途"
    assert status["server_count"] == 1


def test_query_detail(service):
    detail = service.query_detail("review-10003-appstore-01", DT, page=1, page_size=10)
    assert detail["total"] == 55
    assert len(detail["records"]) == 10
    assert detail["page"] == 1


def test_get_timeline(service):
    timeline = service.get_timeline("review-10003-appstore-01", "2026-03-01", "2026-03-07")
    assert len(timeline) == 7
    assert timeline[0]["leak_level"] == "normal"
    assert timeline[-1]["leak_level"] == "leaked"


def test_query_detail_page_out_of_range(service):
    detail = service.query_detail("review-10001-appstore-01", DT, page=999, page_size=10)
    assert detail["total"] == 5
    assert len(detail["records"]) == 0


def test_detect_leak_no_servers(service):
    score = service.detect_leak("99999", "nonexistent", DT)
    assert score.level == "normal"


def test_query_detail_negative_page_size(service):
    """page_size=-1 不应绕过分页限制。"""
    detail = service.query_detail("review-10003-appstore-01", DT, page=1, page_size=-1)
    assert detail["page_size"] == 1
    assert len(detail["records"]) == 1


def test_query_detail_negative_page(service):
    """page=0 或负数应被修正为 1。"""
    detail = service.query_detail("review-10003-appstore-01", DT, page=0, page_size=10)
    assert detail["page"] == 1
    assert len(detail["records"]) == 10


def test_query_detail_huge_page_size(service):
    """page_size 超过上限应被限制为 500。"""
    detail = service.query_detail("review-10003-appstore-01", DT, page=1, page_size=9999)
    assert detail["page_size"] == 500
