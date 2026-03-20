#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
import xml.etree.ElementTree as ET


NS = {"ns": "urn:iso:std:iso:20022:tech:xsd:pain.001.001.03"}


@dataclass
class Transfer:
    end_to_end_id: str = ""
    amount: str = ""
    currency: str = ""
    creditor_name: str = ""
    creditor_iban: str = ""
    creditor_bic: str = ""
    purpose: str = ""
    concept: str = ""


@dataclass
class PaymentInfo:
    payment_info_id: str = ""
    method: str = ""
    execution_date: str = ""
    batch_booking: str = ""
    charge_bearer: str = ""
    debtor_name: str = ""
    debtor_iban: str = ""
    debtor_bic: str = ""
    transfer_count: str = ""
    control_sum: str = ""
    transfers: list[Transfer] = field(default_factory=list)


@dataclass
class SepaDocument:
    file_name: str
    message_id: str = ""
    created_at: str = ""
    initiator_name: str = ""
    initiator_id: str = ""
    total_transactions: str = ""
    total_amount: str = ""
    payments: list[PaymentInfo] = field(default_factory=list)


def text_at(node: ET.Element | None, path: str) -> str:
    if node is None:
        return ""
    found = node.find(path, NS)
    if found is None or found.text is None:
        return ""
    return found.text.strip()


def format_amount(amount: str, currency: str) -> str:
    if not amount:
        return "-"
    try:
        value = Decimal(amount)
    except InvalidOperation:
        return f"{amount} {currency}".strip()
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} {currency}".strip()


def parse_transfer(node: ET.Element) -> Transfer:
    amount_node = node.find("ns:Amt/ns:InstdAmt", NS)
    return Transfer(
        end_to_end_id=text_at(node, "ns:PmtId/ns:EndToEndId"),
        amount=(amount_node.text or "").strip() if amount_node is not None and amount_node.text else "",
        currency=amount_node.attrib.get("Ccy", "") if amount_node is not None else "",
        creditor_name=text_at(node, "ns:Cdtr/ns:Nm"),
        creditor_iban=text_at(node, "ns:CdtrAcct/ns:Id/ns:IBAN"),
        creditor_bic=text_at(node, "ns:CdtrAgt/ns:FinInstnId/ns:BIC"),
        purpose=text_at(node, "ns:Purp/ns:Cd"),
        concept=text_at(node, "ns:RmtInf/ns:Ustrd"),
    )


def parse_payment_info(node: ET.Element) -> PaymentInfo:
    transfers = [parse_transfer(tx) for tx in node.findall("ns:CdtTrfTxInf", NS)]
    return PaymentInfo(
        payment_info_id=text_at(node, "ns:PmtInfId"),
        method=text_at(node, "ns:PmtMtd"),
        execution_date=text_at(node, "ns:ReqdExctnDt"),
        batch_booking=text_at(node, "ns:BtchBookg"),
        charge_bearer=text_at(node, "ns:ChrgBr"),
        debtor_name=text_at(node, "ns:Dbtr/ns:Nm"),
        debtor_iban=text_at(node, "ns:DbtrAcct/ns:Id/ns:IBAN"),
        debtor_bic=text_at(node, "ns:DbtrAgt/ns:FinInstnId/ns:BIC"),
        transfer_count=text_at(node, "ns:NbOfTxs"),
        control_sum=text_at(node, "ns:CtrlSum"),
        transfers=transfers,
    )


def parse_sepa_file(path: Path) -> SepaDocument:
    root = ET.parse(path).getroot()
    customer = root.find("ns:CstmrCdtTrfInitn", NS)
    group_header = customer.find("ns:GrpHdr", NS) if customer is not None else None
    payments = customer.findall("ns:PmtInf", NS) if customer is not None else []

    return SepaDocument(
        file_name=path.name,
        message_id=text_at(group_header, "ns:MsgId"),
        created_at=text_at(group_header, "ns:CreDtTm"),
        initiator_name=text_at(group_header, "ns:InitgPty/ns:Nm"),
        initiator_id=text_at(group_header, "ns:InitgPty/ns:Id/ns:OrgId/ns:Othr/ns:Id"),
        total_transactions=text_at(group_header, "ns:NbOfTxs"),
        total_amount=text_at(group_header, "ns:CtrlSum"),
        payments=[parse_payment_info(payment) for payment in payments],
    )


def render_document(document: SepaDocument) -> str:
    lines: list[str] = []
    lines.append("=" * 80)
    lines.append(f"Fichero: {document.file_name}")
    lines.append("Tipo: Transferencia SEPA (pain.001.001.03)")
    lines.append(f"Mensaje: {document.message_id or '-'}")
    lines.append(f"Creado: {document.created_at or '-'}")
    lines.append(f"Ordenante inicial: {document.initiator_name or '-'}")
    lines.append(f"Identificador ordenante: {document.initiator_id or '-'}")
    lines.append(f"Total operaciones: {document.total_transactions or '-'}")
    lines.append(f"Importe total: {format_amount(document.total_amount, 'EUR')}")

    for payment_index, payment in enumerate(document.payments, start=1):
        lines.append("-" * 80)
        lines.append(f"Bloque de pago {payment_index}")
        lines.append(f"Referencia: {payment.payment_info_id or '-'}")
        lines.append(f"Metodo: {payment.method or '-'}")
        lines.append(f"Fecha de ejecucion: {payment.execution_date or '-'}")
        lines.append(
            "Abono agrupado: "
            + ("si" if payment.batch_booking.lower() == "true" else "no" if payment.batch_booking else "-")
        )
        lines.append(f"Gastos: {payment.charge_bearer or '-'}")
        lines.append(f"Cuenta cargo: {payment.debtor_name or '-'}")
        lines.append(f"IBAN cargo: {payment.debtor_iban or '-'}")
        lines.append(f"BIC cargo: {payment.debtor_bic or '-'}")
        lines.append(f"Numero de transferencias: {payment.transfer_count or '-'}")
        lines.append(f"Suma del bloque: {format_amount(payment.control_sum, 'EUR')}")

        for transfer_index, transfer in enumerate(payment.transfers, start=1):
            lines.append(f"  Transferencia {transfer_index}")
            lines.append(f"    Beneficiario: {transfer.creditor_name or '-'}")
            lines.append(f"    IBAN beneficiario: {transfer.creditor_iban or '-'}")
            lines.append(f"    BIC beneficiario: {transfer.creditor_bic or '-'}")
            lines.append(f"    Importe: {format_amount(transfer.amount, transfer.currency)}")
            lines.append(f"    Concepto: {transfer.concept or '-'}")
            lines.append(f"    Finalidad: {transfer.purpose or '-'}")
            lines.append(f"    EndToEndId: {transfer.end_to_end_id or '-'}")
    return "\n".join(lines)


def find_xml_files(paths: list[str]) -> list[Path]:
    if not paths:
        return sorted(Path.cwd().glob("*.xml"))

    found: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            found.extend(sorted(path.glob("*.xml")))
        elif path.is_file():
            found.append(path)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extrae informacion de documentos SEPA XML y la presenta de forma legible."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Ficheros o carpetas a procesar. Si se omite, se usan los XML de la carpeta actual.",
    )
    args = parser.parse_args()

    files = find_xml_files(args.paths)
    if not files:
        print("No se han encontrado ficheros XML para procesar.", file=sys.stderr)
        return 1

    exit_code = 0
    for index, file_path in enumerate(files):
        try:
            document = parse_sepa_file(file_path)
            if index:
                print()
            print(render_document(document))
        except ET.ParseError as exc:
            exit_code = 1
            print(f"Error al parsear {file_path}: {exc}", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
