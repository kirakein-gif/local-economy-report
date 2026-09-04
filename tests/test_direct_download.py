import unittest
from datetime import date
from io import BytesIO
from unittest.mock import patch
from openpyxl import Workbook
from streamlit.testing.v1 import AppTest


class DirectDownloadTests(unittest.TestCase):
    def test_advisory_warning_preview_and_invalid_period(self):
        workbook = Workbook()
        workbook.remove(workbook.active)
        for name in ('공사', '용역', '물품', '검토반영'):
            sheet = workbook.create_sheet(name)
            sheet['A1'] = '2026년 상반기'
            sheet['A2'] = name
        output = BytesIO()
        workbook.save(output)
        upload = BytesIO(output.getvalue())
        upload.name = 'review.xlsx'
        base = {(kind, loc): (0, 0) for kind in ('공사', '용역', '물품') for loc in (1, 2, 3)}
        counts = {loc: (0, 0) for loc in (1, 2, 3)}
        result = (output.getvalue(), [{'계약일자': ''}], {'institution': '검증기관'}, (base, counts, counts))
        with patch('streamlit.file_uploader', return_value=upload), patch('app_mode2.reports.build_final_halfyear_report_bytes', return_value=result):
            at = AppTest.from_string('from app_mode2 import render_mode2\nrender_mode2()', default_timeout=30).run()
            self.assertFalse(at.exception)
            self.assertTrue(at.warning)
            self.assertEqual(len(at.checkbox), 0)
            self.assertFalse(at.get('download_button')[0].proto.disabled)
            self.assertFalse(any(button.label == '반기보고서 생성하기' for button in at.button))
            for name in ('공사', '용역', '물품', '검토반영'):
                at.radio(key='final_preview_sheet').set_value(name).run()
                self.assertEqual(at.dataframe[0].value.iloc[1, 0], name)
            at.number_input(key='final_report_year').set_value(2027).run()
            self.assertIn('2027년', at.dataframe[0].value.iloc[0, 0])
            at.date_input(key='final_period_start').set_value(date(2099, 1, 1)).run()
            self.assertTrue(at.get('download_button')[0].proto.disabled)
            at.button(key='final_restore').click().run()
            self.assertFalse(at.get('download_button')[0].proto.disabled)
            self.assertFalse(at.exception)
