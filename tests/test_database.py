import tempfile, unittest
from pathlib import Path
import database as db

class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.original=db.DATABASE_NAME
        db.DATABASE_NAME=str(Path(self.tmp.name)/'test.sqlite'); db.initialize_database()
    def tearDown(self):
        db.DATABASE_NAME=self.original; self.tmp.cleanup()
    def test_crud_and_parameterized_text(self):
        pid=db.add_project("Demo'); DROP TABLE projects;--",'Demo manager','On Track',25)
        self.assertEqual(len(db.get_projects()),1)
        self.assertTrue(db.update_project(pid,'Demo','Demo manager','Completed',100))
        self.assertTrue(db.delete_project(pid));self.assertFalse(db.delete_project(pid))
    def test_invalid_records_are_rejected_before_persistence(self):
        for args in [('', 'Manager','On Track',10),('Demo',' ','On Track',10),('Demo','Manager','Unknown',10),('Demo','Manager','On Track',1.5),('Demo','Manager','On Track',True),('Demo','Manager','On Track',101)]:
            with self.subTest(args=args),self.assertRaises(ValueError):db.add_project(*args)
        self.assertEqual(db.get_projects(),[])
