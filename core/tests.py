from django.test import TestCase
from core.utils import calculate_prerequisite_match

class PrerequisiteMatchingTests(TestCase):
    def test_wb_p01_mixed_bullet_types(self):
        matches, total = calculate_prerequisite_match("Python, SQL", "- Python\n* SQL")
        self.assertEqual(matches, 2)
        self.assertEqual(total, 2)

    def test_wb_p02_semantic_gap(self):
        # Without NLP, REACTJS and React.js are different strings.
        matches, total = calculate_prerequisite_match("REACTJS", "React.js")
        self.assertEqual(matches, 0)

    def test_wb_p03_empty_prereqs(self):
        matches, total = calculate_prerequisite_match("java", "")
        self.assertEqual(matches, 0)
        self.assertEqual(total, 0)

    def test_wb_p04_empty_skills(self):
        matches, total = calculate_prerequisite_match("", "Java")
        self.assertEqual(matches, 0)
        self.assertEqual(total, 1)

    def test_wb_p05_special_char_parsing(self):
        matches, total = calculate_prerequisite_match("C#, .NET", "C#, ASP.NET")
        self.assertEqual(matches, 1)
        self.assertEqual(total, 2)
