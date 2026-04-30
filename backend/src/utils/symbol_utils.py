"""
Symbol Normalization Utility

Provides consistent symbol normalization across the entire system.
Ensures all symbols used internally have .m suffix for MT5 compatibility.
"""

def normalize_symbol(symbol: str) -> str:
    """
    Ensure symbol has .m suffix for MT5.
    
    Args:
        symbol: Trading symbol (e.g., 'EURUSD' or 'EURUSD.m')
    
    Returns:
        str: Symbol with .m suffix (e.g., 'EURUSD.m')
    """
    if not symbol:
        return symbol
    
    symbol = symbol.upper()
    
    if not symbol.endswith('.m'):
        return symbol + '.m'
    return symbol


def denormalize_symbol(symbol: str) -> str:
    """
    Remove .m suffix for external API calls.
    
    Args:
        symbol: Internal symbol with .m suffix (e.g., 'EURUSD.m')
    
    Returns:
        str: Symbol without .m suffix (e.g., 'EURUSD')
    """
    if not symbol:
        return symbol
    
    if symbol.endswith('.m'):
        return symbol[:-2]
    return symbol


def is_normalized(symbol: str) -> bool:
    """
    Check if symbol is normalized (has .m suffix).
    
    Args:
        symbol: Trading symbol
    
    Returns:
        bool: True if symbol has .m suffix
    """
    return symbol.endswith('.m') if symbol else False