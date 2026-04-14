import subprocess
import os
import sys
import shutil
import hashlib
import struct
import argparse
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

ADB = "adb"
DEVICE = None

# -------------------------
# RUN
# -------------------------
def run(cmd, check=True):
    global DEVICE
    if DEVICE and cmd.startswith("adb"):
        cmd = cmd.replace("adb", f"adb -s {DEVICE}", 1)

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"[!] ERROR:{result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


# -------------------------
# DEVICE
# -------------------------
def get_devices():
    out = subprocess.run("adb devices", shell=True, capture_output=True, text=True).stdout
    lines = out.splitlines()[1:]

    return [l.split()[0] for l in lines if "device" in l]


def get_device_info(device):
    model = subprocess.run(
        f"adb -s {device} shell getprop ro.product.model",
        shell=True, capture_output=True, text=True
    ).stdout.strip()

    android = subprocess.run(
        f"adb -s {device} shell getprop ro.build.version.release",
        shell=True, capture_output=True, text=True
    ).stdout.strip()

    return model, android


def select_device():
    devices = get_devices()

    if not devices:
        print("[!] No hay dispositivos")
        sys.exit(1)

    if len(devices) == 1:
        m, a = get_device_info(devices[0])
        print(f"[+] {devices[0]} ({m} - Android {a})")
        return devices[0]

    print("\n[*] Dispositivos:")
    for i, d in enumerate(devices):
        m, a = get_device_info(d)
        print(f"[{i}] {d} ({m} - Android {a})")

    while True:
        c = input("Selecciona: ")
        if c.isdigit() and int(c) < len(devices):
            return devices[int(c)]

#---------------------------
# ENV DETECTION
#---------------------------
def is_genymotion():
    props = run("adb shell getprop", check=False).lower()
    return "genymotion" in props or "vbox" in props


def try_direct_system_install(cert_name):
    print(f"[*] Intentando instalación directa (Genymotion) - {cert_name}...")
    input("DtaEH")
    run("adb root", check=False)
    run("adb remount", check=False)
    run(f"adb push {cert_name} /system/etc/security/cacerts/{cert_name}")
    run(f"adb shell chmod 644 /system/etc/security/cacerts/{cert_name}")
    run(f"adb shell chown root:root /system/etc/security/cacerts/{cert_name}")
    return True

# -------------------------
# CERT
# -------------------------
def ensure_pem(path):
    data = open(path, "rb").read()
    try:
        x509.load_pem_x509_certificate(data, default_backend())
        return path
    except ValueError:
        cert = x509.load_der_x509_certificate(data, default_backend())
        pem = cert.public_bytes(serialization.Encoding.PEM)
        new = path + ".pem"
        open(new, "wb").write(pem)
        return new


def subject_hash_old(path):
    cert = x509.load_pem_x509_certificate(open(path, "rb").read(), default_backend())
    der = cert.subject.public_bytes()
    md5 = hashlib.md5(der).digest()
    return format(struct.unpack("<I", md5[:4])[0], "08x")


def get_cert_cn(cert):
    for attr in cert.subject:
        if attr.oid._name == "commonName":
            return attr.value
    return "Custom CA"


# -------------------------
# INSTALL
# -------------------------

def install_magisk(cert_name, module_id, cert_cn):
    print("[*] Usando método Magisk...")
    module_prop = f"""id={module_id}
name={cert_cn}
version=1.0
versionCode=1
author=auto
description=Custom CA
"""
    existing = run(f"adb shell su -c 'ls /data/adb/modules/'")
    if module_id in existing:
        print("[!] Certificado ya instalado")
        return

    with open("module.prop", "w", encoding="utf-8") as f:
        f.write(module_prop)
    run(f"adb push {cert_name} /sdcard/")
    run("adb push module.prop /sdcard/")

    shell = f'''su -c "mkdir -p /data/adb/modules/{module_id}/system/etc/security/cacerts"; su -c "mv /sdcard/{cert_name} /data/adb/modules/{module_id}/system/etc/security/cacerts/"; su -c "chmod 644 /data/adb/modules/{module_id}/system/etc/security/cacerts/{cert_name}"; su -c "chown root:root /data/adb/modules/{module_id}/system/etc/security/cacerts/{cert_name}"; su -c "touch /data/adb/modules/{module_id}/auto_mount"; su -c "mv /sdcard/module.prop /data/adb/modules/{module_id}/module.prop"; su -c "chmod 644 /data/adb/modules/{module_id}/module.prop"; su -c "chown root:root /data/adb/modules/{module_id}/module.prop";'''

    run(f'adb shell "{shell}"')



def install(cert_path):
    print("[*] Instalando...")

    cert_pem = ensure_pem(cert_path)
    cert = x509.load_pem_x509_certificate(open(cert_pem, "rb").read(), default_backend())

    hash_value = subject_hash_old(cert_pem)
    cert_name = f"{hash_value}.0"
    module_id = f"ca_{hash_value}"
    cert_cn = get_cert_cn(cert)
    shutil.copy(cert_pem, cert_name)

    if is_genymotion():
        try:
            try_direct_system_install(cert_name)
        except:
            install_magisk(cert_name, module_id, cert_cn)
    else:
        install_magisk(cert_name, module_id, cert_cn)
    

    print("Instalacion exitosa")
    print("[*] Reiniciando...")
    run("adb reboot")


# -------------------------
# REMOVE
# -------------------------
def remove(module_id):
    print(f"[*] Eliminando {module_id}...")

    shell = f"su -c 'rm -rf /data/adb/modules/{module_id}'"
    run(f'adb shell "{shell}"')

    print("[*] Reiniciando...")
    run("adb reboot")


# -------------------------
# STATUS
# -------------------------
def status():
    print("[*] Certificados instalados:")
    if(is_genymotion()):
        try:
            out = run("adb shell su -c 'ls /system/etc/security/cacerts/'")
            certs = out.split()
            if not certs:
                print("❌ Ninguno")
            else:
                print(out)
            return
        except:
            pass  
    else:
        out = run("adb shell su -c 'ls /data/adb/modules/'")
        
        certs = out.split()
        # modules = [m for m in out.split() if m.startswith("ca_")]

        if not certs:
            print("❌ Ninguno")
            return

        for m in certs:
            name = run(f'adb shell su -c "cat /data/adb/modules/{m}/module.prop | grep name="')
            print(f"✔ {m} → {name.replace('name=', '')}")


# -------------------------
# MAIN
# -------------------------
def main():
    global DEVICE
    DEVICE = select_device()

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    i = sub.add_parser("install")
    i.add_argument("cert")

    r = sub.add_parser("remove")
    r.add_argument("module")

    sub.add_parser("status")

    args = parser.parse_args()

    if args.cmd == "install":
        install(args.cert)
    elif args.cmd == "remove":
        remove(args.module)
    elif args.cmd == "status":
        status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
