import sys
import importlib.metadata
import traceback

def main():
    print(f"Python executável: {sys.executable}")
    print(f"Versão do Python: {sys.version}")
    print("-" * 50)
    
    # Check pydantic version
    try:
        pydantic_version = importlib.metadata.version('pydantic')
        print(f"pydantic (metadata): {pydantic_version}")
    except Exception as e:
        print(f"Erro ao obter versão do pydantic: {e}")
        
    # Check pydantic-core version
    try:
        pydantic_core_version = importlib.metadata.version('pydantic-core')
        print(f"pydantic-core (metadata): {pydantic_core_version}")
    except Exception as e:
        print(f"Erro ao obter versão do pydantic-core: {e}")

    print("-" * 50)
    
    # Test importing
    print("Testando importações...")
    try:
        import pydantic_core
        print(f"Import pydantic_core: OK (arquivo: {pydantic_core.__file__})")
        
        if hasattr(pydantic_core, '__version__'):
            print(f"pydantic_core.__version__: {pydantic_core.__version__}")
            
    except ImportError as e:
        print(f"Falha ao importar pydantic_core: {e}")
        
    try:
        import pydantic
        print(f"Import pydantic: OK (arquivo: {pydantic.__file__})")
        if hasattr(pydantic, '__version__'):
            print(f"pydantic.__version__: {pydantic.__version__}")
    except ImportError as e:
        print(f"Falha ao importar pydantic: {e}")

if __name__ == '__main__':
    main()
