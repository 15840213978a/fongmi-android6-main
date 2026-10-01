import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "verify_upgrade_apks", Path(__file__).resolve().parents[1] / "verify_upgrade_apks.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class CertificateOutputTest(unittest.TestCase):
    # Certificate from the actual previously released b6 APK.
    digest = "09df46ffbdad86403024aa2f822a4b92936cb1b5931c0fb3804b65e8f1bc4d0c"

    def test_build_tools_37_output(self):
        text = f"Verifies\nNumber of signers: 1\nV2 Signer: certificate SHA-256 digest: {self.digest}\n"
        self.assertEqual(verifier.certificate_digest(text), self.digest)

    def test_older_build_tools_output(self):
        text = f"Number of signers: 1\nSigner #1 certificate SHA-256 digest: {self.digest}\n"
        self.assertEqual(verifier.certificate_digest(text), self.digest)

    def test_same_certificate_across_schemes(self):
        text = f"Number of signers: 1\nV2 Signer: certificate SHA-256 digest: {self.digest}\nV3 Signer: certificate SHA-256 digest: {self.digest}\n"
        self.assertEqual(verifier.certificate_digest(text), self.digest)

    def test_rejects_different_certificates(self):
        text = f"Number of signers: 1\nV2 Signer: certificate SHA-256 digest: {self.digest}\nV3 Signer: certificate SHA-256 digest: {'f' * 64}\n"
        with self.assertRaises(RuntimeError):
            verifier.certificate_digest(text)

    def test_rejects_multiple_signers(self):
        with self.assertRaises(RuntimeError):
            verifier.certificate_digest(f"Number of signers: 2\nV2 Signer: certificate SHA-256 digest: {self.digest}\n")

    def test_source_stamp_does_not_replace_apk_signer(self):
        with self.assertRaises(RuntimeError):
            verifier.certificate_digest(f"Number of signers: 1\nSource Stamp Signer: certificate SHA-256 digest: {self.digest}\n")


class ManifestOutputTest(unittest.TestCase):
    def test_build_tools_37_minimum_is_not_target(self):
        self.assertEqual(verifier.minimum_sdk("minSdkVersion:'23'\ntargetSdkVersion:'37'\n"), 23)

    def test_older_build_tools_output(self):
        self.assertEqual(verifier.minimum_sdk("sdkVersion:'24'\ntargetSdkVersion:'37'\n"), 24)

    def test_rejects_missing_minimum_sdk(self):
        with self.assertRaises(RuntimeError):
            verifier.minimum_sdk("targetSdkVersion:'24'\n")


if __name__ == "__main__":
    unittest.main()
