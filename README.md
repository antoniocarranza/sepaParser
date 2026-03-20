# sepa

Script en Python para leer ficheros XML SEPA de transferencias y mostrarlos en un formato legible por terminal.

## Para qué sirve

Este repositorio sirve para inspeccionar ficheros SEPA de tipo `pain.001.001.03` sin tener que abrir el XML a mano.

El script:

- lee uno o varios ficheros XML SEPA;
- extrae los datos principales del mensaje, del ordenante y de cada bloque de pago;
- muestra cada transferencia con beneficiario, IBAN, importe, concepto, finalidad y `EndToEndId`;
- formatea los importes en euros de forma legible.

Es útil para revisar remesas o transferencias exportadas por un ERP, una asesoría o una banca electrónica antes de enviarlas o para auditar su contenido después.

## Contenido del repositorio

- `leer_sepa.py`: script principal.
- `*.xml`: ejemplos de ficheros SEPA para probar el script.

## Requisitos

- Python 3.9 o superior.

## Dependencias

Este proyecto no necesita dependencias externas ni instalar paquetes con `pip`.

Usa solo librerías estándar de Python:

- `argparse`
- `dataclasses`
- `decimal`
- `pathlib`
- `sys`
- `xml.etree.ElementTree`

## Instalación

1. Clona el repositorio:

```bash
git clone <URL_DEL_REPOSITORIO>
cd sepa
```

2. Comprueba que tienes Python 3 disponible:

```bash
python3 --version
```

3. No hace falta instalar nada más.

Opcionalmente, puedes dar permisos de ejecución al script si quieres lanzarlo directamente:

```bash
chmod +x leer_sepa.py
```

## Uso

### Procesar un fichero concreto

```bash
python3 leer_sepa.py A41071465002aebweb20260306134535.xml
```

### Procesar varios ficheros

```bash
python3 leer_sepa.py fichero1.xml fichero2.xml
```

### Procesar todos los XML de una carpeta

```bash
python3 leer_sepa.py .
```

### Procesar los XML de la carpeta actual

Si no pasas argumentos, el script busca automáticamente todos los `*.xml` del directorio actual:

```bash
python3 leer_sepa.py
```

## Qué información muestra

Para cada documento SEPA, el script imprime:

- nombre del fichero;
- identificador del mensaje;
- fecha de creación;
- ordenante inicial e identificador;
- número total de operaciones;
- importe total;
- datos de cada bloque de pago;
- datos de cada transferencia individual.

## Ejemplo de salida

```text
================================================================================
Fichero: A41071465002aebweb20260306134535.xml
Tipo: Transferencia SEPA (pain.001.001.03)
Mensaje: A4103336500220260306134535
Creado: 2026-03-06T13:45:35
Ordenante inicial: TROCICA (TRANSFERENCIA)
Identificador ordenante: A41033365002
Total operaciones: 1
Importe total: 732,27 EUR
```

## Notas

- El script está orientado a documentos SEPA con namespace `urn:iso:std:iso:20022:tech:xsd:pain.001.001.03`.
- Si un XML no es válido o no puede parsearse, el script muestra el error por stderr y continúa con el resto de ficheros.
