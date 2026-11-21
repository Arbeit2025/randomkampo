"""ランダム漢方（randomkampo）のテスト。

外部通信は行わず、内蔵データと Flask テストクライアントで検証する。
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app as app_module  # noqa: E402

SAMPLE = {
    "name": "テスト湯",
    "reading": "てすととう",
    "herbs": "テスト生薬A、テスト生薬B",
    "effects": "これはテスト用の効果・効能です。",
    "constitution": "体力中等度の人",
    "source": "傷寒論",
}

SAMPLE_NO_SOURCE = {
    "name": "出典なし湯",
    "reading": "しゅってんなしとう",
    "herbs": "テスト生薬C",
    "effects": "出典を省略した処方のテストです。",
    "constitution": "体力虚弱な人",
    "source": None,
}


class RandomKampoTest(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()
        self._orig_fetch = app_module.fetch_random_kampo

    def tearDown(self):
        app_module.fetch_random_kampo = self._orig_fetch

    def test_healthz(self):
        res = self.client.get("/healthz")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["status"], "ok")

    def test_index_ok(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        body = res.get_data(as_text=True)
        self.assertIn("ランダム漢方", body)
        self.assertIn("ランダムで漢方薬を表示", body)
        self.assertIn("診断や治療の代わりにはなりません", body)
        self.assertIn("漢方薬にも副作用があり", body)
        self.assertIn("医師・薬剤師に相談してください", body)

    def test_random_success(self):
        app_module.fetch_random_kampo = lambda: dict(SAMPLE)
        res = self.client.get("/random")
        self.assertEqual(res.status_code, 200)
        body = res.get_data(as_text=True)
        self.assertIn("テスト湯", body)
        self.assertIn("てすととう", body)
        self.assertIn("テスト生薬A", body)
        self.assertIn("これはテスト用の効果・効能です。", body)
        self.assertIn("体力中等度の人", body)
        self.assertIn("傷寒論", body)

    def test_random_without_source_hides_source_label(self):
        app_module.fetch_random_kampo = lambda: dict(SAMPLE_NO_SOURCE)
        res = self.client.get("/random")
        self.assertEqual(res.status_code, 200)
        body = res.get_data(as_text=True)
        self.assertIn("出典なし湯", body)
        self.assertNotIn("出典</p>", body)

    def test_random_real_data_has_all_fields(self):
        res = self.client.get("/random")
        self.assertEqual(res.status_code, 200)
        body = res.get_data(as_text=True)
        self.assertIn("構成生薬", body)
        self.assertIn("効果・効能", body)
        self.assertIn("体質・証の目安", body)

    def test_dataset_size_and_uniqueness(self):
        formulas = app_module.FORMULAS
        self.assertEqual(len(formulas), 148)
        names = [f["name"] for f in formulas]
        self.assertEqual(len(names), len(set(names)))

    def test_dataset_fields_complete(self):
        for f in app_module.FORMULAS:
            for key in ("name", "reading", "herbs", "effects",
                        "constitution"):
                self.assertTrue(f[key], (f.get("name"), key))
            # 出典は任意項目：記載がある場合は空でない文字列であること
            if f["source"] is not None:
                self.assertTrue(f["source"].strip(), f["name"])

    def test_fetch_returns_copy_from_dataset(self):
        one = app_module.fetch_random_kampo()
        self.assertIn(one["name"], [f["name"] for f in app_module.FORMULAS])
        one["name"] = "書き換え"
        self.assertNotIn(
            "書き換え", [f["name"] for f in app_module.FORMULAS]
        )


if __name__ == "__main__":
    unittest.main()
