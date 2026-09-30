import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import httpx
from pydantic import ValidationError

from app import routes
from app.schemas import AuditRequest, AuditResponse, AuditSummary
from app.services import carbon, predictor
from app.services.audit import run_audit
from app.services.compare import compare_audits
from app.services.scraper import BlockedURLError, check_green_hosting, extract_assets, reject_private_hosts


class UrlNormalisation(unittest.TestCase):
    def test_bare_domain_gets_https(self):
        self.assertEqual(str(AuditRequest(url="  python.org ").url), "https://python.org/")

    def test_explicit_http_is_kept(self):
        self.assertEqual(str(AuditRequest(url="http://example.com").url), "http://example.com/")

    def test_rejects_other_schemes_and_empty(self):
        for bad in ("ftp://example.com", "", "javascript:alert(1)"):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                AuditRequest(url=bad)


class PrivateHostGuard(unittest.TestCase):
    def check(self, url):
        asyncio.run(reject_private_hosts(httpx.Request("GET", url)))

    def test_blocks_private_and_reserved(self):
        for url in ("http://127.0.0.1/", "http://localhost:8000/", "http://169.254.169.254/latest",
                    "http://10.0.0.1/", "http://192.168.1.1/", "http://[::1]/", "http://[::ffff:127.0.0.1]/"):
            with self.subTest(url=url), self.assertRaises(BlockedURLError):
                self.check(url)

    def test_allows_public_ip(self):
        self.check("http://8.8.8.8/")


class AssetExtraction(unittest.TestCase):
    def test_finds_each_asset_once_with_its_type(self):
        html = """
            <img src="/a.png" srcset="/a.png 1x, /a@2x.png 2x, "><img src="#"><img src="data:image/png;base64,x">
            <script src="app.js"></script><script>inline()</script>
            <link rel="stylesheet" href="/s.css"><link rel="preload" as="font" href="/f.woff2">
            <link rel="shortcut icon" href="/favicon.ico"><link rel="canonical" href="/">
            <style>@font-face { src: url('https://cdn.test/f.woff?v=1'); } body { background: url(https://cdn.test/bg.png) }</style>
        """
        self.assertEqual(extract_assets(html, "https://x.test/page/"), {
            "https://x.test/a.png": "image", "https://x.test/a@2x.png": "image", "https://x.test/page/app.js": "script",
            "https://x.test/s.css": "css", "https://x.test/f.woff2": "font", "https://x.test/favicon.ico": "image",
            "https://cdn.test/f.woff?v=1": "font",
        })


class Carbon(unittest.TestCase):
    def test_grades_and_ratings(self):
        self.assertEqual(carbon.get_grade_and_score(0.09), ("A+", 96))
        self.assertEqual(carbon.get_grade_and_score(0.857), ("D", 35))
        self.assertEqual(carbon.get_grade_and_score(5), ("F", 10))
        self.assertEqual([carbon.get_rating(s) for s in (96, 80, 65, 60, 10)],
                         ["Sustainable", "Sustainable", "Needs Work", "Needs Work", "High Impact"])

    def test_methodology_has_open_ended_top_grade(self):
        self.assertIsNone(carbon.methodology()["grades"][-1]["max_co2"])


class ModelParity(unittest.TestCase):
    def test_matches_scikit_learn_prediction(self):
        features = {
            "html_size_kb": 51.42, "total_assets": 15, "image_count": 3, "script_count": 8, "css_count": 4,
            "font_count": 0, "media_count": 0, "image_total_kb": 32.54, "script_total_kb": 148.97,
            "css_total_kb": 154.75, "font_total_kb": 0.0, "media_total_kb": 0.0, "image_avg_kb": 10.85,
            "script_avg_kb": 18.62, "css_avg_kb": 38.69, "font_avg_kb": 0, "max_single_asset_kb": 122.42,
            "max_image_kb": 15.4, "max_script_kb": 66.36, "red_asset_count": 1, "amber_asset_count": 2,
            "green_asset_count": 12, "image_pct_of_weight": 8.4, "script_pct_of_weight": 38.4,
        }
        self.assertAlmostEqual(predictor.predict_co2(features), 0.14212884825109273, places=6)

    def test_features_cover_the_model(self):
        assets = [{"asset_type": "image", "size_bytes": 2048, "status": "green"}]
        self.assertTrue(set(predictor.MODEL["features"]) <= set(predictor.build_features(1024, assets)))


