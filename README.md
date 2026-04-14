<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<h1>ADBCertInjector</h1>
<p>Herramienta en Python para instalar certificados CA como certificados del sistema en dispositivos Android físicos y emuladores. Compatible con múltiples dispositivos ADB, con soporte especial para Genymotion.</p>

</section>

<section>
<h2>🚀 Características</h2>
<ul>
<li>Instala certificados CA como certificados del sistema</li>
<li>Soporta archivos PEM / CRT / DER</li>
<li>Convierte automáticamente DER → PEM</li>
<li>Selección de múltiples dispositivos conectados por ADB</li>
<li>Soporte para teléfonos físicos con root + Magisks</li>
</ul>
</section>

<section>
<h2>📦 Requisitos</h2>

<h3>Sistema</h3>
<ul>
<li>Python 3.8+</li>
<li>ADB en PATH</li>
<li>Dispositivo Android root + Magisk o Genymotion</li>
</ul>

<h3>Librerias de Python</h3>
<pre>pip install cryptography</pre>
</section>

<section>
<h2>⚙️ Uso</h2>

<h3>Instalar certificado</h3>
<pre>//Archivo .crt
python adbCertInjector.py install certificate.crt</pre>
<pre>//Archivo .pem
python adbCertInjector.py install certificate.pem</pre>
<pre>//Archivo .der
python adbCertInjector.py install certificate.der</pre>

<h3>Validar Certificados Instalados</h3>
<pre>python adbCertInjector.py status</pre>

<h3>Eliminar certificado</h3>
<pre>python adbCertInjector.py remove ca_9a5ba575</pre>
</section>

<section>
<h2>🛠️ Ejemplo</h2>

<pre>
python adbCertInjector.py install burp.crt
</pre>

<pre>
[*] Devices:
[0] SM-A305G (Android 11)
[1] Genymotion (Android 10)

Select: 1
[*] Installing...
[*] Direct system install...
[+] Success
</pre>
</section>

<div class="footer">
<p>Created for SilReon</p>
</div>

</body>
</html>
