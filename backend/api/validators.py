"""
api/validators.py — Validação centralizada de dados de entrada
Implementa regras de validação para melhorar segurança e consistência
"""
import logging
import re
from typing import Any, Tuple

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exceção para erros de validação."""
    pass


def validate_string(
    value: Any,
    field_name: str,
    min_length: int = 1,
    max_length: int = 500,
    pattern: str = None,
    required: bool = True
) -> str:
    """
    Valida uma string.
    
    Args:
        value: Valor a validar
        field_name: Nome do campo (para mensagens de erro)
        min_length: Comprimento mínimo
        max_length: Comprimento máximo
        pattern: Regex pattern para validação adicional
        required: Se é obrigatório
        
    Returns:
        String validada e trimada
        
    Raises:
        ValidationError: Se inválido
    """
    if value is None or value == "":
        if required:
            raise ValidationError(f"{field_name} é obrigatório")
        return None
    
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} deve ser texto")
    
    value = value.strip()
    
    if len(value) < min_length:
        raise ValidationError(
            f"{field_name} deve ter pelo menos {min_length} caractere(s)"
        )
    
    if len(value) > max_length:
        raise ValidationError(
            f"{field_name} não pode ultrapassar {max_length} caracteres"
        )
    
    if pattern and not re.match(pattern, value):
        raise ValidationError(f"{field_name} possui formato inválido")
    
    return value


def validate_integer(
    value: Any,
    field_name: str,
    min_value: int = None,
    max_value: int = None,
    required: bool = True
) -> int:
    """Valida um inteiro."""
    if value is None or value == "":
        if required:
            raise ValidationError(f"{field_name} é obrigatório")
        return None
    
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} deve ser um número inteiro")
    
    if min_value is not None and int_value < min_value:
        raise ValidationError(
            f"{field_name} não pode ser menor que {min_value}"
        )
    
    if max_value is not None and int_value > max_value:
        raise ValidationError(
            f"{field_name} não pode ser maior que {max_value}"
        )
    
    return int_value


def validate_email(value: str) -> str:
    """Valida um email."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return validate_string(
        value,
        "Email",
        min_length=5,
        max_length=255,
        pattern=pattern
    )


def validate_id(value: str) -> str:
    """Valida um ID (UUID ou similar)."""
    return validate_string(
        value,
        "ID",
        min_length=1,
        max_length=100,
        required=True
    )


def validate_isbn(value: str) -> str:
    """Valida um ISBN."""
    value = validate_string(
        value,
        "ISBN",
        min_length=10,
        max_length=13,
        required=False
    )
    if value:
        # Remove hífens e espaços
        value = value.replace("-", "").replace(" ", "")
        if not value.isdigit():
            raise ValidationError("ISBN deve conter apenas dígitos")
    return value


def validate_book(book_data: dict) -> Tuple[bool, str]:
    """
    Valida um livro completo.
    
    Returns:
        (is_valid, error_message)
    """
    try:
        validate_string(book_data.get("titulo"), "Título", max_length=200)
        validate_string(book_data.get("autor"), "Autor", max_length=200)
        
        if "exemplares" in book_data:
            validate_integer(
                book_data.get("exemplares"),
                "Exemplares",
                min_value=1,
                max_value=999,
                required=False
            )
        
        if "isbn" in book_data and book_data.get("isbn"):
            validate_isbn(book_data.get("isbn"))
        
        return True, ""
    except ValidationError as e:
        return False, str(e)


def validate_student(student_data: dict) -> Tuple[bool, str]:
    """Valida um aluno."""
    try:
        validate_string(student_data.get("nome"), "Nome", max_length=200)
        validate_string(student_data.get("turma"), "Turma", max_length=50)
        
        if "carteirinha" in student_data and student_data.get("carteirinha"):
            validate_string(
                student_data.get("carteirinha"),
                "Carteirinha",
                max_length=50
            )
        
        return True, ""
    except ValidationError as e:
        return False, str(e)
