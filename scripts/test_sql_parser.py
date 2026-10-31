"""Offline regression tests for the SQL VALUES parser; no database access."""
import unittest
from import_licensed_definitions import values

class SQLParserTests(unittest.TestCase):
    def test_multiple_rows_and_nulls(self):
        self.assertEqual(list(values("(1,'ROGI',NULL),(2,'CASA','ok')")), [["1","ROGI",None],["2","CASA","ok"]])
    def test_mysql_escaped_quote_and_backslash(self):
        self.assertEqual(list(values(r"(1,'a\'b','c\\d')")), [["1","a'b",r"c\d"]])
    def test_commas_inside_strings(self):
        self.assertEqual(list(values("(1,'a,b'),(2,'c')")), [["1","a,b"],["2","c"]])

if __name__ == "__main__":
    unittest.main()