class Pipeline(unittest.TestCase):
    def test_result_matches_response_schema(self):
        scraped = {"html_size": 50_000, "assets": [
            {"url": "https://x.test/a.js", "name": "a.js", "asset_type": "script", "size_bytes": 20_000},
            {"url": "https://x.test/a.png", "name": "a.png", "asset_type": "image", "size_bytes": 400_000},
        ]}
        green = {"green": True, "hosted_by": "Host"}
        with patch("app.services.audit.scrape_page", AsyncMock(return_value=scraped)),                 patch("app.services.audit.check_green_hosting", AsyncMock(return_value=green)):
            result = AuditResponse.model_validate(asyncio.run(run_audit("https://x.test/")))
        self.assertEqual(result.total_bytes, 470_000)
        self.assertEqual([a.status for a in result.assets], ["red", "green"])
        self.assertEqual([(c.name, c.percentage) for c in result.categories], [("Image", 85.1), ("Script", 4.3)])
        self.assertIn(result.ml_prediction.agreement, ("close", "divergent"))
        self.assertEqual([a.saving_co2_grams for a in result.assets], [carbon.calculate_co2_grams(280_000), 0.0])
        self.assertEqual((result.grade, result.potential.grade, result.potential.saving_pct), ("A", "A+", 59.6))
        self.assertTrue(result.green_hosting.green)


class GreenHosting(unittest.TestCase):
    def lookup(self, **mock):
        with patch("app.services.scraper.httpx.AsyncClient.get", AsyncMock(**mock)):
            return asyncio.run(check_green_hosting("https://www.example.com/page"))

    def test_reads_green_status(self):
        response = httpx.Response(200, json={"green": True, "hosted_by": "Cloudflare"},
                                  request=httpx.Request("GET", "https://x.test"))
        self.assertEqual(self.lookup(return_value=response), {"green": True, "hosted_by": "Cloudflare"})

    def test_failure_is_unknown_not_an_error(self):
        self.assertIsNone(self.lookup(side_effect=httpx.ConnectError("down")))


class AuditCache(unittest.TestCase):
    def test_reuses_result_until_refresh(self):
        routes._cache.clear()
        fake = AsyncMock(side_effect=lambda url: {"id": str(fake.await_count), "grade": "A", "total_co2": 0.1,
                                                  "request_count": 1})
        with patch("app.routes.run_audit", fake):
            first = asyncio.run(routes.audit(AuditRequest(url="python.org")))
            again = asyncio.run(routes.audit(AuditRequest(url="https://python.org/")))
            fresh = asyncio.run(routes.audit(AuditRequest(url="python.org", refresh=True)))
        self.assertEqual((first["id"], again["id"], fresh["id"], fake.await_count), ("1", "1", "2", 2))


def summary(when, co2, score, categories):
    return AuditSummary(id=str(when), url="https://x.test/", audited_at=when, grade="A", score=score,
                        total_co2=co2, annual_co2_kg=co2 * 120, total_bytes=int(co2 * 2_793_000), request_count=10,
                        categories=[{"name": n, "count": 1, "total_bytes": 1, "total_co2": c, "percentage": 0}
                                    for n, c in categories])


class Compare(unittest.TestCase):
    now = datetime.now(timezone.utc)

    def test_orders_by_date_and_scores_changes(self):
        older = summary(self.now - timedelta(days=1), 0.8366, 35, [("Image", 0.5), ("Script", 0.2)])
        newer = summary(self.now, 0.1421, 88, [("Script", 0.1), ("Css", 0.02)])
        result = compare_audits(newer, older)
        self.assertEqual(result["older"].id, older.id)
        self.assertEqual(result["verdict"], "better")
        self.assertEqual(result["summary"], "Audit B emits 83% less CO₂ per visit than Audit A.")
        rows = {r["key"]: r for r in result["metrics"]}
        self.assertEqual((rows["score"]["direction"], rows["score"]["verdict"]), ("up", "better"))
        self.assertEqual((rows["total_co2"]["change_pct"], rows["total_co2"]["verdict"]), (-83, "better"))
        self.assertEqual([c["label"] for c in result["categories"]], ["Image", "Script", "Css"])
        self.assertIsNone(result["categories"][2]["change_pct"])
        self.assertEqual(result["categories"][2]["verdict"], "worse")

    def test_identical_audits_are_the_same(self):
        a = summary(self.now, 0.5, 50, [])
        result = compare_audits(a, a)
        self.assertEqual(result["verdict"], "same")
        self.assertTrue(all(r["verdict"] == "same" for r in result["metrics"]))
