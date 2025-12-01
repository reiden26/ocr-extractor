import os
import json
from typing import Dict, Any, Optional

import requests


LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
LMSTUDIO_API_KEY = os.getenv("LMSTUDIO_API_KEY", "lmstudio-key")
LMSTUDIO_MODEL = os.getenv("LMSTUDIO_MODEL", "llama-3.2-3b-instruct")


class LocalAIAgentError(Exception):
    """Error genérico del agente de IA local."""


def _chat(messages, temperature: float = 0.2, max_tokens: int = 1024) -> str:
    """
    Llama al servidor local de LM Studio usando la API compatible con OpenAI.
    Espera que LM Studio esté corriendo en LMSTUDIO_BASE_URL.
    """
    url = f"{LMSTUDIO_BASE_URL}/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LMSTUDIO_API_KEY}",
    }

    payload = {
        "model": LMSTUDIO_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
    except Exception as e:
        raise LocalAIAgentError(f"No se pudo conectar al servidor LM Studio en {url}: {e}")

    if resp.status_code != 200:
        raise LocalAIAgentError(
            f"Respuesta no exitosa de LM Studio ({resp.status_code}): {resp.text[:500]}"
        )

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise LocalAIAgentError(f"Formato de respuesta inesperado de LM Studio: {e} - {data}")


def extraer_datos_con_ia(raw_text: str) -> Dict[str, Any]:
    """
    Extrae TODOS los datos de la factura directamente del texto OCR usando el modelo.
    Esta es la función principal que debe usarse para determinar los campos.
    """
    system_prompt = (
        "Eres un asistente experto en analizar facturas. "
        "Analiza el texto OCR completo de una factura y extrae TODOS los campos relevantes. "
        "Busca información en cualquier parte del texto, incluyendo campos como 'PERÍODO', 'FECHA', 'FECHA DE EMISIÓN', etc. "
        "Si encuentras 'PERÍODO: SEPTIEMBRE - 2025', mapea eso al campo 'date' como '2025-09' o '2025-09-01'. "
        "El campo 'invoice_number' debe ser el identificador de la factura (un número o código alfanumérico), "
        "NUNCA el nombre genérico del documento (por ejemplo, no uses 'CUPÓN PARA PAGO MES ANTERIOR' como número). "
        "Si solo encuentras un texto descriptivo, guárdalo en el campo opcional 'document_title' y deja 'invoice_number' en null. "
        "Además de los campos básicos, PUEDES añadir campos adicionales cuando veas información importante "
        "para entender la factura (por ejemplo: 'contract_number', 'billing_period', 'service_name', 'customer_name', 'address', etc.). "
        "Responde ÚNICAMENTE con un JSON válido, sin texto adicional."
    )

    user_prompt = (
        "Texto OCR completo de la factura:\n"
        "================================\n"
        f"{raw_text}\n\n"
        "Analiza este texto y extrae TODOS los campos de la factura. "
        "Busca en cualquier parte del documento: encabezados, pies de página, secciones intermedias, etc.\n\n"
        "Devuelve un JSON con al menos estos campos (puedes añadir más si lo consideras importante):\n"
        "{\n"
        '  "invoice_number": string | null,        // Número de factura, puede estar como "FACTURA N°", "NÚMERO", "NO.", etc.\n'
        '  "date": string | null,                  // Fecha de emisión. Si encuentras "PERÍODO: SEPTIEMBRE - 2025", úsalo como fecha. Formato preferido: YYYY-MM-DD o YYYY-MM\n'
        '  "supplier": string | null,              // Nombre de la empresa o entidad que EMITE la factura (ej. Gases del Caribe, Claro, banco, etc.)\n'
        '  "nit": string | null,                   // NIT, RUC, RFC, o identificación fiscal\n'
        '  "subtotal": number | null,              // Subtotal antes de impuestos\n'
        '  "tax": number | null,                   // IVA, impuestos, tax\n'
        '  "total": number | null,                 // Total a pagar\n'
        '  "currency": string | null,              // Moneda (COP, USD, EUR, etc.)\n'
        '  "payment_terms": string | null,         // Condiciones de pago si aparecen\n'
        '  "raw_text": string,                     // Incluye aquí el texto OCR completo\n'
        '  "document_title": string | null         // Título o descripción general del documento, si existe\n'
        "}\n\n"
        "SI VES otros datos claramente importantes (número de contrato, período de facturación, servicio, "
        "cliente/receptor de la factura, dirección, etc.), añade campos adicionales con nombres claros en inglés en snake_case "
        "(por ejemplo: \"contract_number\", \"billing_period\", \"service_name\").\n\n"
        "IMPORTANTE: Si ves 'PERÍODO: SEPTIEMBRE - 2025' o similar, mapea eso al campo 'date'. "
        "Si ves 'FECHA', 'FECHA DE EMISIÓN', 'FECHA DE FACTURACIÓN', etc., úsalo para 'date'. "
        "Responde solo con JSON puro, sin comentarios ni texto fuera del JSON."
    )

    content = _chat(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=1000,
    )

    # Intentar parsear como JSON robustamente
    content_stripped = content.strip()
    if not content_stripped.startswith("{"):
        start = content_stripped.find("{")
        end = content_stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            content_stripped = content_stripped[start : end + 1]

    try:
        data = json.loads(content_stripped)
    except json.JSONDecodeError as e:
        raise LocalAIAgentError(f"No se pudo parsear la respuesta como JSON: {e}\nRespuesta: {content}")

    # Asegurar que al menos devolvemos raw_text y no perdemos campos extra
    if "raw_text" not in data or not data.get("raw_text"):
        data["raw_text"] = raw_text

    return data


def refinar_datos_factura(raw_text: str, data_inicial: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envía el texto OCR completo y los datos iniciales al modelo para que devuelva
    un JSON bien estructurado con los campos de la factura refinados.
    """
    system_prompt = (
        "Eres un asistente experto en facturas. "
        "Recibirás el texto OCR completo de una factura y un JSON con una extracción inicial. "
        "Debes corregir, completar y normalizar los campos de la factura. "
        "Responde ÚNICAMENTE con un JSON válido, sin texto adicional."
    )

    user_prompt = (
        "Texto OCR de la factura:\n"
        "------------------------\n"
        f"{raw_text}\n\n"
        "Datos extraídos inicialmente (pueden contener errores o campos vacíos):\n"
        "---------------------------------------------------------------------\n"
        f"{json.dumps(data_inicial, ensure_ascii=False, indent=2)}\n\n"
        "Devuelve un JSON con la siguiente estructura (rellena lo que puedas, deja null si no sabes):\n"
        "{\n"
        '  \"invoice_number\": string | null,\n'
        '  \"date\": string | null,            // formato sugerido YYYY-MM-DD si es posible\n'
        '  \"supplier\": string | null,\n'
        '  \"nit\": string | null,\n'
        '  \"subtotal\": number | null,\n'
        '  \"tax\": number | null,\n'
        '  \"total\": number | null,\n'
        '  \"currency\": string | null,        // por ejemplo \"COP\", \"USD\", etc.\n'
        '  \"payment_terms\": string | null,   // condiciones de pago si aparecen\n'
        '  \"raw_text\": string                // incluye aquí el texto OCR completo\n'
        "}\n"
        "Recuerda: responde solo con JSON puro, sin comentarios ni texto fuera del JSON."
    )

    content = _chat(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=800,
    )

    # Intentar parsear como JSON robustamente
    content_stripped = content.strip()
    # Por si el modelo rodea el JSON con texto, buscar el primer '{' y el último '}'
    if not content_stripped.startswith("{"):
        start = content_stripped.find("{")
        end = content_stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            content_stripped = content_stripped[start : end + 1]

    try:
        data = json.loads(content_stripped)
    except json.JSONDecodeError as e:
        raise LocalAIAgentError(f"No se pudo parsear la respuesta como JSON: {e}\nRespuesta: {content}")

    # Asegurar que al menos devolvemos los campos esperados
    result: Dict[str, Optional[Any]] = {
        "invoice_number": data.get("invoice_number"),
        "date": data.get("date"),
        "supplier": data.get("supplier"),
        "nit": data.get("nit"),
        "subtotal": data.get("subtotal"),
        "tax": data.get("tax"),
        "total": data.get("total"),
        "currency": data.get("currency"),
        "payment_terms": data.get("payment_terms"),
        "raw_text": data.get("raw_text", raw_text),
    }

    return result


def responder_pregunta_sobre_factura(
    raw_text: str,
    data_estructurada: Dict[str, Any],
    pregunta: str,
) -> str:
    """
    Permite hacer preguntas en lenguaje natural sobre una factura concreta.
    Usa como contexto el texto OCR completo y los datos ya estructurados.
    """
    system_prompt = (
        "Eres un asistente que responde preguntas sobre facturas usando ÚNICAMENTE "
        "la información proporcionada (texto OCR y datos estructurados). "
        "Si no encuentras la respuesta en la factura, di claramente que no estás seguro. "
        "Responde siempre en español."
    )

    context = (
        "Datos estructurados de la factura:\n"
        f"{json.dumps(data_estructurada, ensure_ascii=False, indent=2)}\n\n"
        "Texto OCR completo:\n"
        f"{raw_text}\n"
    )

    user_prompt = (
        "Contexto de la factura:\n"
        "-----------------------\n"
        f"{context}\n\n"
        f"Pregunta del usuario: {pregunta}\n\n"
        "Responde de forma clara y breve."
    )

    answer = _chat(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=512,
    )

    return answer.strip()


