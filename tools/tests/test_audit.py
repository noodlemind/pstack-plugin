from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_repository import audit, inspect_file


class PublicationAuditTests(unittest.TestCase):
    def test_rejects_secret_without_echoing_it(self):
        token = b'sk-' + b'z' * 40
        result = inspect_file('README.md',b'credential ' + token)
        self.assertIn('provider-token',result)
        self.assertNotIn(token.decode(),str(result))

    def test_rejects_private_paths_and_runtime_artifacts(self):
        private_path = b'/' + b'Users/' + b'private-person/project'
        self.assertIn('personal-home-path',inspect_file('README.md',private_path))
        self.assertIn('private-or-generated-artifact',inspect_file('evidence/result.json',b'{}'))
        self.assertIn('personal-runtime-configuration',inspect_file('.codex/config.toml',b''))

    def test_allows_original_credit_public_links_and_synthetic_contacts(self):
        body = b'Lauren Tan (poteto), Copyright Cursor; https://github.com/poteto; git@github.com:example/project; test@example.com; /Users/you/project'
        self.assertEqual(inspect_file('NOTICE.md',body),[])

    def test_rejects_personal_contact_and_symlink(self):
        contact = b'person' + b'@' + b'private-mail.test'
        self.assertIn('non-example-email',inspect_file('README.md',contact))
        self.assertIn('non-regular-index-entry',inspect_file('fixture',b'../private','120000'))

    def test_audits_staged_content_even_when_worktree_was_cleaned(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            subprocess.run(['git','init','-q',str(root)],check=True)
            file = root/'fixture.txt'
            file.write_bytes(b'sk-' + b'z' * 40)
            subprocess.run(['git','add','fixture.txt'],cwd=root,check=True)
            file.write_text('safe worktree, unsafe index')
            report = audit(root)
            self.assertEqual(report['files_checked'],1)
            self.assertIn('provider-token',report['findings'][0]['rules'])


if __name__ == '__main__':
    unittest.main()
