# apps/core/hardware.py
import hashlib
import platform
import subprocess

SECRET = "VMRB66062515479*-+/"

class HardwareID:
    """Genera un ID único basado en el hardware de la máquina"""

    @staticmethod
    def get_cpu_id():
        system = platform.system().lower()
        identifier = None

        if system == "linux":
            identifier = open("/etc/machine-id").read().strip()

        elif system == "windows":
            identifier = subprocess.check_output(
                "wmic csproduct get uuid", shell=True
            ).decode(errors="ignore").split("\n")[1].strip()
        elif system == "darwin":  # macOS
            identifier = subprocess.check_output(
                "system_profiler SPHardwareDataType | grep 'Serial Number'", shell=True
            ).decode(errors="ignore").split(":")[-1].strip()

        if not identifier:
            raise RuntimeError("No se pudo obtener un identificador único para esta máquina.")

        # Generar hash uniforme
        return identifier

    @classmethod
    def generar_fingerprint(cls):
        """Genera fingerprint basado en CPU"""
        cpu_id = cls.get_cpu_id()
        fingerprint_str = f"{cpu_id}{SECRET}"
        license_hash = hashlib.sha256(fingerprint_str.encode()).hexdigest()
        return license_hash
